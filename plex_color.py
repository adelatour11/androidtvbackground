# Plex background generator using a colored background and vignetting effect
# === Standard Library Imports ===
import os
import time
from datetime import datetime
import math
import random
import shutil
import textwrap
import unicodedata
from io import BytesIO

# === Third-Party Imports ===
import re
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from plexapi.server import PlexServer
from dotenv import load_dotenv
load_dotenv(verbose=True)

# === User Configurable Options ===

# NOTE: It's recommended to load these from environment variables

# OPTION 1: Hardcode baseurl and token (not recommended in production)
# UNCOMMENT the following lines if you want to hardcode values:
#baseurl = ''  # Your Plex server base URL, example: baseurl='http://192.168.1.100:32400'
#token = ''    # Your Plex API token, example: token='f6a5e7a6d9f6a8d6f7a5e8d5'

# OPTION 2: Use environment variables (recommended)
# Open your .env file in your text editor and set the environment variables:
# Example: BASEURL='http://192.168.1.100:32400'
# Example: TOKEN='f6a5e7a6d9f6a8d6f7a5e8d5'

# Script options
order_by = 'mix'            # 'aired', 'added', or 'mix' (mix will round up limit to a multiple of 3)
download_movies = True      # Allow background generation for Plex movies
download_series = True      # Allow background generation for Plex TV series
limit = 10                  # Max backgrounds per content type (TV/movies), so total can be up to limit × enabled types
debug = False               # Enable debug message printing

# Plex logo settings
logo_variant = "white"  # "white" or "color"
plex_logo_horizontal_offset = 0  # Adjust right (+) or left (-) by this many pixels (default: 0 for Roboto-Light.ttf)
plex_logo_vertical_offset = 7    # Adjust down (+) or up (-) by this many pixels (default: 7 for Roboto-Light.ttf)

# Max length of a TV or movie summary in characters (set to None to use the default of 525)
max_summary_chars = None

# Max width (in pixels) for wrapped summary text lines
max_summary_width = None  # Set to an integer like 2100, or leave as None for default

# Custom text labels for group types, shown before the Plex logo image; replace to personalize
added_label = "New or updated on"             # Label for recently added items (default: "New or updated on")
aired_label = "Recent release, available on"  # Label for recently aired items (default: "Recent release, available on")
random_label = "Random pick from"             # Label for random picks in mix mode (default: "Random pick from")
default_label = "New or updated on"           # Fallback label for unexpected cases (default: "New or updated on")

# User-configurable font URL and name; if unavailble, script tries fallback fonts
# May need to adjust the vertical adjustment for the Plex logo if it doesn't line
# up, see logo_vertical_adjustment above.
user_font_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'  # URL to download TTF
user_font_name = 'Roboto-Light.ttf'  # Filename to save the font as

# Text colors (can be color names like "white", "black", or RGB tuples like (255, 255, 255))
# Examples of valid color inputs:
#   - "white"
#   - "black"
#   - (255, 0, 0)  # red in RGB tuple form
#   - (150, 150, 150)  # gray in RGB tuple form
# Note: RGB tuples must be 3 integers in range 0-255.
main_color      = "white"             # Main title or header text color
info_color      = (150, 150, 150)     # Subdued secondary info text color (gray tone)
summary_color   = "white"             # Summary text color
metadata_color  = "white"             # Metadata text color (e.g., year, genre)

# Shadow styling
shadow_color    = "black"             # Shadow color behind text
shadow_offset   = 2                   # Shadow offset in pixels (x and y direction)

# Seconds to sleep between processing each media item to reduce Plex server load
plex_api_delay_seconds = 1.0  # Default 1 second; adjust as needed if Plex is struggling to keep up

# === Script Initialization ===
# NOTE: This section and those below are for internal script use only.
# User configurable options are above this point.

# Create a directory to save the backgrounds and clear its contents
background_dir = "plex_backgrounds"
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

# If baseurl or token are not hardcoded, then load from environment variables
baseurl = locals().get('baseurl', os.getenv('PLEX_BASEURL'))  # Plex server base URL either hardcoded or from environment
token = locals().get('token', os.getenv('PLEX_TOKEN'))  # Plex API token either hardcoded from environment

# Validate that either hardcoded values or environment variables are set
if not baseurl or baseurl.strip() == '' or not token or token.strip() == '':
    print("ERROR: Both Plex server base URL and API token are required.")
    print("Please set one of the following options:")
    print("1. Uncomment and set your hardcoded baseurl and token in the script.")
    print("2. Set BASEURL and TOKEN as environment variables in the .env file.")
    exit(1)

# Initialize the PlexServer instance globally
plex_instance = None

# Set the truetype_path based on successful download
truetype_path = None

# Fallback font settings (Roboto Light)
fallback_font_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'  # Roboto Light as fallback
fallback_font_path = 'Roboto-Light.ttf'  # Path for Roboto Light

# Additional fallback fonts (e.g., Lato Light, Poppins Light)
additional_fallback_fonts = [
    {'url': 'https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Light.ttf', 'path': 'OpenSans-Light.ttf'},
    {'url': 'https://github.com/googlefonts/lato/raw/main/fonts/ttf/Lato-Light.ttf', 'path': 'Lato-Light.ttf'},
    {'url': 'https://github.com/googlefonts/poppins/raw/main/fonts/ttf/Poppins-Light.ttf', 'path': 'Poppins-Light.ttf'}
]

# Map plex logo variant to filename
logo_filenames = {
    "color": "plexlogo_color.png",
    "white": "plexlogo.png",
}
# Default to white plex logo if invalid
plex_logo_file = logo_filenames.get(logo_variant, "plexlogo.png")

# === Utility Functions ===

def download_font(url, path):
    """
    Function to download and save the font from the provided URL.
    Returns True if download was successful, False otherwise.
    """
    try:
        if not os.path.exists(path):
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                debug and print(f"[DEBUG] {path} font downloaded and saved.")
                return True
            else:
                print(f"[ERROR] Failed to download {path} font. HTTP Status: {response.status_code}")
                return False
        else:
            debug and print(f"[DEBUG] {path} font already exists.")
            return True
    except Exception as e:
        print(f"[ERROR] Error downloading font: {e}")
        return False

def initialize_plex_connection():
    """
    Initializes the global plex_instance variable if it's not already set.
    """
    global plex_instance  # Access the global plex_instance variable
    if plex_instance is None:  # Ensure we only initialize once
        plex_instance = PlexServer(baseurl, token)
        try:
            plex_version = plex_instance.version
            debug and print(f"[DEBUG] Connected to Plex Server: {plex_version}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Plex server: {e}")
    else:
        debug and print("[DEBUG] Plex server is already initialized.")

def validate_color(color, default):
    """
    Validate color input.
    Accepts color names (str) or RGB tuples (3 ints 0-255).
    Returns a valid color or default.
    """
    if not color:
        return default
    if isinstance(color, str) and color.strip():
        return color
    if isinstance(color, tuple) and len(color) == 3:
        if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
            return color
    return default

def vignette_side(h, w, fade_ratio=5, fade_power=5.0, position="bottom-left"):
    y, x = np.ogrid[0:h, 0:w]
    rx, ry = w * fade_ratio, h * fade_ratio

    dist_x, dist_y = np.ones_like(x, dtype=np.float32), np.ones_like(y, dtype=np.float32)

    if "left" in position:
        dist_x = np.clip(x / rx, 0, 1)
    elif "right" in position:
        dist_x = np.clip((w - x) / rx, 0, 1)

    if "top" in position:
        dist_y = np.clip(y / ry, 0, 1)
    elif "bottom" in position:
        dist_y = np.clip((h - y) / ry, 0, 1)

    if any(corner in position for corner in ["left", "right"]) and \
       any(corner in position for corner in ["top", "bottom"]):
        alpha = np.minimum(dist_x, dist_y)
    else:
        alpha = dist_x * dist_y

    alpha = (alpha ** fade_power * 255).astype(np.uint8)
    mask = Image.fromarray(alpha)
    return mask

def generate_background_fast(input_img, target_width=3000):
    """
    Faster background generator:
    - Blurry darkened canvas
    - Vignette mask for foreground
    - Pastes resized image top-right
    """
    # Step 1: Create blurry/dark canvas
    canvas_rgb = create_blurry_background(input_img, size=(3840, 2160), blur_radius=800)
    canvas_array = np.array(canvas_rgb).astype(np.float32)
    canvas_array = (canvas_array * 0.4).clip(0, 255).astype(np.uint8)  # darken
    canvas_rgb = Image.fromarray(canvas_array)

    # RGBA base
    canvas = Image.new("RGBA", canvas_rgb.size, (0, 0, 0, 255))
    canvas.paste(canvas_rgb, (0, 0))

    # Step 2: Resize input to target_width
    w_percent = target_width / input_img.width
    new_size = (target_width, int(input_img.height * w_percent))
    img_resized = input_img.resize(new_size, Image.LANCZOS).convert("RGBA")

    # Step 3: Apply bottom-left vignette
    h, w = img_resized.height, img_resized.width
    mask = vignette_side(h, w, fade_ratio=0.3, fade_power=2.5, position="bottom-left")
    img_resized.putalpha(mask)

    # Step 4: Paste aligned top-right
    canvas.paste(img_resized, (3840 - w, 0), img_resized)

    return canvas.convert("RGB")




def create_blurry_background(image, size=(3840, 2160), blur_radius=800, dither_strength=16):
    """
    Create a blurry canvas background from the input image, with strong noise to prevent banding.
    """
    bg = image.resize(size, Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    bg_array = np.array(bg).astype(np.float32)

    # Ajoute du bruit aléatoire (dithering doux)
    noise = np.random.uniform(-dither_strength, dither_strength, bg_array.shape)
    bg_array = np.clip(bg_array + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(bg_array)


def validate_shadow_offset(offset, default):
    """
    Validate shadow offset.
    Must be an integer (positive, zero, or negative).
    """
    if isinstance(offset, int):
        return offset
    # Try to convert if possible
    try:
        return int(offset)
    except (ValueError, TypeError):
        return default

def resize_image(image: Image.Image, target_height: int) -> Image.Image:
    """
    Resizes an image to a specific height while maintaining aspect ratio.

    :param image: PIL Image object.
    :param target_height: Desired height in pixels.
    :return: Resized image.
    """
    ratio = target_height / image.height
    target_width = int(image.width * ratio)
    return image.resize((target_width, target_height))

def resize_logo(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """
    Resizes a logo to fit within the given width and height, maintaining aspect ratio.

    :param image: PIL Image object.
    :param max_width: Maximum width.
    :param max_height: Maximum height.
    :return: Resized logo image.
    """
    aspect_ratio = image.width / image.height
    new_width = min(max_width, int(max_height * aspect_ratio))
    new_height = int(new_width / aspect_ratio)

    if new_height > max_height:
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

    return image.resize((new_width, new_height))

def truncate_summary(summary: str, max_chars: int) -> tuple[str, bool]:
    """
    Truncates a summary only if needed, at word boundaries, if it exceeds the character limit.

    Returns:
        - The summary (possibly shortened)
        - A boolean indicating whether it was truncated
    """
    summary = summary or ""

    try:
        shortened = textwrap.shorten(summary, width=max_chars, placeholder="...")
        was_truncated = shortened != summary
        return shortened, was_truncated
    except ValueError:
        # If no space to fit anything (e.g. max_chars < len(placeholder))
        return "...", True

def draw_text_with_shadow(draw, position, text, font, fill_color, shadow_color, shadow_offset=(2,2)):
    """
    Draws text with a shadow effect on an image or canvas.

    The shadow is rendered first with an offset, followed by the main text on top of it.
    The shadow creates a visual effect of depth, making the text stand out.
    """
    # Unpack the x and y coordinates from the provided position tuple
    x, y = position
    # The shadow is drawn slightly offset from the main text using the shadow_offset parameter (default is (2, 2))
    draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
    # The main text is drawn on top of the shadow at the original position (x, y)
    draw.text((x, y), text, font=font, fill=fill_color)

def wrap_text_by_pixel_width(text, font, max_width, draw):
    """
    Wraps text to fit within a pixel width using the specified font and draw context.

    :param text: The input text to wrap.
    :param font: PIL ImageFont object.
    :param max_width: Maximum width in pixels.
    :param draw: PIL ImageDraw.Draw object (needed for textbbox).
    :return: List of lines.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        line_width = draw.textlength(test_line, font=font)

        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:  # if line isn't empty, push it
                lines.append(current_line)
            # If word alone is longer than max width, forcibly split it
            if draw.textlength(word, font=font) > max_width:
                split_word = ""
                for char in word:
                    if draw.textlength(split_word + char, font=font) <= max_width:
                        split_word += char
                    else:
                        lines.append(split_word)
                        split_word = char
                current_line = split_word
            else:
                current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def clean_filename(filename: str) -> str:
    """
    Sanitizes a filename by replacing problematic characters with underscores.

    :param filename: Raw filename.
    :return: Cleaned filename safe for filesystem usage.
    """
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)

def download_logo_in_memory(media_item) -> Image.Image or None:
    """
    Attempts to download the Plex clearLogo image for a media item directly into memory.

    :param media_item: Plex media object.
    :return: PIL Image object of logo, or None if unavailable.
    """
    logo_url = f"{baseurl}/library/metadata/{media_item.ratingKey}/clearLogo?X-Plex-Token={token}"

    try:
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            debug and print(f"Failed to retrieve logo for {media_item.title}. Status: {response.status_code}")
    except Exception as e:
        debug and print(f"Exception downloading logo for {media_item.title}: {e}")

    return None

def generate_background_for_item(item, media_type, group_type='',
                                 base_background=None, overlay=None,
                                 plex_logo=None, target_folder=None):
    """
    Generates a customized background image for a given Plex media item (movie or show).
    Downloads the art directly into memory, applies overlays, adds metadata text, and saves the final image.

    :param item: Plex media item (movie or show).
    :param media_type: 'movie' or 'tv'.
    :param group_type: Category label like 'aired', 'added', or 'random' (for custom text).
    :param base_background: Preloaded background base image.
    :param overlay: Preloaded overlay image.
    :param plex_logo: Preloaded Plex logo image.
    :param target_folder: Folder to save the background image to (defaults to current background_dir).
    """

    if target_folder is None:
        target_folder = background_dir  # fallback to existing global background dir

    # Normalize the path to remove trailing slashes/backslashes
    target_folder = os.path.normpath(target_folder)

    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)

    background_url = item.artUrl
    if not background_url:
        debug and print(f"No background art URL for {item.title}")
        return

    try:
        # Download the background image from Plex
        response = requests.get(background_url, timeout=10)
        response.raise_for_status()

        # Load image directly from bytes into memory
        image = Image.open(BytesIO(response.content))

        # Safe filename
        filename_safe_title = unicodedata.normalize('NFKD', item.title).encode('ASCII', 'ignore').decode('utf-8')
        filename_safe_title = clean_filename(filename_safe_title)

        # Save into target_folder instead of background_dir
        background_filename = os.path.join(target_folder, f"{filename_safe_title}.jpg")

        # Make copies of cached base background and overlay
        canvas = generate_background_fast(image)


        # Prepare to draw
        draw = ImageDraw.Draw(canvas)

        # Load fonts
        try:
            font_title = ImageFont.truetype(truetype_path, size=190)
            font_info = ImageFont.truetype(truetype_path, size=55)
            font_summary = ImageFont.truetype(truetype_path, size=50)
            font_custom = ImageFont.truetype(truetype_path, size=60)
        except (OSError, IOError) as e:
            print(f"[ERROR] Stopped background generation. Failed to load font from '{truetype_path}': {e}")
            return  # Exit the function early; image generation cannot proceed without fonts

        # Info text
        if media_type == 'movie':
            max_genres = 3
            genres_list = [genre.tag for genre in item.genres][:max_genres]
            genres_text = ', '.join(genres_list)
            rating = getattr(item, "audienceRating", None) or getattr(item, "rating", None) or ""
            rating_text = f" IMDb: {rating}" if rating else ""
            duration = getattr(item, "duration", None)
            if duration:
                duration_hours = duration // (60 * 60 * 1000)
                duration_minutes = (duration // (60 * 1000)) % 60
                duration_text = f"{duration_hours}h {duration_minutes}min"
            else:
                duration_text = ""
            contentrating = getattr(item, "contentRating", "")
            contentrating_text = f" {contentrating}" if contentrating else ""

            info_parts = [str(item.year)]

            if genres_text:
                info_parts.append(genres_text)

            if duration_text:
                info_parts.append(duration_text)

            if contentrating_text:
                info_parts.append(contentrating_text)

            if rating_text:
                info_parts.append(rating_text)

            info_text = "  •  ".join(info_parts)
        else:
            max_genres = 3
            genres_list = [genre.tag for genre in item.genres][:max_genres]
            genres_text = ', '.join(genres_list)
            rating = getattr(item, "audienceRating", None) or getattr(item, "rating", None) or ""
            rating_text = f"IMDb: {rating}" if rating else ""
            contentrating = getattr(item, "contentRating", None) or ""
            contentrating_text = contentrating if contentrating else ""
            seasons = getattr(item, "seasons", lambda: [])()
            seasons_count = len(seasons)
            seasons_text = f"{seasons_count} Season" if seasons_count == 1 else f"{seasons_count} Seasons" if seasons_count else ""

            info_parts = [str(item.year)]

            if genres_text:
                info_parts.append(genres_text)

            if seasons_text:
                info_parts.append(seasons_text)

            if contentrating_text:
                info_parts.append(contentrating_text)

            if rating_text:
                info_parts.append(rating_text)

            info_text = "  •  ".join(info_parts)

        # Summary text

        # Use default max length for summary if not explicitly set
        summary_max_chars = max_summary_chars if max_summary_chars is not None else 525

        # Use default max width if not explicitly set
        summary_pixel_width = max_summary_width if max_summary_width is not None else 2100

        # Truncate and wrap summary text
        summary_text, was_truncated = truncate_summary(item.summary, summary_max_chars)
        wrapped_summary_lines = wrap_text_by_pixel_width(
            summary_text,
            font_summary,
            max_width=summary_pixel_width,
            draw=draw
        )
        # Adds a newline between each summary line, may not be enough for fonts
        # with fancy flourishes but should work most of the time. Can improve this
        # logic if it causes issues with line overlap to allow for a custom line spacing
        wrapped_summary = "\n".join(wrapped_summary_lines)

        # Custom label text, uses the user-defined custom text options
        if group_type == 'added':
            custom_text = added_label
        elif group_type == 'aired':
            custom_text = aired_label
        elif group_type == 'random':
            custom_text = random_label
        else:
            custom_text = default_label

        # Info text
        info_position = (210, 650)
        draw_text_with_shadow(
            draw,
            info_position,
            info_text,
            font_info,
            fill_color=info_color,
            shadow_color=shadow_color,
            shadow_offset=(shadow_offset, shadow_offset)
)
        # Summary block
        summary_position = (210, 730)
        draw_text_with_shadow(
            draw,
            summary_position,
            wrapped_summary,
            font_summary,
            fill_color=summary_color,
            shadow_color=shadow_color,
            shadow_offset=(shadow_offset, shadow_offset)
)

        # Custom label and attempt at Plex logo positioning
        draw_bbox = draw.textbbox((0, 0), custom_text, font=font_custom)
        text_width = draw_bbox[2] - draw_bbox[0]
        summary_bbox = draw.textbbox((0, 0), wrapped_summary, font=font_summary)
        summary_block_height = summary_bbox[3] - summary_bbox[1]
        custom_x = 210
        custom_y = summary_position[1] + summary_block_height + 30
        custom_ascent, custom_descent = font_custom.getmetrics()
        text_height = custom_ascent + custom_descent

        logo_width, logo_height = plex_logo.size
        padding = 20
        logo_x = custom_x + text_width + padding + plex_logo_horizontal_offset
        logo_y = custom_y + (text_height - logo_height) // 2 + plex_logo_vertical_offset

        draw_text_with_shadow(
            draw,
            (custom_x, custom_y),
            custom_text,
            font_custom,
            fill_color=metadata_color,
            shadow_color=shadow_color,
            shadow_offset=(shadow_offset, shadow_offset)
        )

        # Paste Plex Logo
        canvas.paste(plex_logo, (logo_x, logo_y), plex_logo)

        # Logo or fallback title
        logo_image = download_logo_in_memory(item)
        if logo_image:
            logo_resized = resize_logo(logo_image, 1300, 400).convert('RGBA')
            logo_position = (210, info_position[1] - logo_resized.height - 25)
            canvas.paste(logo_resized, logo_position, logo_resized)
        else:
            title_position = (200, 420)
            title_text, _ = truncate_summary(item.title, 30)
            draw_text_with_shadow(
                draw,
                title_position,
                title_text,
                font_title,
                fill_color=main_color,
                shadow_color=shadow_color,
                shadow_offset=(shadow_offset, shadow_offset)
            )

        # Save final image
        canvas = canvas.convert('RGB')
        canvas.save(background_filename)
        print(f"Image saved: {background_filename}")

    except requests.exceptions.HTTPError as e:
        print(f"Failed to download background for {item.title}: HTTP error {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading background for {item.title}: {e}")
    except Exception as e:
        print(f"An error occurred while processing {item.title}: {e}")

def download_latest_media(order_by, limit, media_type,
                          target_folder=None,
                          base_background=None,
                          overlay=None,
                          plex_logo=None):
    """
    Downloads and processes the latest media items from Plex library.

    Args:
        order_by (str): Criterion to order items by ('aired' or 'added').
        limit (int): Number of items to process.
        media_type (str): Type of media to fetch ('movie' or 'tv').

    Returns:
        None. Downloads and generates backgrounds for the selected media.
    """
    if target_folder is None:
        target_folder = background_dir

    # Ensure global plex_instance is initialized
    initialize_plex_connection()

    # Early exit if media type not enabled by global flags
    if media_type == 'movie' and not download_movies:
        debug and print("[DEBUG] Movie downloads disabled; skipping.")
        return
    if media_type == 'tv' and not download_series:
        debug and print("[DEBUG] Series downloads disabled; skipping.")
        return

    def sort_movies(movies, key_attr):
        """
        Sort movies based on a given datetime attribute.
        """
        filtered = [m for m in movies if getattr(m, key_attr) is not None]
        return sorted(filtered, key=lambda x: getattr(x, key_attr), reverse=True)

    def sort_shows(shows, key_attr):
        """
        Sort TV shows based on the latest episode's datetime attribute.
        """
        shows_with_dates = []
        for show in shows:
            episodes = show.episodes()
            episodes_with_date = [ep for ep in episodes if getattr(ep, key_attr) is not None]
            if episodes_with_date:
                latest_episode = max(episodes_with_date, key=lambda ep: getattr(ep, key_attr))
                shows_with_dates.append((show, getattr(latest_episode, key_attr)))
        return [s[0] for s in sorted(shows_with_dates, key=lambda x: x[1], reverse=True)]

    if media_type == 'movie':
        media_items = plex_instance.library.search(libtype='movie')
        if order_by == 'aired':
            media_sorted = sort_movies(media_items, 'originallyAvailableAt')
        elif order_by == 'added':
            media_sorted = sort_movies(media_items, 'addedAt')
        else:
            print("Invalid order_by parameter. Please use 'aired' or 'added'.")
            return

    elif media_type == 'tv':
        media_items = plex_instance.library.search(libtype='show')
        if order_by == 'aired':
            media_sorted = sort_shows(media_items, 'originallyAvailableAt')
        elif order_by == 'added':
            media_sorted = sort_shows(media_items, 'addedAt')
        else:
            print("Invalid order_by parameter. Please use 'aired' or 'added'.")
            return
    else:
        print("Invalid media_type parameter. Use 'movie' or 'tv'.")
        return

    debug and print(f"[DEBUG] Processing {len(media_sorted[:limit])} {media_type} items sorted by {order_by}")

    for item in media_sorted[:limit]:
        generate_background_for_item(
            item,
            media_type,
            group_type=order_by,
            base_background=None,
            overlay=None,
            plex_logo=plex_logo,
            target_folder=target_folder
        )
        time.sleep(plex_api_delay_seconds)

def fetch_items(media_type, sort_type, count):
    """
    Fetch media items of a given type sorted by specified attribute.

    Args:
        media_type (str): 'movie' or 'show'.
        sort_type (str): 'aired', 'added', or 'random'.
        count (int): Number of items to fetch.

    Returns:
        list: Sorted/fetched media items.
    """

    # Ensure global plex_instance is initialized
    initialize_plex_connection()

    # Get sections relevant for the media type
    if media_type == 'movie':
        sections = [s for s in plex_instance.library.sections() if s.type == 'movie']
    elif media_type == 'show':
        sections = [s for s in plex_instance.library.sections() if s.type == 'show']
    else:
        print(f"[ERROR] Invalid media_type: {media_type}. Expected 'movie' or 'show'.")
        return []

    # Aggregate all items from all sections
    items = []
    for section in sections:
        items.extend(section.search())

    # Sort/filter items based on sort_type
    if sort_type == 'aired':
        filtered = [i for i in items if getattr(i, 'originallyAvailableAt', None) is not None]
        sorted_items = sorted(filtered, key=lambda x: x.originallyAvailableAt, reverse=True)
    elif sort_type == 'added':
        filtered = [i for i in items if getattr(i, 'addedAt', None) is not None]
        sorted_items = sorted(filtered, key=lambda x: x.addedAt, reverse=True)
    elif sort_type == 'random':
        # Random sample (no sort needed)
        return random.sample(items, min(count, len(items)))
    else:
        return []

    return sorted_items[:count]

def dedup(items, seen):
    """
    Remove duplicates from a list of media items based on their unique ratingKey.

    Args:
        items (list): List of media items to filter.
        seen (set): A set of ratingKeys already encountered; used to track duplicates across multiple calls.

    Returns:
        list: A new list containing only unique media items not previously seen.

    Notes:
    The function updates the 'seen' set with the ratingKeys of newly returned items.
    This helps avoid duplicates when fetching items in multiple batches.
    """
    unique_items = []
    for item in items:
        if item.ratingKey not in seen:
            seen.add(item.ratingKey)
            unique_items.append(item)
    return unique_items

def get_mixed_media(limit, download_movies=True, download_series=True, seen=None):
    """
    Fetches a mixed collection of Plex media items (movies or shows), split evenly
    across three groups: 'aired', 'added', and 'random'. Handles deduplication and
    adaptive overfetching to ensure enough unique items per group.

    Args:
        limit (int): Number of items to fetch per media type.
        download_movies (bool): Whether to include movies.
        download_series (bool): Whether to include TV shows.
        seen (set): Set of ratingKeys already seen for deduplication (per media type).

    Returns:
        list of tuples: Each tuple contains (media_item, group_type), where group_type
        is one of 'aired', 'added', or 'random'.
    """
    # Ensure global plex_instance is initialized
    initialize_plex_connection()

    if seen is None:
        seen = set()

    # Adjust limit to be a multiple of 3 (for even split between aired, added, random)
    original_limit = limit
    adjusted_limit = int(math.ceil(limit / 3.0) * 3)
    if adjusted_limit != original_limit:
        debug and print(f"[DEBUG] Limit adjusted from {original_limit} to {adjusted_limit} for equal group distribution.")
    per_group = adjusted_limit // 3

    final_items_by_group = {'aired': [], 'added': [], 'random': []}

    # Determine media_type for current call
    if download_movies and not download_series:
        media_type = 'movie'
    elif download_series and not download_movies:
        media_type = 'show'
    else:
        media_type = 'movie'  # Fallback: assume movies only if ambiguous

    # Loop through each group type
    for group_type in ['aired', 'added', 'random']:
        collected = []
        attempts = 0
        max_attempts = 3
        overfetch_factor = 1.5

        while len(collected) < per_group and attempts < max_attempts:
            overfetch_count = int(per_group * overfetch_factor)
            fetched = fetch_items(media_type, group_type, overfetch_count)
            unique = dedup(fetched, seen)
            new_items = [item for item in unique if item not in collected]
            collected.extend(new_items)
            attempts += 1
            overfetch_factor *= 0.9  # Slightly decrease each attempt

            debug and print(f"[DEBUG] [{media_type.upper()}][{group_type.upper()}] Attempt {attempts}: "
                            f"Fetched {len(fetched)}, Unique {len(unique)}, "
                            f"New {len(new_items)}, Total Collected {len(collected)}")

            if len(new_items) == 0:
                break  # No more new items likely available

        if len(collected) < per_group:
            debug and print(f"[DEBUG] ⚠️ Only {len(collected)} {media_type}s available for group '{group_type}' (expected {per_group})")

        final_items_by_group[group_type] = collected[:per_group]

        debug and print(f"[DEBUG] [{media_type.upper()}][{group_type.upper()}] Final count: {len(final_items_by_group[group_type])}")
        for item in final_items_by_group[group_type]:
            debug and print(f"  - {item.title} (ratingKey: {item.ratingKey})")

    # Combine all groups into one list with group_type info
    combined = []
    for group_type in ['aired', 'added', 'random']:
        combined.extend((item, group_type) for item in final_items_by_group[group_type])

    return combined

def main_process(order_by, limit, download_movies, download_series,
                 base_background, overlay, plex_logo):
    """
    Main execution logic to select and process media items
    based on the 'order_by' parameter.
    Supports mixed mode or single mode processing.
    """
    # Ensure global plex_instance is initialized
    initialize_plex_connection()

    if order_by == 'mix':
        # Mixed mode: fetch per-type to respect limit for each
        if download_movies:
            movie_seen = set()
            movie_items = get_mixed_media(limit, download_movies=True, download_series=False, seen=movie_seen)
            for item, group_type in movie_items:
                generate_background_for_item(
                    item,
                    media_type='movie',
                    group_type=group_type,
                    base_background=None,
                    overlay=None,
                    plex_logo=plex_logo,
                    target_folder=background_dir
                )
                time.sleep(plex_api_delay_seconds)

        if download_series:
            show_seen = set()
            show_items = get_mixed_media(limit, download_movies=False, download_series=True, seen=show_seen)
            for item, group_type in show_items:
                generate_background_for_item(
                    item,
                    media_type='tv',
                    group_type=group_type,
                    base_background=None,
                    overlay=None,
                    plex_logo=plex_logo,
                    target_folder=background_dir
                )
                time.sleep(plex_api_delay_seconds)

    else:
        # Single mode: download movies and/or series based on order_by parameter
        if download_movies:
            download_latest_media(
                order_by, limit, 'movie',
                target_folder=background_dir,
                base_background=None,
                overlay=overlay,
                plex_logo=plex_logo
            )
        if download_series:
            download_latest_media(
                order_by, limit, 'tv',
                target_folder=background_dir,
                base_background=None,
                overlay=overlay,
                plex_logo=plex_logo
            )

# === Main Execution Logic ===

# Validate user-configurable color and offset settings before use
# Spelling errors can still break this
main_color = validate_color(main_color, "white")
info_color = validate_color(info_color, (150, 150, 150))
summary_color = validate_color(summary_color, "white")
metadata_color = validate_color(metadata_color, "white")

shadow_color = validate_color(shadow_color, "black")
shadow_offset = validate_shadow_offset(shadow_offset, 2)

# Catch errors with Plex logo offset variable
try:
    plex_logo_vertical_offset = int(plex_logo_vertical_offset)
except (NameError, ValueError, TypeError):
    plex_logo_vertical_offset = 7  # Default vertical shift

try:
    plex_logo_horizontal_offset = int(plex_logo_horizontal_offset)
except (NameError, ValueError, TypeError):
    plex_logo_horizontal_offset = 0  # Default horizontal shift

# Attempt to download the user-configured font
debug and print(f"[DEBUG] Attempting to download user-configured font: {user_font_name}")
font_downloaded = download_font(user_font_url, user_font_name)

# If the user-configured font download succeeds, set truetype_path
if font_downloaded:
    truetype_path = user_font_name

# Step 2: If user-configured font fails, and user font isn't the same as default font
# fall back to the default font
if not font_downloaded and not (
    user_font_url == fallback_font_url and user_font_name == fallback_font_path
):
    print("[ERROR] User font download failed. Falling back to default font...")
    font_downloaded = download_font(fallback_font_url, fallback_font_path)

    if font_downloaded:
        truetype_path = fallback_font_path

# Step 3: If default font also fails, try additional fallback fonts
if not font_downloaded:
    for fallback in additional_fallback_fonts:
        print(f"[ERROR] Default font download failed. Trying additional fallback font: {fallback['path']}")
        font_downloaded = download_font(fallback['url'], fallback['path'])

        if font_downloaded:
            truetype_path = fallback['path']
            break

# If no font is found, print an error and exit
if not font_downloaded:
    print("[ERROR] No valid font available. The script cannot proceed without a font.")
    exit(1)  # Exit the script if no font is available

if __name__ == "__main__":
    # Load overlay resources once at module load
    BASE_PATH = os.path.dirname(__file__)
    try:
        plex_logo = Image.open(os.path.join(BASE_PATH, plex_logo_file)).convert('RGBA')
    except Exception as e:
        print(f"[ERROR] Failed to load overlay images: {e}")
        exit(1)

    # Execute the main process with the configured parameters
    main_process(
        order_by=order_by,
        limit=limit,
        download_movies=download_movies,
        download_series=download_series,
        base_background=None,
        overlay=None,
        plex_logo=plex_logo
    )
