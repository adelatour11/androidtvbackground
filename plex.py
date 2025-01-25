import requests
import os
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.request import urlopen
import unicodedata
import re
import shutil
import textwrap
from plexapi.server import PlexServer

# Plex Server Configuration (Global Parameters)
baseurl = 'http://XXX:XXX'
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
limit = 10

# Create a directory to save the backgrounds
background_dir = "plex_backgrounds"
# Clear the contents of the folder
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
    os.makedirs(background_dir)


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
    cleaned_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    return cleaned_filename

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

def download_latest_media(order_by, limit, media_type):
    plex = PlexServer(baseurl, token)

    if media_type == 'movie' and download_movies:
        media_items = plex.library.search(libtype='movie')
    elif media_type == 'tv' and download_series:
        media_items = plex.library.search(libtype='show')
    else:
        print("Invalid media_type parameter.")
        return

    # Adjust sorting logic for TV shows based on episodes
    if media_type == 'tv' and order_by == 'added':
        series_with_dates = []
        for series in media_items:
            episodes = series.episodes()
            if episodes:
                # Filter out episodes with no addedAt date
                episodes_with_added_date = [ep for ep in episodes if ep.addedAt is not None]
                if episodes_with_added_date:
                    # Find the latest episode by addedAt
                    latest_episode = max(episodes_with_added_date, key=lambda ep: ep.addedAt)
                    latest_date = latest_episode.addedAt
                    series_with_dates.append((series, latest_date))

        # Sort series based on the latest episode's added date
        media_sorted = [item[0] for item in sorted(series_with_dates, key=lambda x: x[1], reverse=True)]
    elif media_type == 'tv' and order_by == 'aired':
        series_with_dates = []
        for series in media_items:
            episodes = series.episodes()
            if episodes:
                # Filter out episodes with no air date
                episodes_with_air_date = [ep for ep in episodes if ep.originallyAvailableAt is not None]
                if episodes_with_air_date:
                    # Find the latest episode by air date
                    latest_episode = max(episodes_with_air_date, key=lambda ep: ep.originallyAvailableAt)
                    latest_date = latest_episode.originallyAvailableAt
                    series_with_dates.append((series, latest_date))

        # Sort series based on the latest episode's air date
        media_sorted = [item[0] for item in sorted(series_with_dates, key=lambda x: x[1], reverse=True)]
    else:
        print("Invalid order_by parameter. Please use 'aired' or 'added'.")
        return

    for item in media_sorted[:limit]:
        # Get the URL of the background image
        background_url = item.artUrl

        if background_url:
            try:
                # Download the background image with a timeout of 10 seconds
                response = requests.get(background_url, timeout=10)
                if response.status_code == 200:
                    filename_safe_title = unicodedata.normalize('NFKD', item.title).encode('ASCII', 'ignore').decode('utf-8')
                    filename_safe_title = clean_filename(filename_safe_title)
                    background_filename = os.path.join(background_dir, f"{filename_safe_title}.jpg")
                    with open(background_filename, 'wb') as f:
                        f.write(response.content)
                    
                    image = Image.open(background_filename)
                    bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
                    
                    # Resize the image to have a height of 1500 pixels
                    image = resize_image(image, 1500)

                    overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
                    plexlogo = Image.open(os.path.join(os.path.dirname(__file__), "plexlogo.png"))

                    bckg.paste(image, (1175, 0))
                    bckg.paste(overlay, (1175, 0), overlay)
                    bckg.paste(plexlogo, (680, 890), plexlogo)

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
                    info_color = (150, 150, 150)
                    summary_color = "white"
                    metadata_color = "white"
                    wrapped_summary = "\n".join(textwrap.wrap(summary_text, width=95)) + "..."

                    title_position = (200, 420)
                    summary_position = (210, 730)
                    shadow_offset = 2
                    info_position = (210, 650)
                    metadata_position = (210, 820)
                    custom_position = (210, 870)

                    draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_info, fill=shadow_color)
                    draw.text(info_position, info_text, font=font_info, fill=info_color)
                    draw.text((summary_position[0] + shadow_offset, summary_position[1] + shadow_offset), wrapped_summary, font=font_summary, fill=shadow_color)
                    draw.text(summary_position, wrapped_summary, font=font_summary, fill=summary_color)
                    draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)
                    draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)

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
