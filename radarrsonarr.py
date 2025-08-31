# TMDB background generator for Radarr and Sonarr upcoming releases

import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os, shutil, textwrap
from dotenv import load_dotenv
load_dotenv(verbose=True)

# --- CONFIGURATION ---
RADARR_URL = os.getenv('RADARR_URL')
SONARR_URL = os.getenv('SONARR_URL')
RADARR_API_KEY = os.getenv('RADARR_API_KEY')
SONARR_API_KEY = os.getenv('SONARR_API_KEY')
TMDB_BEARER_TOKEN = os.getenv('TMDB_BEARER_TOKEN')
DAYS_AHEAD = int(os.getenv('DAYS_AHEAD'))
TMDB_BASE_URL = os.getenv('TMDB_BASE_URL')
TMDB_IMG_BASE = os.getenv('TMDB_IMG_BASE')
RADARR_SONARR_LOGO = os.getenv('RADARR_SONARR_LOGO')

try:
    url = f"{RADARR_URL}/api/v3/system/status"
    resp = requests.get(url, headers={"X-Api-Key": RADARR_API_KEY})
    resp.raise_for_status()
    data = resp.json()
    print(f"Radarr: {data.get('appName')} v{data.get('version')}")
except Exception as e:
    print(f"Radarr connection failed: {e}")

try:
    url = f"{SONARR_URL}/api/v3/system/status"
    resp = requests.get(url, headers={"X-Api-Key": SONARR_API_KEY})
    resp.raise_for_status()
    data = resp.json()
    print(f"Sonarr: {data.get('appName')} v{data.get('version')}")
except Exception as e:
    print(f"Sonarr connection failed: {e}")


TMDB_HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
}


# --- UTILITIES ---
def fetch_json(url, headers=None, params=None):
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}

# Create a directory to save the backgrounds and clear its contents if it exists
background_dir = "radarrsonarr_backgrounds"
if os.path.exists(background_dir):
   shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))

# Get current date in YYYYMMDD format
date_str = datetime.now().strftime("%Y%m%d")

def clean_filename(filename):
    # Remove problematic characters from the filename
    cleaned_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return cleaned_filename

def resize_logo(image, width, height):
    aspect_ratio = image.width / image.height
    new_width = width
    new_height = int(new_width / aspect_ratio)
    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)
    return image.resize((new_width, new_height))

def truncate(text, max_chars):
    return text if len(text) <= max_chars else text[:max_chars-3] + "..."

def wrap_text(text, width=70, max_lines=2):
    return "\n".join(textwrap.wrap(text, width=width, max_lines=max_lines, placeholder=" ..."))

def resolve_tmdb_from_tvdb(tvdb_id):
    url = f"{TMDB_BASE_URL}/find/{tvdb_id}"
    params = {"external_source": "tvdb_id"}
    result = fetch_json(url, headers=TMDB_HEADERS, params=params)
    if result.get("tv_results"):
        return result["tv_results"][0]["id"]
    return None

def get_logo(media_type, media_id, language="en"):
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}/images?language={language}"
    resp = requests.get(url, headers=TMDB_HEADERS)
    if resp.status_code == 200:
        logos = resp.json().get("logos", [])
        for logo in logos:
            if logo["iso_639_1"] == "en" and logo["file_path"].endswith(".png"):
                return logo["file_path"]
    return None

def format_duration(minutes):
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h{mins:02d}min"

def process_image(image_url, title, overview, genre, year, rating, custom_text, is_movie, tmdb_id, duration=None, seasons=None):
    try:
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content))
        image = resize_image(image, 1500)

        # Base and overlays
        bckg = Image.open(os.path.join(os.path.dirname(__file__), "bckg.png"))
        overlay = Image.open(os.path.join(os.path.dirname(__file__), "overlay.png"))
        logo = Image.open(os.path.join(os.path.dirname(__file__), RADARR_SONARR_LOGO))

        bckg.paste(image, (1175, 0))
        if overlay:
            bckg.paste(overlay, (1175, 0), overlay)
        if logo:
        	if is_movie:
        		logo_position = (970, 890)  # position for movies
        	else:
        		logo_position = (1010, 890)  # position for TV shows
        	bckg.paste(logo, logo_position, logo)


        draw = ImageDraw.Draw(bckg)
        font_path = "Roboto-Light.ttf"
        if not os.path.exists(font_path):
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf"
            font_data = requests.get(font_url).content
            with open(font_path, 'wb') as f: f.write(font_data)

        font_title = ImageFont.truetype(font_path, size=90)
        font_overview = ImageFont.truetype(font_path, size=50)
        font_custom = ImageFont.truetype(font_path, size=60)

        shadow_offset = 2
        title_pos = (200, 420)
        overview_pos = (210, 730)
        info_pos = (210, 650)
        custom_pos = (210, 870)

        wrapped_overview = wrap_text(overview)
        additional = format_duration(duration) if is_movie else f"{seasons} season{'s' if seasons and seasons > 1 else ''}"
        rating_text = f"TMDB: {rating:.1f}" if rating else "TMDB: N/A"
        year_text = truncate(str(year), 7)
        info_text = f"{genre}  •  {year_text}  •  {additional}  •  {rating_text}"

        logo_drawn = False
        logo_path = get_logo("movie" if is_movie else "tv", tmdb_id, language="en")
        if logo_path:
            logo_url = f"{TMDB_IMG_BASE}{logo_path}"
            logo_resp = requests.get(logo_url)
            if logo_resp.status_code == 200:
                logo_img = Image.open(BytesIO(logo_resp.content))
                logo_img = resize_logo(logo_img, 1000, 500).convert("RGBA")
                logo_pos = (210, info_pos[1] - logo_img.height - 25)
                bckg.paste(logo_img, logo_pos, logo_img)
                logo_drawn = True

        if not logo_drawn:
            draw.text((title_pos[0] + shadow_offset, title_pos[1] + shadow_offset), title, font=font_title, fill="black")
            draw.text(title_pos, title, font=font_title, fill="white")

        draw.text((overview_pos[0] + shadow_offset, overview_pos[1] + shadow_offset), wrapped_overview, font=font_overview, fill="black")
        draw.text(overview_pos, wrapped_overview, font=font_overview, fill="white")
        draw.text((info_pos[0] + shadow_offset, info_pos[1] + shadow_offset), info_text, font=font_overview, fill="black")
        draw.text(info_pos, info_text, font=font_overview, fill=(150,150,150))
        draw.text((custom_pos[0] + shadow_offset, custom_pos[1] + shadow_offset), custom_text, font=font_custom, fill="black")
        draw.text(custom_pos, custom_text, font=font_custom, fill="white")

        filename = os.path.join(background_dir, f"{clean_filename(title)}_{date_str}.jpg")
        bckg = bckg.convert('RGB')
        bckg.save(filename)
        print(f"Generated: {filename}")

    except Exception as e:
        print(f"Image error for {title}: {e}")

# --- FETCH FROM RADARR ---
def get_radarr_upcoming():
    start = datetime.utcnow().date()
    end = start + timedelta(days=DAYS_AHEAD)
    headers = {"X-Api-Key": RADARR_API_KEY}
    url = f"{RADARR_URL}/api/v3/movie"
    movies = fetch_json(url, headers=headers)
    
    entries = []
    for movie in movies:
        if not movie.get("monitored") or movie.get("hasFile"):
            continue

        # Get release dates
        digital_date = movie.get("digitalRelease")
        physical_date = movie.get("physicalRelease")

        # Convert ISO 8601 to datetime.date if present
        def parse_iso_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ").date()
            except Exception:
                return None

        digital_dt = parse_iso_date(digital_date)
        physical_dt = parse_iso_date(physical_date)

        # Check if release is within range
        is_digital_in_range = digital_dt and start <= digital_dt <= end
        is_physical_in_range = physical_dt and start <= physical_dt <= end

        if is_digital_in_range or is_physical_in_range:
            print(f"[Radarr] Upcoming: {movie.get('title')} (TMDB {movie.get('tmdbId')}) → Digital: {digital_date} | Physical: {physical_date}")
            entries.append((movie.get("tmdbId"), True))

    return entries

# --- FETCH FROM SONARR ---
def get_sonarr_upcoming():
    start = datetime.utcnow().date()
    end = start + timedelta(days=DAYS_AHEAD)
    url = f"{SONARR_URL}/api/v3/calendar?start={start}&end={end}"
    headers = {"X-Api-Key": SONARR_API_KEY}
    episodes = fetch_json(url, headers=headers)
    print(f"[Sonarr] Episodes returned: {len(episodes)}")
    entries = set()
    for ep in episodes:
        series_id = ep.get("seriesId")
        if ep.get("monitored") and series_id:
            series_url = f"{SONARR_URL}/api/v3/series/{series_id}"
            series = fetch_json(series_url, headers=headers)
            if series.get("monitored"):
                title = series.get("title")
                tvdb_id = series.get("tvdbId")
                print(f"[Sonarr] Title: {title} | TVDB: {tvdb_id}")
                if tvdb_id:
                    tmdb_id = resolve_tmdb_from_tvdb(tvdb_id)
                    if tmdb_id:
                        print(f"[Sonarr] {title} → TVDB {tvdb_id} → TMDB {tmdb_id}")
                        entries.add((tmdb_id, False))
                    else:
                        print(f"[Sonarr] No TMDB match for {title} (TVDB ID: {tvdb_id})")
    return list(entries)


    

# --- FETCH DETAILS FROM TMDB ---
def get_tmdb_details(tmdb_id, is_movie):
    media_type = "movie" if is_movie else "tv"
    data = fetch_json(f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}", headers=TMDB_HEADERS)
    return {
        "title": data.get("title") or data.get("name"),
        "overview": data.get("overview", ""),
        "genre": ", ".join([genre['name'] for genre in data.get("genres", [])]),
        "year": (data.get("release_date") or data.get("first_air_date", ""))[:4],
        "rating": data.get("vote_average"),
        "duration": data.get("runtime"),
        "seasons": data.get("number_of_seasons"),
        "backdrop_path": data.get("backdrop_path")
    }

# --- MAIN FLOW ---
if __name__ == "__main__":
#    shutil.rmtree("tmdb_backgrounds", ignore_errors=True)
#    os.makedirs("tmdb_backgrounds", exist_ok=True)

    all_entries = get_sonarr_upcoming() + get_radarr_upcoming()
    for tmdb_id, is_movie in all_entries:
        details = get_tmdb_details(tmdb_id, is_movie)
        if details["backdrop_path"]:
            image_url = f"{TMDB_IMG_BASE}{details['backdrop_path']}"
            process_image(
                image_url=image_url,
                title=truncate(details['title'], 45),
                overview=truncate(details['overview'], 300),
                genre=details['genre'],
                year=details['year'],
                rating=details['rating'],
                custom_text="New movie coming soon on" if is_movie else "New episode coming soon on",
                is_movie=is_movie,
                tmdb_id=tmdb_id,
                duration=details['duration'] if is_movie else None,
                seasons=details['seasons'] if not is_movie else None
            )
        else:
            print(f"No backdrop for TMDB ID {tmdb_id}")
