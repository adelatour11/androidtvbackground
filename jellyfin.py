import requests
import os
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import unicodedata
import shutil
import textwrap
from dotenv import load_dotenv
load_dotenv(verbose=True)

# Jellyfin Server Configuration (Global Parameters)
baseurl = os.getenv('JELLYFIN_BASEURL')
token = os.getenv('JELLYFIN_TOKEN')
user_id = os.getenv('JELLYFIN_USER_ID')
# try to connect to the server and get the user name

try:
    print('Trying to connect to JellyFin')
    print(f'baseurl:{baseurl}')
    print(f'token:{token}')
    print(f'user_id:{user_id}')
    url = f"{baseurl}/Users/{user_id}"
    response = requests.get(url, headers={"X-Emby-Token": token})
    response.raise_for_status()
    data = response.json()
    print(f"Connected to Jellyfin! User name: {data.get('Name')}")
except requests.exceptions.RequestException as e:
    print(f"Failed to connect to Jellyfin: {e}")
    exit(1)

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
order_by = 'DateCreated' # 'DateCreated', 'DateLastContentAdded', 'PremiereDate'
download_movies = True
download_series = True
limit = 10
excluded_genres = ['Horror', 'Thriller']
excluded_tags = ['Adult', 'Violence']
excluded_libraries = ['Web Videos']

# Create a directory to save the backgrounds and clear its contents if it exists
background_dir = "jellyfin_backgrounds"
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)


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
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename

def download_logo_in_memory(media_item):
    logo_url = f"{baseurl}/Items/{media_item['Id']}/Images/Logo?api_key={token}"
    
    try:
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo_image = Image.open(BytesIO(response.content))
            return logo_image  # Return the logo as a PIL Image object
        else:
            print(f"Failed to retrieve logo for {media_item['Name']}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while downloading the logo for {media_item['Name']}: {e}")
        return None

def get_excluded_library_paths():
    """Fetch library IDs based on excluded library names."""
    headers = {'X-Emby-Token': token}
    response = requests.get(f"{baseurl}/Library/VirtualFolders", headers=headers)
    
    if response.status_code == 200:
        libraries = response.json()
        # print(json.dumps(libraries,indent=4))
        locs = [lib['Locations'] for lib in libraries if lib['Name'] in excluded_libraries]
        locs = [item for sublist in locs for item in sublist]
        return set(locs)
    else:
        print("Failed to retrieve library information.")
        return set()

excluded_library_paths = get_excluded_library_paths()

def download_latest_media(order_by, limit, media_type):
    headers = {'X-Emby-Token': token}
    params = {
        'SortBy': order_by,
        'Limit': limit,
        'IncludeItemTypes': media_type,
        'Recursive': 'true',
        'SortOrder': 'Descending',
        'Fields': 'Path,Overview,Genres,CommunityRating,PremiereDate,Tags',
    }
    response = requests.get(f"{baseurl}/Users/{user_id}/Items", headers=headers, params=params)

    if response.status_code == 200:
        media_items = response.json()['Items']
    else:
        print(f"Failed to retrieve media items. Status code: {response.status_code}")
        return

    # Filter out excluded genres, tags, and libraries
    filtered_items = []

    for item in media_items:
        if any(genre in excluded_genres for genre in item.get('Genres', [])):
            continue
        if any(tag in excluded_tags for tag in item.get('Tags', [])):
            continue
        if any(excluded_path in item.get('Path') for excluded_path in excluded_library_paths):
            continue
        filtered_items.append(item)

    # Process the sorted media
    for item in filtered_items:
        # Get the URL of the background image
        background_url = f"{baseurl}/Items/{item['Id']}/Images/Backdrop?api_key={token}"

        if background_url:
            try:
                # Download the background image with a timeout of 10 seconds
                response = requests.get(background_url, timeout=10)

                if response.status_code == 200:
                    filename_safe_title = unicodedata.normalize('NFKD', item['Name']).encode('ASCII', 'ignore').decode('utf-8')
                    filename_safe_title = clean_filename(filename_safe_title)
                    background_filename = os.path.join(background_dir, f"{filename_safe_title}_{item['ProductionYear']}.jpg")
                    
                    with open(background_filename, 'wb') as f:
                        f.write(response.content)
                    
                    image = Image.open(background_filename)
                    bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
                    
                    # Resize the image to have a height of 1500 pixels
                    image = resize_image(image, 1500)

                    overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
                    jellyfinlogo = Image.open(os.path.join(os.path.dirname(__file__), "jellyfinlogo.png"))

                    bckg.paste(image, (1175, 0))
                    bckg.paste(overlay, (1175, 0), overlay)
                    bckg.paste(jellyfinlogo, (680, 890), jellyfinlogo)

                    # Add text on top of the image with shadow effect
                    draw = ImageDraw.Draw(bckg)
                    
                    # Font Setup
                    font_title = ImageFont.truetype(truetype_path, size=190)
                    font_info = ImageFont.truetype(truetype_path, size=55)
                    font_summary = ImageFont.truetype(truetype_path, size=50)
                    font_metadata = ImageFont.truetype(truetype_path, size=50)
                    font_custom = ImageFont.truetype(truetype_path, size=60)                 
                    
                    title_text = f"{item['Name']}"
                    logo_image = download_logo_in_memory(item)

                    if media_type == 'Movie':
                        if 'CommunityRating' in item:
                            rating_text = f" IMDb: {item['CommunityRating']:.1f}"
                        else:
                            rating_text = ""
                        duration_ticks = item['RunTimeTicks']
                        duration_minutes = duration_ticks // (10**7 * 60)
                        duration_text = f"{duration_minutes // 60}h{duration_minutes % 60}min"
                        info_text = f"{item['PremiereDate'][:4]}  •  {', '.join(item['Genres'])}  •  {duration_text}  •  {rating_text}"
                    else:
                        if 'CommunityRating' in item:
                            rating_text = f" IMDb: {item['CommunityRating']:.1f}"
                        else:
                            rating_text = ""
                        
                        seasons_url = f"{baseurl}/Shows/{item['Id']}/Seasons?api_key={token}"
                        response = requests.get(seasons_url, timeout=10)

                        if response.status_code == 200:
                            full_response_data = response.json()
                            
                            if 'Items' in full_response_data and isinstance(full_response_data['Items'], list):
                                actual_seasons = [
                                    s for s in full_response_data['Items'] 
                                    if s.get('Type') == 'Season' and s.get('IndexNumber', 0) > 0
                                ]
                                
                                seasons_count = len(actual_seasons)
                                seasons_text = f"Season" if seasons_count == 1 else f"Seasons"
                                seasons_text = f"{seasons_count} {seasons_text} • " 
                            else:
                                seasons_text = ""
                        else:
                            seasons_text = ""
                        
                        info_text = f"{item['PremiereDate'][:4]}  •  {', '.join(item['Genres'])}  •  {seasons_text}{rating_text}"

                    summary_text = truncate_summary(item['Overview'], 175)
                    custom_text = "Now Available on"

                    # Draw Text (with shadow for better visibility)
                    shadow_color = "black"
                    main_color = "white"
                    info_color = (150, 150, 150)
                    summary_color = "white"
                    metadata_color = "white"
                    wrapped_summary = "\n".join(textwrap.wrap(summary_text, width=95))

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
                    print(f"Failed to download background for {item['Name']}")
            except Exception as e:
                print(f"An error occurred while processing {item['Name']}: {e}")

        time.sleep(1)

# Download the latest movies according to the specified order and limit
if download_movies:
    download_latest_media(order_by, limit, 'Movie')

# Download the latest TV series according to the specified order and limit
if download_series:
    download_latest_media(order_by, limit, 'Series')
