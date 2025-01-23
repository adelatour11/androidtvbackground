import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
import shutil
from urllib.request import urlopen
import textwrap
from datetime import datetime, timedelta

# Base URL for the API
url = "https://api.themoviedb.org/3/"

# Set your TMDB API Read Access Token key here
headers = {
    "accept": "application/json",
    "Authorization": "Bearer XXXXX"
}

# TV Exclusion list - this filter will exclude Tv shows from chosen countries that have a specific genre
tv_excluded_countries=['XX','XX','XX'] #based on ISO 3166-1 alpha-2 codes, enter lowercase like ['cn','kr','jp','fr','us']
tv_excluded_genres=['XXXX'] # like ['Animation']

# Movie Exclusion list - this filter will exclude movies from chosen countries that have a specific genre
movie_excluded_countries=['XX','XX','XXX'] #based on ISO 3166-1 alpha-2 codes, enter lowercase like ['cn','kr','jp','fr','us']
movie_excluded_genres=['XXX'] # like ['Animation']

# Keyword exclusion list - this filter will exclude movies or tv shows that contain a specific keyword in their TMDB profile
excluded_keywords = ['XXX','XXX','XXX'] # like ['adult']

# Directory to save the backgrounds
background_dir = "tmdb_backgrounds"

# Filter movies by release date and tv shows by last air date
max_air_date = datetime.now() - timedelta(days=30) #specify the number of days since the movei release or the tv show last air date, shows before this date will be excluded 

# Save font locally
truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'
truetype_path = '/Roboto-Light.ttf'
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
genres_data = genres_response.json()
movie_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}

# Fetching genres for TV shows
genres_url = f'{url}genre/tv/list?language=en-US'
genres_response = requests.get(genres_url, headers=headers)
genres_data = genres_response.json()
tv_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}

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

# Function to fetch keywords for a movie
def get_movie_keywords(movie_id):
    keywords_url = f"{url}movie/{movie_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        # Extract and return the names of the keywords
        return [keyword['name'].lower() for keyword in response.json().get('keywords', [])]
    return []

# Function to fetch keywords for a TV show
def get_tv_keywords(tv_id):
    keywords_url = f"{url}tv/{tv_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        return [keyword['name'].lower() for keyword in response.json().get('results', [])]
    return []

# Clear the contents of the folder
shutil.rmtree(background_dir)  
os.makedirs(background_dir, exist_ok=True)

#truncate overview
def truncate_overview(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars]
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

def resize_logo(image, width, height):
    # Get the aspect ratio of the image
    aspect_ratio = image.width / image.height
    
    # Calculate new width and height to maintain aspect ratio
    new_width = width
    new_height = int(new_width / aspect_ratio)
    
    # If the calculated height is greater than the desired height,
    # recalculate the width to fit the desired height
    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)
    
    # Resize the image
    resized_img = image.resize((new_width, new_height))
    return resized_img

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename

# Fetch movie or TV show logo in English
def get_logo(media_type, media_id, language="en"):
    logo_url = f"{url}{media_type}/{media_id}/images?language={language}"
    logo_response = requests.get(logo_url, headers=headers)
    logo_data = logo_response.json()
    if logo_response.status_code == 200:
        logos = logo_response.json().get("logos", [])
        for logo in logos:
            if logo["iso_639_1"] == "en" and logo["file_path"].endswith(".png"):
                return logo["file_path"]
    return None

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
        bckg.paste(tmdblogo, (680, 890), tmdblogo)

        # Add title text with shadow
        draw = ImageDraw.Draw(bckg)

        # Text font
        font_title = ImageFont.truetype(urlopen(truetype_url), size=190)
        font_overview = ImageFont.truetype(urlopen(truetype_url), size=50)
        font_custom = ImageFont.truetype(urlopen(truetype_url), size=60)

        # Text color
        shadow_color = "black"
        main_color = "white"
        overview_color = (150, 150, 150)  # Grey color for the summary
        metadata_color = "white"

        # Text position
        title_position = (200, 420)
        overview_position = (210, 730)
        shadow_offset = 2
        info_position = (210, 650)  # Adjusted position for logo and info
        custom_position = (210, 870)

        # Wrap overview text
        wrapped_overview = "\n".join(textwrap.wrap(overview, width=70, max_lines=2, placeholder=" ..."))

        # Draw Overview for info
        draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset), wrapped_overview, font=font_overview, fill=shadow_color)
        draw.text(overview_position, wrapped_overview, font=font_overview, fill=metadata_color)

        # Determine genre text and additional info
        if is_movie:
            genre_text = genre
            additional_info = f"{duration}"
        else:
            genre_text = genre
            additional_info = f"{seasons} {'Season' if seasons == 1 else 'Seasons'}"

        rating_text = "TMDB: " + str(rating)
        year_text = truncate(str(year), 7)
        info_text = f"{genre_text}  \u2022  {year_text}  \u2022  {additional_info}  \u2022  {rating_text}"

        # Draw metadata
        draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_overview, fill=shadow_color)
        draw.text(info_position, info_text, font=font_overview, fill=overview_color)

        # Get logo image URL
        if is_movie:
            logo_path = get_logo("movie", movie['id'], language="en")
        else:
            logo_path = get_logo("tv", tvshow['id'], language="en")

        logo_drawn = False  # Flag to track if logo is drawn

        if logo_path:
            logo_url = f"https://image.tmdb.org/t/p/original{logo_path}"
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                try:
                    logo_image = Image.open(BytesIO(logo_response.content))
                    # Resize the logo image to fit within a box while maintaining aspect ratio
                    logo_image = resize_logo(logo_image, 1000, 500)
                    logo_position = (210, info_position[1] - logo_image.height - 25)  # Position for logo
                    logo_image = logo_image.convert('RGBA')

                    # Paste the logo onto the image
                    bckg.paste(logo_image, logo_position, logo_image)
                    logo_drawn = True  # Logo was successfully drawn
                except Exception as e:
                    print(f"Failed to draw logo for {title}: {e}")

        if not logo_drawn:
            # Draw title text if logo is not available or failed to draw
            draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title, font=font_title, fill=shadow_color)
            draw.text(title_position, title, font=font_title, fill=main_color)

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

# Filter criteria
def should_exclude_movie(movie, movie_excluded_countries=movie_excluded_countries, movie_excluded_genres=movie_excluded_genres, excluded_keywords=excluded_keywords):
    # Check if the movie's country is in the excluded countries list
    country = movie.get('origin_country', '').lower()
    
    # Check if any genre in the movie matches the excluded genres list
    genres = [movie_genres.get(genre_id, '') for genre_id in movie.get('genre_ids', [])]
    
    # Fetch movie keywords
    movie_keywords = get_movie_keywords(movie['id']) if excluded_keywords else []
    
    # Check release date
    release_date_str = movie.get('release_date')
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d") if release_date_str else None

    # Return True if excluded by country, genre, keywords, or release date
    if (country in movie_excluded_countries or 
        any(genre in movie_excluded_genres for genre in genres) or 
        any(keyword in movie_keywords for keyword in excluded_keywords) or
        (release_date and release_date < max_air_date)):
        return True
    return False

def should_exclude_tvshow(tvshow, tv_excluded_countries=tv_excluded_countries, tv_excluded_genres=tv_excluded_genres, excluded_keywords=excluded_keywords):
    # Check if the TV show's country is in the excluded countries list
    country = tvshow.get('origin_country', [''])[0].lower()
    
    # Check if any genre in the TV show matches the excluded genres list
    genres = [tv_genres.get(genre_id, '') for genre_id in tvshow.get('genre_ids', [])]
    
    # Fetch TV show keywords
    tv_keywords = get_tv_keywords(tvshow['id']) if excluded_keywords else []
    
    # Check next episode to air date
    last_air_date_str = get_tv_show_details(tvshow['id']).get('last_air_date')
    last_air_date = datetime.strptime(last_air_date_str, "%Y-%m-%d") if last_air_date_str else None

    # Return True if excluded by country, genre, keywords, or next episode air date
    if (country in tv_excluded_countries or 
        any(genre in tv_excluded_genres for genre in genres) or 
        any(keyword in tv_keywords for keyword in excluded_keywords) or
        (last_air_date and last_air_date < max_air_date)):
        return True
    return False


# Process each trending movie
for movie in trending_movies.get('results', []):
    if should_exclude_movie(movie):
        continue
    
    # Extract movie details
    title = movie['title']
    overview = movie['overview']
    year = movie['release_date']
    rating = round(movie['vote_average'],1)
    genre = ', '.join([movie_genres[genre_id] for genre_id in movie['genre_ids']])
    
    # Fetch additional movie details
    movie_details = get_movie_details(movie['id'])
    duration = movie_details.get('runtime', 0)
    
    # Format duration as hours and minutes
    if duration:
        hours = duration // 60
        minutes = duration % 60
        duration = f"{hours}h{minutes}min"
    else:
        duration = "N/A"

    # Check if backdrop image is available
    backdrop_path = movie['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        # Construct image URL
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        # Process the image
        process_image(image_url, title, is_movie=True, genre=genre, year=year, rating=rating, duration=duration)
    else:
        # Print error message if no backdrop image found
        print(f"No backdrop image found for {title}")



# Process trending TV shows
for tvshow in trending_tvshows.get('results', []):
    if should_exclude_tvshow(tvshow):
        continue

    # Extract TV show details
    title = truncate_overview(tvshow['name'],38)
    overview = tvshow['overview']
    year = tvshow['first_air_date']
    rating = round(tvshow['vote_average'],1)
    genre = ', '.join([tv_genres[genre_id] for genre_id in tvshow['genre_ids']])
    
    # Fetch additional TV show details
    tv_details = get_tv_show_details(tvshow['id'])
    seasons = tv_details.get('number_of_seasons', 0)
    
    # Check if backdrop image is available
    backdrop_path = tvshow['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        # Construct image URL
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        
        # Process the image
        process_image(image_url, title, is_movie=False, genre=genre, year=year, rating=rating, seasons=seasons)
    else:
        # Print error message if no backdrop image found
        print(f"No backdrop image found for {title}")
