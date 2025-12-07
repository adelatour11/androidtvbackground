# TMDB background generator using a colored background and vignetting effect
import requests
import numpy as np
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
import shutil
import textwrap
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv(verbose=True)

TMDB_BEARER_TOKEN = os.getenv('TMDB_BEARER_TOKEN')
TMDB_BASE_URL = os.getenv('TMDB_BASE_URL')
LANGUAGE = os.getenv("TMDB_LANGUAGE", "en-US")

# Set your TMDB API Read Access Token key here
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
}


# Get current date in YYYYMMDD formaat
date_str = datetime.now().strftime("%Y%m%d")

# Set the number of movies and tvshwos to get
numberofmovies = 5
numberoftvshows = 5

# TV Exclusion list - this filter will exclude TV shows from chosen countries that have a specific genre
tv_excluded_countries = ['XX', 'XX', 'XX', 'XX', 'XX', 'XX']  # ISO 3166-1 alpha-2 codes lowercas, jp, kr, us for Japan, Korea, and the US
tv_excluded_genres = {
    'XX': ['XXXX', 'XXXX', 'XXXX'],  # Exclude Animation and Drama from Japan
    'XX': ['XXXX', 'XXX', 'XXXX', 'XXXX'],  # Exclude Animation and Drama from Korea
    'XX': ['XXXX','XXXX'],           # Exclude Animation from the US
    'XX': ['*'],
    'XX': ['*'],
    'X': ['*']
}

# Movie Exclusion list - this filter will exclude movies from chosen countries that have a specific genre
movie_excluded_countries = ['XX', 'XX', 'XX', 'XX', 'XX', 'XX']  # ISO 3166-1 alpha-2 codes lowercas, jp, kr, us for Japan, Korea, and the US
movie_excluded_genres = {
    'XX': ['XX'],  # Exclude Animation and Drama from Japan
    'kr': ['XX'],  # Exclude Animation and Drama from Korea
    'XX': ['XX'],  # Exclude Animation and Drama from US
    'XX': ['*'],
    'XX': ['*'],
    'XX': ['*']
}

# Keyword exclusion list - this filter will exclude movies or TV shows that contain a specific keyword in their TMDB profile
excluded_keywords = ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX','XX']  # like ['adult']

# Filter movies by release date and TV shows by last air date
max_air_date = datetime.now() - timedelta(days=90)  # specify the number of days since the movie release or the TV show last air date, shows before this date will be excluded

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




# Fetching genres for movies
genres_url = f'{TMDB_BASE_URL}/genre/movie/list?language={LANGUAGE}'
genres_response = requests.get(genres_url, headers=headers)
genres_data = genres_response.json()
movie_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}

# Fetching genres for TV shows
genres_url = f'{TMDB_BASE_URL}/genre/tv/list?language={LANGUAGE}'
genres_response = requests.get(genres_url, headers=headers)
genres_data = genres_response.json()
tv_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}

# Fetching TV show details
def get_tv_show_details(tv_id):
    tv_details_url = f'{TMDB_BASE_URL}/tv/{tv_id}?language={LANGUAGE}'
    tv_details_response = requests.get(tv_details_url, headers=headers)
    return tv_details_response.json()

# Fetching movie details
def get_movie_details(movie_id):
    movie_details_url = f'{TMDB_BASE_URL}/movie/{movie_id}?language={LANGUAGE}'
    movie_details_response = requests.get(movie_details_url, headers=headers)
    return movie_details_response.json()

# Function to fetch keywords for a movie
def get_movie_keywords(movie_id):
    keywords_url = f"{TMDB_BASE_URL}/movie/{movie_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        # Extract and return the names of the keywords
        return [keyword['name'].lower() for keyword in response.json().get('keywords', [])]
    return []

# Function to fetch keywords for a TV show
def get_tv_keywords(tv_id):
    keywords_url = f"{TMDB_BASE_URL}tv/{tv_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        return [keyword['name'].lower() for keyword in response.json().get('results', [])]
    return []



# Filter criteria for movies
def should_exclude_movie(movie, movie_excluded_countries=movie_excluded_countries, movie_excluded_genres=movie_excluded_genres, excluded_keywords=excluded_keywords):
    # Check if the movie's country is in the excluded countries list
    origin_countries = [c.lower() for c in movie.get('origin_country', [])]
    genres = [movie_genres.get(genre_id, '') for genre_id in movie.get('genre_ids', [])]
    
    # Fetch movie keywords
    movie_keywords = get_movie_keywords(movie['id']) if excluded_keywords else []
    
    # Check release date
    release_date_str = movie.get('release_date')
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d") if release_date_str else None
    
    # Exclusion logic by country and genre
    for country in origin_countries:
        if country in movie_excluded_countries:
            excluded = movie_excluded_genres.get(country, [])
            if excluded == ['*'] or any(genre in excluded for genre in genres):
                return True
    
    # Exclusion by keyword or date
    if any(keyword in movie_keywords for keyword in excluded_keywords):
        return True
    
    if release_date and release_date < max_air_date:
        return True
    
    return False


# Filter criteria for TV shows
def should_exclude_tvshow(tvshow, tv_excluded_countries=tv_excluded_countries, tv_excluded_genres=tv_excluded_genres, excluded_keywords=excluded_keywords):
    # Ensure 'origin_country' is a list or string and get the country (case insensitive)
    origin_countries = [c.lower() for c in tvshow.get('origin_country', [])]
    genres = [tv_genres.get(genre_id, '') for genre_id in tvshow.get('genre_ids', [])]

    for country in origin_countries:
        if country in tv_excluded_countries:
            excluded = tv_excluded_genres.get(country, [])
            if excluded == ['*'] or any(genre in excluded for genre in genres):
                return True

    # Fetch TV show keywords and check against the exclusion list
    tv_keywords = get_tv_keywords(tvshow['id']) if excluded_keywords else []
    if any(keyword in tv_keywords for keyword in excluded_keywords):
        return True

    # Check last air date
    last_air_date_str = get_tv_show_details(tvshow['id']).get('last_air_date')
    if last_air_date_str:
        try:
            last_air_date = datetime.strptime(last_air_date_str, "%Y-%m-%d")
        except ValueError:
            last_air_date = None
    else:
        last_air_date = None

    # Exclude if older than max_air_date
    if last_air_date and last_air_date < max_air_date:
        return True

    # Include future shows
    if last_air_date and last_air_date > datetime.now():
        return False

    return False

# Endpoint for trending shows
trending_movies_url = f'{TMDB_BASE_URL}/trending/movie/week?language={LANGUAGE}'
trending_tvshows_url = f'{TMDB_BASE_URL}/trending/tv/week?language={LANGUAGE}'

# Fetch more than required to allow filtering
initial_fetch_count = numberofmovies + 10  # Fetch 15 to get at least 5 valid ones
trending_movies_url = f'{TMDB_BASE_URL}/trending/movie/week?language={LANGUAGE}'
trending_movies_response = requests.get(trending_movies_url, headers=headers)
all_movies = trending_movies_response.json().get('results', [])[:initial_fetch_count]

# Filter manually
valid_movies = []
for movie in all_movies:
    if not should_exclude_movie(movie):
        valid_movies.append(movie)
    else:
        print(f"Excluded Movie: {movie['title']} ({movie.get('origin_country')})")
    
    if len(valid_movies) >= numberofmovies:
        break

trending_movies = {'results': valid_movies}


# Fetching trending TV shows
initial_fetch_count = numberoftvshows + 10  # Fetch more than needed
trending_tvshows_url = f'{TMDB_BASE_URL}/trending/tv/week?language={LANGUAGE}'
trending_tvshows_response = requests.get(trending_tvshows_url, headers=headers)
all_tvshows = trending_tvshows_response.json().get('results', [])[:initial_fetch_count]

# Filter manually
valid_tvshows = []
for tvshow in all_tvshows:
    if not should_exclude_tvshow(tvshow):
        valid_tvshows.append(tvshow)
    if len(valid_tvshows) >= numberoftvshows:
        break
trending_tvshows = {'results': valid_tvshows}

# Create a directory to save the backgrounds and clear its contents if it exists

background_dir = "tmdb_backgrounds"
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)


# Truncate overview
def truncate_overview(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars]
    else:
        return overview

# Truncate
def truncate(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars-3]
    else:
        return overview

# Resize image
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





def vignette_side(h, w, fade_ratio=5, fade_power=5.0, position="bottom-left", offset_left=0, offset_bottom=0):
    """
    Create a vignette mask for the given position.
    offset_left / offset_bottom allow shifting the start of the fade inward in pixels.
    """
    y, x = np.ogrid[0:h, 0:w]
    rx, ry = w * fade_ratio, h * fade_ratio

    dist_x, dist_y = np.ones_like(x, dtype=np.float32), np.ones_like(y, dtype=np.float32)

    if "left" in position:
        dist_x = np.clip((x - offset_left) / rx, 0, 1)
    elif "right" in position:
        dist_x = np.clip((w - x) / rx, 0, 1)

    if "top" in position:
        dist_y = np.clip(y / ry, 0, 1)
    elif "bottom" in position:
        dist_y = np.clip((h - y - offset_bottom) / ry, 0, 1)

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

    # Add dithering noise
    noise = np.random.uniform(-dither_strength, dither_strength, bg_array.shape)
    bg_array = np.clip(bg_array + noise, 0, 255).astype(np.uint8)
    bg_img = Image.fromarray(bg_array)

    # Detect uniformity
    gray = np.array(bg_img.convert("L"))
    is_uniform = gray.std() < 15  # threshold for "too uniform"

    if is_uniform:
        print("[Background] Detected uniform image, will soften vignette.")
    
    return bg_img, is_uniform

def generate_background_fast(input_img, target_width=3000):
    # Step 1: Create blurry/dark canvas
    canvas_rgb, is_uniform = create_blurry_background(input_img, size=(3840, 2160), blur_radius=800)

    canvas_array = np.array(canvas_rgb).astype(np.float32)
    canvas_array = (canvas_array * 0.4).clip(0, 255).astype(np.uint8)  # darken
    canvas_rgb = Image.fromarray(canvas_array)

    canvas = Image.new("RGBA", canvas_rgb.size, (0, 0, 0, 255))
    canvas.paste(canvas_rgb, (0, 0))

    # Step 2: Resize input to target width
    w_percent = target_width / input_img.width
    new_size = (target_width, int(input_img.height * w_percent))
    img_resized = input_img.resize(new_size, Image.LANCZOS).convert("RGBA")

    # Step 3: Apply vignette
    h, w = img_resized.height, img_resized.width
    mask = vignette_side(
        h, w,
        fade_ratio=0.3,
        fade_power=2.5,
        position="bottom-left",
        offset_left=0,
        offset_bottom=150
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=60))

    img_resized.putalpha(mask)

    # Step 4: Paste top-right
    canvas.paste(img_resized, (3840 - w, 0), img_resized)

    return canvas.convert("RGB")


def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename


# Fetch movie or TV show logo in English
def get_logo(media_type, media_id, language):
    # Prepare language code (fr-FR -> fr)
    lang_code = language.split("-")[0]

    # Build TMDB API URL
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}/images?language={LANGUAGE}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    logos = response.json().get("logos", [])

    # If no logos at all, try English fallback
    if not logos:
        url_en = f"{TMDB_BASE_URL}/{media_type}/{media_id}/images?language=en"
        response_en = requests.get(url_en, headers=headers)
        if response_en.status_code == 200:
            logos_en = response_en.json().get("logos", [])
            if logos_en:
                return sorted(logos_en, key=lambda x: x.get("vote_average", 0), reverse=True)[0]["file_path"]
        return None

    # 1. Exact match for requested language
    lang_match = [l for l in logos if l.get("iso_639_1") == LANGUAGE]
    if lang_match:
        # Pick highest rated
        return sorted(lang_match, key=lambda x: x.get("vote_average", 0), reverse=True)[0]["file_path"]

    # 4. Last fallback: best-rated logo overall
    return sorted(logos, key=lambda x: x.get("vote_average", 0), reverse=True)[0]["file_path"]


def process_image(image_url, title, is_movie, genre, year, rating, duration=None, seasons=None):
    response = requests.get(image_url, timeout=10)
    if response.status_code == 200:
        input_img = Image.open(BytesIO(response.content))

        # Generate blurred/vignette background instead of static overlay
        bckg = generate_background_fast(input_img, target_width=3000)


        draw = ImageDraw.Draw(bckg)

        tmdblogo = Image.open(os.path.join(os.path.dirname(__file__), "tmdblogo.png"))

        # Fonts
        font_title = ImageFont.truetype(truetype_path, size=190)
        font_overview = ImageFont.truetype(truetype_path, size=50)
        font_custom = ImageFont.truetype(truetype_path, size=60)

        shadow_color = "black"
        main_color = "white"
        overview_color = "white"
        metadata_color = "white"

        title_position = (200, 420)
        overview_position = (210, 730)
        shadow_offset = 2
        info_position = (210, 650)

        # Wrap overview
        wrapped_overview = "\n".join(textwrap.wrap(overview, width=65, max_lines=3, placeholder=" ..."))
        lines = wrapped_overview.split("\n")

        # Compute height of one line using getbbox
        bbox = font_overview.getbbox("A")  # (left, top, right, bottom)
        line_height = bbox[3] - bbox[1]

        # Total height of wrapped summary
        summary_height = line_height * len(lines)

        custom_position =  (210, overview_position[1] + summary_height + 100)


        # Overview
        draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset),
                  wrapped_overview, font=font_overview, fill=shadow_color)
        draw.text(overview_position, wrapped_overview, font=font_overview, fill=overview_color)

        # Metadata
        if is_movie:
            genre_text = genre
            additional_info = f"{duration}"
        else:
            genre_text = genre
            additional_info = f"{seasons} {'Season' if seasons == 1 else 'Seasons'}"

        rating_text = "TMDB: " + str(rating)
        year_text = truncate(str(year), 7)
        info_text = f"{genre_text}  •  {year_text}  •  {additional_info}  •  {rating_text}"

        draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset),
                  info_text, font=font_overview, fill=shadow_color)
        draw.text(info_position, info_text, font=font_overview, fill=overview_color)

        # Logo (same as your old code)
        if is_movie:
            logo_path = get_logo("movie", movie['id'], language="en")
        else:
            logo_path = get_logo("tv", tvshow['id'], language="en")

        logo_drawn = False
        if logo_path:
            logo_url = f"https://image.tmdb.org/t/p/original{logo_path}"
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                try:
                    logo_image = Image.open(BytesIO(logo_response.content))
                    logo_image = resize_logo(logo_image, 1000, 500)
                    logo_position = (210, info_position[1] - logo_image.height - 25)
                    logo_image = logo_image.convert('RGBA')
                    bckg.paste(logo_image, logo_position, logo_image)
                    logo_drawn = True
                except Exception as e:
                    print(f"Failed to draw logo for {title}: {e}")

        if not logo_drawn:
            draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset),
                      title, font=font_title, fill=shadow_color)
            draw.text(title_position, title, font=font_title, fill=main_color)

        # Custom text
        draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset),
                  custom_text, font=font_custom, fill=shadow_color)
        draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)

        bckg.paste(tmdblogo, (680, custom_position[1] + 20), tmdblogo)

        # Save
        filename = os.path.join(background_dir, f"{clean_filename(title)}.jpg")
        bckg = bckg.convert('RGB')
        bckg.save(filename)
        print(f"Image saved: {filename}")
    else:
        print(f"Failed to download background for {title}")


# Process each trending movie
for movie in trending_movies.get('results', []):
    if should_exclude_movie(movie):
        print(f"Excluded Movie: {movie['title']} ({movie.get('origin_country')})")
        continue

    # Extract movie details
    title = movie['title']
    overview = movie['overview']
    year = movie['release_date']
    rating = round(movie['vote_average'], 1)
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
        print(f"Excluded TV Show: {tvshow['name']} ({tvshow.get('origin_country')})")
        continue

    # Extract TV show details
    title = truncate_overview(tvshow['name'], 38)
    overview = tvshow['overview']
    year = tvshow['first_air_date']
    rating = round(tvshow['vote_average'], 1)
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
