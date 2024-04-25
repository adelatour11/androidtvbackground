import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import shutil
from urllib.request import urlopen
import textwrap

# Base URL for the API
url = "https://api.themoviedb.org/3/"

# Set your API key here
headers = {
    "accept": "application/json",
    "Authorization": "Bearer XXXXX"
}
# The font used
truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'

# Endpoint for trending shows
trending_movies_url = f'{url}trending/movie/week?language=en-US'
trending_tvshows_url = f'{url}trending/tv/week?language=en-US'

# Fetching trending movies
trending_movies_response = requests.get(trending_movies_url, headers=headers)
trending_movies = trending_movies_response.json()

# Fetching trending TV shows
trending_tvshows_response = requests.get(trending_tvshows_url, headers=headers)
trending_tvshows = trending_tvshows_response.json()

# Fetching genres for movies
genres_url = f'{url}genre/movie/list?language=en-US'
genres_response = requests.get(genres_url, headers=headers)
movie_genres = {genre['id']: genre['name'] for genre in genres_response.json()['genres']}

# Fetching genres for TV shows
genres_url = f'{url}genre/tv/list?language=en-US'
genres_response = requests.get(genres_url, headers=headers)
tv_genres = {genre['id']: genre['name'] for genre in genres_response.json()['genres']}

# Fetching TV show details
def get_tv_show_details(tv_id):
    tv_details_url = f'{url}tv/{tv_id}?language=en-US'
    tv_details_response = requests.get(tv_details_url, headers=headers)
    return tv_details_response.json()

# Fetching movie details
def get_movie_details(movie_id):
    movie_details_url = f'{url}movie/{movie_id}?language=en-US'
    movie_details_response = requests.get(movie_details_url, headers=headers)
    return movie_details_response.json()


# Create a directory to save the backgrounds
background_dir = "tmdb_backgrounds"
# Clear the contents of the folder
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

#truncate overview
def truncate_overview(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars-3] + "..."
    else:
        return overview

#truncate
def truncate(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars-3]
    else:
        return overview

# resize image
def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename

def process_image(image_url, title, is_movie, genre, year, rating, duration=None, seasons=None):
    # Download the background image with a timeout of 10 seconds
    response = requests.get(image_url, timeout=10)
    if response.status_code == 200:
        # Open the image
        image = Image.open(BytesIO(response.content))

        # Resize the image to have a width of 1500 pixels while preserving aspect ratio
        image = resize_image(image, 1500)

        # Open overlay images
        bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
        overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
        tmdblogo = Image.open(os.path.join(os.path.dirname(__file__), "tmdblogo.png"))


        # Paste images
        bckg.paste(image, (1175, 0))
        bckg.paste(overlay, (1175, 0), overlay)
        bckg.paste(tmdblogo, (680, 975), tmdblogo)

        # Add title text with shadow
        draw = ImageDraw.Draw(bckg)

        #Text font
        font_title = ImageFont.truetype(urlopen(truetype_url), size=190)
        font_overview = ImageFont.truetype(urlopen(truetype_url), size=45)
        font_custom = ImageFont.truetype(urlopen(truetype_url), size=60)                 

        #Text color
        shadow_color = "black"
        main_color = "white"
        overview_color = (150,150,150)  # Grey color for the summary
        metadata_color = "white"

        #Text position
        title_position = (200, 540)
        overview_position = (210, 830)
        shadow_offset = 2
        info_position = (210, 520)
        custom_position = (210, 950)

        # Draw Title for info
        draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title, font=font_title, fill=shadow_color)
        draw.text(title_position, title, font=font_title, fill=main_color)

        # Wrap Overview text
        wrapped_overview = "\n".join(textwrap.wrap(overview, width=90))

        # Draw Overview for info
        draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset), wrapped_overview, font=font_overview, fill=shadow_color)
        draw.text(overview_position, wrapped_overview, font=font_overview, fill=overview_color)

        # Determine genre text and additional info
        if is_movie:
            genre_text = genre
            additional_info = f"{duration}"
        else:
            genre_text = genre
            additional_info = f"{seasons} {'Season' if seasons == 1 else 'Seasons'}"

        rating_text = "TMDB: "+ str(rating)
        year_text = truncate(str(year),7) 
        info_text = f"{genre_text}  •  {year_text}  •  {additional_info}  •  {rating_text}"

        # Draw metadata
        draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_overview, fill=shadow_color)
        draw.text(info_position, info_text, font=font_overview, fill=overview_color)

        # Draw custom text
        draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)                  
        draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)

        # Save the resized image
        filename = os.path.join(background_dir, f"{clean_filename(title)}.jpg")
        bckg = bckg.convert('RGB')
        bckg.save(filename)
        print(f"Image saved: {filename}")
    else:
        print(f"Failed to download background for {title}")

# Process each trending movie
for movie in trending_movies.get('results', []):
    title = movie['title']
    overview = truncate_overview(movie['overview'],175)
    year = movie['release_date']
    rating = round(movie['vote_average'],1)
    genre = ', '.join([movie_genres[genre_id] for genre_id in movie['genre_ids']])


    movie_details = get_movie_details(movie['id'])
    duration = movie_details.get('runtime', 0)
    if duration:
        hours = duration // 60
        minutes = duration % 60
        duration = f"{hours}h{minutes}min"
    else:
        duration = "N/A"

    backdrop_path = movie['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=True, genre=genre, year=year, rating=rating, duration=duration)
    else:
        print(f"No backdrop image found for {title}")

# Process trending TV shows
for tvshow in trending_tvshows.get('results', []):
    title = truncate_overview(tvshow['name'],38)
    overview = truncate_overview(tvshow['overview'],175)
    year = tvshow['first_air_date']
    rating = round(tvshow['vote_average'],1)
    genre = ', '.join([tv_genres[genre_id] for genre_id in tvshow['genre_ids']])
    tv_details = get_tv_show_details(tvshow['id'])
    seasons = tv_details.get('number_of_seasons', 0)
    backdrop_path = tvshow['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=False, genre=genre, year=year, rating=rating, seasons=seasons)
    else:
        print(f"No backdrop image found for {title}")