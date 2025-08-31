import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, UnidentifiedImageError
from io import BytesIO
import os
import shutil
import textwrap
from dotenv import load_dotenv

load_dotenv(verbose=True)

# Replace with your actual Trakt API key, TMDB API Read Access Token, username, and list name
TRAKT_API_KEY = os.getenv('TRAKT_API_KEY')
TRAKT_USERNAME = os.getenv('TRAKT_USERNAME')
TRAKT_LISTNAME = os.getenv('TRAKT_LISTNAME')
TMDB_BEARER_TOKEN = os.getenv('TMDB_BEARER_TOKEN')
TMDB_BASE_URL = os.getenv('TMDB_BASE_URL')

# Set your TMDB API Read Access Token key here after Bearer
tmdb_headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
}

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

# Function to truncate the overview text if it exceeds a certain length
def truncate_overview(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars]
    else:
        return overview

# Function to clean filenames by removing problematic characters
def clean_filename(filename):
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename

# Function to fetch movies and shows from Trakt API
def get_trakt_movies_and_shows(api_key, username, list_name):
    url = f"https://api.trakt.tv/users/{username}/lists/{list_name}/items"
    traktheaders = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": api_key
    }

    response = requests.get(url, headers=traktheaders)
    if response.status_code == 200:
        items = response.json()
        movies = [(item['movie']['title'], item['movie']['ids']['tmdb']) for item in items if item['type'] == 'movie']
        shows = [(item['show']['title'], item['show']['ids']['tmdb']) for item in items if item['type'] == 'show']
        return movies, shows
    else:
        print(f"Error: Unable to fetch list (status code {response.status_code})")
        return [], []

# Function to fetch the logo for a movie or TV show from TMDB
def get_logo(media_type, media_id, language="en"):
    logo_url = f"{TMDB_BASE_URL}{media_type}/{media_id}/images?language={language}"
    logo_response = requests.get(logo_url, headers=tmdb_headers)
    logo_data = logo_response.json()
    if logo_response.status_code == 200:
        logos = logo_response.json().get("logos", [])
        for logo in logos:
            if logo["iso_639_1"] == "en" and logo["file_path"].endswith(".png"):
                return logo["file_path"]
    return None

# Function to resize an image while maintaining aspect ratio
def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

# Function to resize a logo while maintaining aspect ratio
def resize_logo(image, width, height):
    aspect_ratio = image.width / image.height
    new_width = width
    new_height = int(new_width / aspect_ratio)
    
    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)
    
    resized_img = image.resize((new_width, new_height))
    return resized_img

# Function to get details of a TV show from TMDB
def get_tv_show_details(tv_id):
    tv_details_url = f'{TMDB_BASE_URL}tv/{tv_id}?language=en-US'
    tv_details_response = requests.get(tv_details_url, headers=tmdb_headers)
    return tv_details_response.json()

# Function to get details of a movie from TMDB
def get_movie_details(movie_id):
    movie_details_url = f'{TMDB_BASE_URL}movie/{movie_id}?language=en-US'
    movie_details_response = requests.get(movie_details_url, headers=tmdb_headers)
    return movie_details_response.json()

# Create a directory to save the backgrounds and clear its contents if it exists
background_dir = "trakt_backgrounds"
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

# Function to fetch and save background images for movies and shows
def fetch_and_save_background_images(movies, shows):
    directory = background_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for title, tmdb_id in shows + movies:
        if tmdb_id:
            bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
            overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
            traktlogo = Image.open(os.path.join(os.path.dirname(__file__), "traktlogo.png"))

            if title in [show[0] for show in shows]:
                show_data = get_tv_show_details(tmdb_id)
                media_type = "tv"
            else:
                show_data = get_movie_details(tmdb_id)
                media_type = "movie"
                
            backdrop_path = show_data.get("backdrop_path")
            if backdrop_path:
                image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    show_image = Image.open(BytesIO(image_response.content))
                    show_image = resize_image(show_image, 1500)
                    bckg.paste(show_image, (bckg.width - show_image.width, 0))
                    draw = ImageDraw.Draw(bckg)

                    # Text font
                    font_title = ImageFont.truetype(truetype_path, size=190)
                    font_overview = ImageFont.truetype(truetype_path, size=50)
                    font_custom = ImageFont.truetype(truetype_path, size=60)
                    font_info = ImageFont.truetype(truetype_path, size=50)

                    # Text color
                    shadow_color = "black"
                    main_color = "white"
                    overview_color = "white"
                    metadata_color = (150, 150, 150)

                    # Text position
                    title_position = (200, 420)
                    overview_position = (210, 730)
                    shadow_offset = 2
                    info_position = (210, 650)
                    custom_position = (210, 870)

                    #paste overlay
                    bckg.paste(overlay, (bckg.width - overlay.width, 0), overlay)

                    #paste logo and if no logo exists in english draw show title  
                    logo_path = get_logo(media_type, tmdb_id)
                    if logo_path:
                        logo_url = f"https://image.tmdb.org/t/p/original{logo_path}"
                        logo_response = requests.get(logo_url)                        
                        try:
                            if logo_response.status_code == 200:
                                logo_image = Image.open(BytesIO(logo_response.content))
                                logo_image = resize_logo(logo_image, 1000, 500)
                                logo_image = logo_image.convert("RGBA")
                                logo_position = (210, info_position[1] - logo_image.height - 25)
                                bckg.paste(logo_image, logo_position, logo_image)
                            else:
                                print(f"Error downloading logo for {title}: status code {logo_response.status_code}")
                                draw.text(title_position, title, fill="white", font=font_title)
                        except UnidentifiedImageError:
                            print(f"Error identifying logo image for {title}")
                            draw.text(title_position, title, fill="white", font=font_title)
                    else:
                        draw.text(title_position, title, fill="white", font=font_title)

                    #get metadata
                    info = ""
                    overview = ""
                    if media_type == "movie":
                        movie_details = get_movie_details(tmdb_id)
                        genres = ", ".join([genre['name'] for genre in movie_details.get('genres', [])])
                        year = movie_details.get('release_date', '')[:4]
                        duration = movie_details.get('runtime', 0)
                        hours, minutes = divmod(duration, 60)
                        overview = movie_details.get('overview')
                        tmdb_score = round(movie_details.get('vote_average', 0),1)
                        info = f"{genres}  •  {year}  •  {hours}h{minutes}min  •  TMDB: {tmdb_score}"
                    elif media_type == "tv":
                        tv_details = get_tv_show_details(tmdb_id)
                        genres = ", ".join([genre['name'] for genre in tv_details.get('genres', [])])
                        year = tv_details.get('first_air_date', '')[:4]
                        seasons = tv_details.get('number_of_seasons', 0)
                        tmdb_score = round(tv_details.get('vote_average', 0),1)
                        overview = tv_details.get('overview')
                        info = f"{genres}  •  {year}  •  {seasons} {'Season' if seasons == 1 else 'Seasons'}  •  TMDB: {tmdb_score}"

                    #draw show info
                    draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info, font=font_info, fill=shadow_color)
                    draw.multiline_text(info_position, info, font=font_info, fill=metadata_color)

                    #draw overview
                    wrapped_overview = "\n".join(textwrap.wrap(overview, width=70, max_lines=2, placeholder=" ..."))
                    overview_position = (210, info_position[1] + 70)
                    draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset), wrapped_overview, font=font_overview, fill=shadow_color)
                    draw.multiline_text(overview_position, wrapped_overview, font=font_overview, fill=overview_color)

                    #draw custom text and paste trakt logo
                    custom_text = f"Now on my {list_name} "
                    draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)
                    draw.text(custom_position, custom_text, font=font_custom, fill=overview_color)
                    bckg.paste(traktlogo, (780, 885), traktlogo)

                    #save image
                    image_path = os.path.join(directory, f"{clean_filename(title)}.jpg")
                    bckg = bckg.convert('RGB')
                    bckg.save(image_path, "JPEG")
                else:
                    print(f"Error downloading image for {title}: status code {image_response.status_code}")
            else:
                print(f"No background image found for {title}")

# Fetch movie and show lists from Trakt API
movies_list, shows_list = get_trakt_movies_and_shows(trakt_api_key, username, list_name)

# Fetch and save background images for the movies and shows
fetch_and_save_background_images(movies_list, shows_list)
