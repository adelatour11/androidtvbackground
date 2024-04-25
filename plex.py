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


truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'

from plexapi.server import PlexServer

# Set the order_by parameter to 'aired' or 'added'
order_by = 'added'
download_movies = True
download_series = True
# Set the number of latest movies to download
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

def truncate_summary(summary, max_chars):
    if len(summary) > max_chars:
        return summary[:max_chars]
    else:
        return summary

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    return cleaned_filename

def download_latest_media(order_by, limit, media_type):
    baseurl = 'http://XXXX:32400'
    token = 'XXXX'
    plex = PlexServer(baseurl, token)

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
                    background_filename = os.path.join(background_dir, f"{filename_safe_title}.jpg")
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
                    bckg.paste(plexlogo, (680, 970),plexlogo)

                    # Add text on top of the image with shadow effect
                    draw = ImageDraw.Draw(bckg)
                    
                    #Text Font
                    font_title = ImageFont.truetype(urlopen(truetype_url), size=190)
                    font_info = ImageFont.truetype(urlopen(truetype_url), size=55)
                    font_summary = ImageFont.truetype(urlopen(truetype_url), size=45)
                    font_metadata = ImageFont.truetype(urlopen(truetype_url), size=50)
                    font_custom = ImageFont.truetype(urlopen(truetype_url), size=60)                 
                    
                    title_text = f"{item.title}"
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
                        if seasons_count == 1:
                            seasons_text = "Season"
                        else:
                            seasons_text = "Seasons"
                        info_text = f"{item.year}  •  {', '.join([genre.tag for genre in item.genres])}  •  {seasons_count} {seasons_text}  •  {rating_text}"
                    summary_text = truncate_summary(item.summary, 175)
                    custom_text = "Now Available on"
                    
                    title_text_width, title_text_height = draw.textlength(title_text, font=font_title), draw.textlength(title_text, font=font_title)
                    info_text_width, info_text_height = draw.textlength(info_text, font=font_info), draw.textlength(info_text, font=font_info)
                    custom_text_width, custom_text_height = draw.textlength(custom_text, font=font_info), draw.textlength(custom_text, font=font_custom)
                    summary_text_width, summary_text_height = draw.textlength(summary_text, font=font_summary), draw.textlength(summary_text, font=font_summary)
                    metadata_text_width, metadata_text_height = draw.textlength(info_text, font=font_metadata), draw.textlength(info_text, font=font_metadata)
                    
                    #Position
                    title_position = (200, 540)
                    summary_position = (210, 830)
                    info_position = (210, 520)
                    metadata_position = (210, 920)
                    custom_position = (210, 950)
                    shadow_offset = 2

                    #Color
                    shadow_color = "black"
                    main_color = "white"
                    info_color = "white"
                    summary_color = (150,150,150)  # Grey color for the summary
                    metadata_color = "white"

                    # Draw shadow for title
                    draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title_text, font=font_title, fill=shadow_color)
                    # Draw main title text
                    draw.text(title_position, title_text, font=font_title, fill=main_color)

                    # Wrap summary text
                    wrapped_summary = "\n".join(textwrap.wrap(summary_text, width=95)) + "..."
                    
                    # Draw shadow for info
                    draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_summary, fill=shadow_color)
                    # Draw main info text
                    draw.text(info_position, info_text, font=font_summary, fill=summary_color)
                    
                    # Draw shadow for summary text
                    draw.text((summary_position[0] + shadow_offset, summary_position[1] + shadow_offset), wrapped_summary, font=font_summary, fill=shadow_color)
                    # Draw summary text
                    draw.text(summary_position, wrapped_summary, font=font_summary, fill=summary_color)


                    # Draw shadow for custom text
                    draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)                  
                    # Draw custom text
                    draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)



                    
                    # Save the modified image
                    bckg = bckg.convert('RGB')  # Convert image to RGB mode to save as JPEG
                    bckg.save(background_filename)
                    print(f"Image saved: {background_filename}")

                    
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
