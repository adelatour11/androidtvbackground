import requests
import os
import time
from PIL import Image, ImageDraw, ImageFont  # Import Image module
from io import BytesIO
from urllib.request import urlopen
import unicodedata
import re

truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'

from plexapi.server import PlexServer

# Set the order_by parameter to 'aired' or 'added'
order_by = 'added'
download_movies = True
download_series = True
# Set the number of latest movies to download
limit = 10

def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

def truncate_summary(summary, max_chars):
    if len(summary) > max_chars:
        return summary[:max_chars-3] + "..."
    else:
        return summary

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    return cleaned_filename

def download_latest_media(order_by, limit, media_type):
    baseurl = 'http://XXXXX:32400'
    token = 'XXXXX'
    plex = PlexServer(baseurl, token)

    # Create a directory to save the backgrounds
    background_dir = f"plex_backgrounds"
    os.makedirs(background_dir, exist_ok=True)  # Create the directory if it doesn't exist

    # Delete the contents of the folder
    for file in os.listdir(background_dir):
        file_path = os.path.join(background_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    os.makedirs(background_dir, exist_ok=True)

    if media_type == 'movie' and download_movies:
        media_items = plex.library.search(libtype='movie')
    elif media_type == 'tv' and download_series:
        media_items = plex.library.search(libtype='show')
    else:
        print("Invalid media_type parameter.")
        return
    
    if order_by == 'aired':
        media_sorted = sorted(media_items, key=lambda x: x.originallyAvailableAt, reverse=True)
    elif order_by == 'added':
        media_sorted = sorted(media_items, key=lambda x: x.addedAt, reverse=True)
    else:
        print("Invalid order_by parameter. Please use 'aired' or 'added'.")
        return

    for item in media_sorted[:limit]:
        print(item.title)
        # Get the URL of the background image
        background_url = item.artUrl

        if background_url:
            try:
                # Download the background image with a timeout of 10 seconds
                response = requests.get(background_url, timeout=10)
                if response.status_code == 200:
                    # Remove problematic characters from the item title
                    filename_safe_title = unicodedata.normalize('NFKD', item.title).encode('ASCII', 'ignore').decode('utf-8')
                    filename_safe_title = clean_filename(filename_safe_title)
                    # Save the background image to a file
                    background_filename = os.path.join(background_dir, f"{filename_safe_title}_background.jpg")
                    with open(background_filename, 'wb') as f:
                        f.write(response.content)
                    
                    # Open the background image with PIL
                    image = Image.open(background_filename)
                    bckg = Image.open(os.path.join(os.path.dirname(__file__),"bckg.png"))
                    
                    # Resize the image to have a height of 1080 pixels
                    image = resize_image(image, 1500)

                    # Open overlay image
                    overlay = Image.open(os.path.join(os.path.dirname(__file__),"overlay.png"))
                    plexlogo = Image.open(os.path.join(os.path.dirname(__file__),"plexlogo.png"))

                    bckg.paste(image, (1175, 0))
                    bckg.paste(overlay, (1175,0), overlay)
                    bckg.paste(plexlogo, (215, 530),plexlogo)


                    # Add text on top of the image with shadow effect
                    draw = ImageDraw.Draw(bckg)
                    font_title = ImageFont.truetype(urlopen(truetype_url), size=190)
                    font_info = ImageFont.truetype(urlopen(truetype_url), size=75)
                    font_summary = ImageFont.truetype(urlopen(truetype_url), size=50)
                    title_text = f"{item.title}"
                    info_text = "Now Available"
                    summary_text = truncate_summary(item.summary, 130)
                    title_text_width, title_text_height = draw.textlength(title_text, font=font_title), draw.textlength(title_text, font=font_title)
                    info_text_width, info_text_height = draw.textlength(info_text, font=font_info), draw.textlength(info_text, font=font_info)
                    summary_text_width, summary_text_height = draw.textlength(summary_text, font=font_summary), draw.textlength(summary_text, font=font_summary)
                    title_position = (200, 540)
                    summary_position = (210, 780)
                    info_position = (210, 850)
                    shadow_offset = 1
                    shadow_color = "black"
                    main_color = "white"
                    info_color = "white"
                    summary_color = (150,150,150)  # Grey color for the summary
                    # Draw shadow for title
                    draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title_text, font=font_title, fill=shadow_color)
                    # Draw main title text
                    draw.text(title_position, title_text, font=font_title, fill=main_color)
                    # Draw shadow for info
                    draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_info, fill=shadow_color)
                    # Draw main info text
                    draw.text(info_position, info_text, font=font_info, fill=info_color)
                    # Draw summary text
                    draw.text(summary_position, summary_text, font=font_summary, fill=summary_color)
                    
                    # Save the modified image
                    bckg = bckg.convert('RGB')  # Convert image to RGB mode to save as JPEG
                    bckg.save(background_filename)
                    
                    print(f"Background saved: {background_filename}")
                else:
                    print(f"Failed to download background for {item.title}")
            except Exception as e:
                print(f"An error occurred while processing {item.title}: {e}")
        else:
            print(f"No background image found for {item.title}")

        # Adding a small delay to give the server some time to respond
        time.sleep(1)

# Download the latest movies according to the specified order and limit
if download_movies:
    download_latest_media(order_by, limit, 'movie')

# Download the latest TV series according to the specified order and limit
if download_series:
    download_latest_media(order_by, limit, 'tv')
