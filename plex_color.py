# Plex background generator using a colored background and vignetting effect
import requests
import numpy as np
from datetime import datetime
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import unicodedata
import re
import textwrap
from plexapi.server import PlexServer

# Plex Server Configuration (Global Parameters)
baseurl = 'XXXX'
token = 'XXXX'

# Save font locally
truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'
truetype_path = 'Roboto-Light.ttf'
if not os.path.exists(truetype_path):
    try:
        response = requests.get(truetype_url, timeout=10)
        if response.status_code == 200:
            with open(truetype_path, 'wb') as f:
                f.write(response.content)
            print("Roboto-Light font saved")
        else:
            print(f"Failed to download Roboto-Light font. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading the Roboto-Light font: {e}")

# Set the order_by parameter to 'aired' or 'added'
order_by = 'added'
download_movies = True
download_series = True
limit = 6

# Create a directory to save the backgrounds
background_dir = "plex_backgrounds"
 Clear the contents of the folder
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
    os.makedirs(background_dir)

# Get current date in YYYYMMDD format
date_str = datetime.now().strftime("%Y%m%d")

def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

def resize_logo(image, width, height):
    aspect_ratio = image.width / image.height
    new_width = width
    new_height = int(new_width / aspect_ratio)
    
    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)
    
    resized_img = image.resize((new_width, new_height))
    return resized_img

def truncate_summary(summary, max_chars):
    return textwrap.shorten(summary, width=max_chars, placeholder="...")

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned = ''.join(c if c.isalnum() or c in '._-' else '_' for c in filename)
    # Collapse multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned
    
def download_logo_in_memory(media_item):
    logo_url = f"{baseurl}/library/metadata/{media_item.ratingKey}/clearLogo?X-Plex-Token={token}"
    
    try:
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo_image = Image.open(BytesIO(response.content))
            return logo_image  # Return the logo as a PIL Image object
        else:
            print(f"Failed to retrieve logo for {media_item.title}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while downloading the logo for {media_item.title}: {e}")
        return None

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


def download_latest_media(order_by, limit, media_type):
    plex = PlexServer(baseurl, token)

    if media_type == 'movie' and download_movies:
        media_items = plex.library.search(libtype='movie')

        # Sort movies based on the specified order_by
        if order_by == 'aired':
            # Sort movies by their release date
            media_sorted = sorted(
                [movie for movie in media_items if movie.originallyAvailableAt is not None],
                key=lambda x: x.originallyAvailableAt,
                reverse=True
            )
        elif order_by == 'added':
            # Sort movies by the date they were added to the library
            media_sorted = sorted(
                [movie for movie in media_items if movie.addedAt is not None],
                key=lambda x: x.addedAt,
                reverse=True
            )
        else:
            print("Invalid order_by parameter. Please use 'aired' or 'added'.")
            return
    elif media_type == 'tv' and download_series:
        media_items = plex.library.search(libtype='show')

        if order_by == 'aired':
            # Sort TV series by the latest episode's air date
            series_with_dates = []
            for series in media_items:
                episodes = series.episodes()
                episodes_with_air_date = [ep for ep in episodes if ep.originallyAvailableAt is not None]
                if episodes_with_air_date:
                    latest_episode = max(episodes_with_air_date, key=lambda ep: ep.originallyAvailableAt)
                    latest_date = latest_episode.originallyAvailableAt
                    series_with_dates.append((series, latest_date))
            media_sorted = [item[0] for item in sorted(series_with_dates, key=lambda x: x[1], reverse=True)]
        elif order_by == 'added':
            # Sort TV series by the latest episode's added date
            series_with_dates = []
            for series in media_items:
                episodes = series.episodes()
                episodes_with_added_date = [ep for ep in episodes if ep.addedAt is not None]
                if episodes_with_added_date:
                    latest_episode = max(episodes_with_added_date, key=lambda ep: ep.addedAt)
                    latest_date = latest_episode.addedAt
                    series_with_dates.append((series, latest_date))
            media_sorted = [item[0] for item in sorted(series_with_dates, key=lambda x: x[1], reverse=True)]
        else:
            print("Invalid order_by parameter. Please use 'aired' or 'added'.")
            return
    else:
        print("Invalid media_type parameter.")
        return


    # Process the sorted media
    for item in media_sorted[:limit]:
        # Get the URL of the background image
        background_url = item.artUrl

        if background_url:
            try:
                # Download the background image with a timeout of 10 seconds
                response = requests.get(background_url, timeout=10)
                if response.status_code == 200:
                    filename_safe_title = clean_filename(unicodedata.normalize('NFKD', item.title).encode('ASCII', 'ignore').decode('utf-8'))
                    background_filename = os.path.join(background_dir, f"{filename_safe_title}_{date_str}.jpg")
                    with open(background_filename, 'wb') as f:
                        f.write(response.content)
                    
                    image = Image.open(background_filename)


                    # Apply vignette canvas instead of original background and overlay
                    bckg = generate_background_fast(image, target_width=2700)


                    # Resize the image to have a height of 1500 pixels
                    image = resize_image(image, 1500)

                    # Add text on top of the image with shadow effect
                    draw = ImageDraw.Draw(bckg)
                    
                    # Font Setup
                    font_title = ImageFont.truetype(truetype_path, size=190)
                    font_info = ImageFont.truetype(truetype_path, size=55)
                    font_summary = ImageFont.truetype(truetype_path, size=50)
                    font_metadata = ImageFont.truetype(truetype_path, size=50)
                    font_custom = ImageFont.truetype(truetype_path, size=60)                 
                    
                    title_text = f"{item.title}"
                    logo_image = download_logo_in_memory(item)

                    if media_type == 'movie':
                        if item.audienceRating:
                            rating_text = f" IMDb: {item.audienceRating}"
                        elif item.rating:
                            rating_text = f" IMDb: {item.rating}"
                        else:
                            rating_text = ""
                        duration_hours = item.duration // (60*60*1000)
                        duration_minutes = (item.duration // (60*1000)) % 60
                        duration_text = f"{duration_hours}h{duration_minutes}min"
                        info_text = f"{item.year}  •  {', '.join([genre.tag for genre in item.genres])}  •  {duration_text}  •  {rating_text}"
                    else:
                        if item.audienceRating:
                            rating_text = f" IMDb: {item.audienceRating}"
                        elif item.rating:
                            rating_text = f" IMDb: {item.rating}"
                        else:
                            rating_text = ""
                        seasons_count = len(item.seasons())
                        seasons_text = "Season" if seasons_count == 1 else "Seasons"
                        info_text = f"{item.year}  •  {', '.join([genre.tag for genre in item.genres])}  •  {seasons_count} {seasons_text}  •  {rating_text}"
                    summary_text = truncate_summary(item.summary, 175)
                    custom_text = "Now Available on"

                    # Draw Text (with shadow for better visibility)
                    shadow_color = "black"
                    main_color = "white"
                    info_color = "white"
                    summary_color = "white"
                    metadata_color = "white"

                    # Wrap summary
                    wrapped_summary = "\n".join(textwrap.wrap(summary_text, width=65)) + "..."
                    lines = wrapped_summary.split("\n")

                    # Compute height of one line using getbbox
                    bbox = font_summary.getbbox("A")  # (left, top, right, bottom)
                    line_height = bbox[3] - bbox[1]

                    # Total height of wrapped summary
                    summary_height = line_height * len(lines)

                    # Compute height of one line using getbbox
                    bbox = font_summary.getbbox("A")  # (left, top, right, bottom)
                    line_height = bbox[3] - bbox[1]

                    title_position = (200, 420)
                    summary_position = (210, 730)
                    shadow_offset = 2
                    info_position = (210, 650)
                    metadata_position = (210, 820)
                    custom_position = (210, summary_position[1] + summary_height + 100)


                    draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_info, fill=shadow_color)
                    draw.text(info_position, info_text, font=font_info, fill=info_color)
                    draw.text((summary_position[0] + shadow_offset, summary_position[1] + shadow_offset), wrapped_summary, font=font_summary, fill=shadow_color)
                    draw.text(summary_position, wrapped_summary, font=font_summary, fill=summary_color)
                    draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)
                    draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)

                    plexlogo = Image.open(os.path.join(os.path.dirname(__file__), "plexlogo.png"))

                    # Paste Plex logo only
                    plexlogo = Image.open(os.path.join(os.path.dirname(__file__), "plexlogo.png"))
                    bckg.paste(plexlogo, (680, custom_position[1] + 20), plexlogo)

                    if logo_image:
                        logo_resized = resize_logo(logo_image, 1300, 400).convert('RGBA')
                        logo_position = (210, info_position[1] - logo_resized.height - 25)
                        bckg.paste(logo_resized, logo_position, logo_resized)
                    else:
                        draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), truncate_summary(title_text,30), font=font_title, fill=shadow_color)
                        draw.text(title_position, truncate_summary(title_text,30), font=font_title, fill=main_color)

                    bckg = bckg.convert('RGB')
                    bckg.save(background_filename)
                    print(f"Image saved: {background_filename}")

                else:
                    print(f"Failed to download background for {item.title}")
            except Exception as e:
                print(f"An error occurred while processing {item.title}: {e}")

        time.sleep(1)

# Download the latest movies according to the specified order and limit
if download_movies:
    download_latest_media(order_by, limit, 'movie')

# Download the latest TV series according to the specified order and limit
if download_series:
    download_latest_media(order_by, limit, 'tv')
