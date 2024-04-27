import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import shutil
from urllib.request import urlopen
import textwrap

# Base URL for the API
url = "https://api.themoviedb.org/3/"

# Set your TMDB API Read Access Token key here
headers = {
    "accept": "application/json",
    "Authorization": "Bearer XXXX"
}
# The font used
truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'

# Endpoint for trending shows
trending_movies_url = f'{url}trending/movie/week?language=en-US'
trending_tvshows_url = f'{url}trending/tv/week?language=en-US'

# Fetching trending movies and TV shows
def fetch_trending(url):
    """Fetches trending movies or TV shows"""
    response = requests.get(url, headers=headers)
    return response.json().get('results', [])

trending_movies = fetch_trending(trending_movies_url)
trending_tvshows = fetch_trending(trending_tvshows_url)

# Fetching genres for movies and TV shows
def fetch_genres(media_type):
    """Fetches genres for movies or TV shows"""
    genres_url = f'{url}genre/{media_type}/list?language=en-US'
    response = requests.get(genres_url, headers=headers)
    return {genre['id']: genre['name'] for genre in response.json().get('genres', [])}

movie_genres = fetch_genres("movie")
tv_genres = fetch_genres("tv")

# Fetching TV show and movie details
def fetch_details(media_type, media_id):
    """Fetches details of a movie or TV show"""
    details_url = f'{url}{media_type}/{media_id}?language=en-US'
    response = requests.get(details_url, headers=headers)
    return response.json()

# Create a directory to save the backgrounds
background_dir = "tmdb_backgrounds"
# Clear the contents of the folder
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

# Resize image
def resize_image(image, height):
    """Resizes an image"""
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

# Clean filename
def clean_filename(filename):
    """Cleans a filename"""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)

# Process image
def process_image(image_url, title, is_movie, genre, year, rating, duration=None, seasons=None):
    """
    Processes and saves an image.

    Parameters:
        image_url (str): URL of the image.
        title (str): Title of the movie or TV show.
        is_movie (bool): True if the media is a movie, False if it's a TV show.
        genre (str): Genre of the movie or TV show.
        year (str): Release year of the movie or TV show.
        rating (float): Rating of the movie or TV show.
        duration (str, optional): Duration of the movie. Defaults to None.
        seasons (int, optional): Number of seasons of the TV show. Defaults to None.
    """
    response = requests.get(image_url, timeout=10)
    if response.status_code == 200:
        # Open the downloaded image
        image = Image.open(BytesIO(response.content))
        # Resize the image
        image = resize_image(image, 1500)
        # Open background, overlay, and TMDB logo images
        bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
        overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
        tmdblogo = Image.open(os.path.join(os.path.dirname(__file__), "tmdblogo.png"))
        
        # Paste the image onto the background
        bckg.paste(image, (1175, 0))
        bckg.paste(overlay, (1175, 0), overlay)
        bckg.paste(tmdblogo, (680, 975), tmdblogo)
        draw = ImageDraw.Draw(bckg)
        
        # Define fonts and colors
        font_title = ImageFont.truetype(urlopen(truetype_url), size=190)
        font_overview = ImageFont.truetype(urlopen(truetype_url), size=45)
        font_custom = ImageFont.truetype(urlopen(truetype_url), size=60)
        shadow_color = "black"
        main_color = "white"
        overview_color = (150,150,150)
        metadata_color = "white"
        shadow_offset = 2
        
        # Define text positions
        title_position = (200, 540)
        overview_position = (210, 830)
        info_position = (210, 520)
        custom_position = (210, 950)

        # Draw title
        draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title, font=font_title, fill=shadow_color)
        draw.text(title_position, title, font=font_title, fill=main_color)
        
        # Wrap overview text
        wrapped_overview = "\n".join(textwrap.wrap(overview,width= 90,initial_indent= "",subsequent_indent= "",expand_tabs= True,tabsize= 8,replace_whitespace= True,fix_sentence_endings= False,break_long_words= True,break_on_hyphens= True,drop_whitespace= True,max_lines= 2,placeholder= " ..."))
        
        # Draw overview
        draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset), wrapped_overview, font=font_overview, fill=shadow_color)
        draw.text(overview_position, wrapped_overview, font=font_overview, fill=overview_color)
        
        # Determine genre text and additional info
        genre_text = genre
        additional_info = duration if is_movie else f"{seasons} {'Season' if seasons == 1 else 'Seasons'}"
        rating_text = f"TMDB: {rating}"
        year_text = year[:7]
        info_text = f"{genre_text}  •  {year_text}  •  {additional_info}  •  {rating_text}"
        
        # Draw metadata
        draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_overview, fill=shadow_color)
        draw.text(info_position, info_text, font=font_overview, fill=overview_color)
        
        # Draw custom text
        draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), "Now Trending on", font=font_custom, fill=shadow_color)
        draw.text(custom_position, "Now Trending on", font=font_custom, fill=metadata_color)
        
        # Save the resized image
        filename = os.path.join(background_dir, f"{clean_filename(title)}.jpg")
        bckg = bckg.convert('RGB')
        bckg.save(filename)
        print(f"Image saved: {filename}")
    else:
        print(f"Failed to download background for {title}")


# Process each trending movie
for movie in trending_movies:
    # Extract movie details
    title = movie['title']
    overview = movie['overview']
    year = movie['release_date']
    rating = round(movie['vote_average'], 1)
    genre = ', '.join([movie_genres[genre_id] for genre_id in movie['genre_ids']])
    
    # Fetch additional movie details
    movie_details = fetch_details("movie", movie['id'])
    duration = movie_details.get('runtime', "N/A")
    
    # Format duration as hours and minutes
    if duration != "N/A":
        hours = duration // 60
        minutes = duration % 60
        duration = f"{hours}h{minutes}min"
        
    # Check if backdrop image is available
    backdrop_path = movie['backdrop_path']
    if backdrop_path:
        # Construct image URL
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        
        # Process the image
        process_image(image_url, title, is_movie=True, genre=genre, year=year, rating=rating, duration=duration)
    else:
        # Print error message if no backdrop image found
        print(f"No backdrop image found for {title}")

# Process trending TV shows
for tvshow in trending_tvshows:
    # Extract TV show details
    title = textwrap.shorten(tvshow['name'], width=38)
    overview = textwrap.shorten(tvshow['overview'], width=175)
    year = tvshow['first_air_date']
    rating = round(tvshow['vote_average'], 1)
    genre = ', '.join([tv_genres[genre_id] for genre_id in tvshow['genre_ids']])
    
    # Fetch additional TV show details
    tv_details = fetch_details("tv", tvshow['id'])
    seasons = tv_details.get('number_of_seasons', 0)
    
    # Check if backdrop image is available
    backdrop_path = tvshow['backdrop_path']
    if backdrop_path:
        # Construct image URL
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        
        # Process the image
        process_image(image_url, title, is_movie=False, genre=genre, year=year, rating=rating, seasons=seasons)
    else:
        # Print error message if no backdrop image found
        print(f"No backdrop image found for {title}")
