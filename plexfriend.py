# plexfriends_all.py
# Fetch friends' libraries and generate backgrounds using your exact image-processing logic

# === Standard Library Imports ===
import os
import time
from datetime import datetime
import math
import random
import shutil
import textwrap
import unicodedata
from io import BytesIO

# === Third-Party Imports ===
import requests
from PIL import Image, ImageDraw, ImageFont
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

# === User Configurable Options ===
PLEX_TOKEN = os.getenv('XXXX') or 'XXXX'
TARGET_FRIEND = None  # e.g. "Alice Dupont"
order_by = 'added'      # 'aired', 'added', or 'mix'
download_movies = True
download_series = True
limit = 5
debug = False

logo_variant = 'white'
plex_logo_horizontal_offset = 0
plex_logo_vertical_offset = 7

max_summary_chars = None
max_summary_width = None

added_label = 'Now shared on'
aired_label = 'Recent release, shared on'
random_label = 'Shared on'
default_label = 'Now shared on'

env_font_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'
env_font_name = 'Roboto-Light.ttf'

main_color     = 'white'
info_color     = (150, 150, 150)
summary_color  = 'white'
metadata_color = 'white'
shadow_color   = 'black'
shadow_offset  = 2

plex_api_delay_seconds = 1.0

# Prepare output directory
background_dir = 'plex_backgrounds'
if os.path.exists(background_dir):
    shutil.rmtree(background_dir)
os.makedirs(background_dir, exist_ok=True)

# === Download Font ===
def download_font(url, path):
    try:
        if not os.path.exists(path):
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(path, 'wb') as f: f.write(r.content)
                return True
            return False
        return True
    except:
        return False

# === Discover Friend Servers ===
def get_friend_servers(token, target_friend=None):
    account = MyPlexAccount(token=token)
    friend_map = {u.id: u.title for u in account.users()}
    servers = {}
    for res in account.resources():
        if res.provides == 'server' and not res.owned:
            owner = friend_map.get(res.ownerId)
            if not owner or (target_friend and owner != target_friend):
                continue
            try:
                plex = res.connect()
                servers[owner] = plex
                print(f"[INFO] Connected to {owner}'s server: {res.name}")
            except Exception as e:
                print(f"[WARN] Could not connect to {owner}: {e}")
    return servers

# === Utilities ===
def clean_filename(name):
    return ''.join(c if c.isalnum() or c in '._-' else '_' for c in name)

def resize_image(img, h):
    ratio = h / img.height
    return img.resize((int(img.width*ratio), h))

def resize_logo(img, w, h):
    aspect = img.width / img.height
    new_w = min(w, int(h*aspect))
    new_h = int(new_w/aspect)
    return img.resize((new_w, new_h))

def truncate_summary(summary: str, max_chars: int) -> tuple[str, bool]:
    """
    Truncates a summary only if needed, at word boundaries, if it exceeds the character limit.

    Returns:
        - The summary (possibly shortened)
        - A boolean indicating whether it was truncated
    """
    summary = summary or ""

    try:
        shortened = textwrap.shorten(summary, width=max_chars, placeholder="...")
        was_truncated = shortened != summary
        return shortened, was_truncated
    except ValueError:
        # If no space to fit anything (e.g. max_chars < len(placeholder))
        return "...", True

def wrap_text_by_pixel_width(text, font, max_width, draw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        test = (cur+' '+w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def draw_text_with_shadow(draw, pos, text, font, fill, shadow, offset=(2,2)):
    x,y = pos
    draw.text((x+offset[0], y+offset[1]), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def download_logo_in_memory(item, baseurl, token):
    url = f"{baseurl}/library/metadata/{item.ratingKey}/clearLogo?X-Plex-Token={token}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
    except:
        pass
    return None

# === Core Image Processing ===
def generate_background_for_item(item, media_type, group_type,
                                 base_background, overlay, plex_logo,
                                 target_folder):
    # ensure assets
    if not (base_background and overlay and plex_logo):
        print("[ERROR] Missing background/overlay/logo")
        return

    # prepare folder
    os.makedirs(target_folder, exist_ok=True)

    # fetch art
    art_url = item.artUrl
    if not art_url: return
    try:
        r = requests.get(art_url, timeout=10); r.raise_for_status()
        art = Image.open(BytesIO(r.content))
    except:
        return



    # filename
    today = datetime.today().date().strftime('%Y-%m-%d')
    safe = unicodedata.normalize('NFKD', item.title).encode('ASCII','ignore').decode()
    safe = today + "-" + friend + "-" + clean_filename(safe)
    out_path = os.path.join(target_folder,  f"{safe}.jpg")

    # compose canvas
    canvas = base_background.copy()
    over   = overlay.copy()
    art    = resize_image(art, 1500)
    canvas.paste(art, (1175,0)); canvas.paste(over,(1175,0),over)
    draw = ImageDraw.Draw(canvas)

    # load fonts
    try:
        ft_title   = ImageFont.truetype(truetype_path, size=190)
        ft_info    = ImageFont.truetype(truetype_path, size=55)
        ft_summary = ImageFont.truetype(truetype_path, size=50)
        ft_custom  = ImageFont.truetype(truetype_path, size=60)
    except Exception as e:
        print(f"[ERROR] Font load: {e}")
        return

    # metadata text
    if media_type=='movie':
        genres = [g.tag for g in item.genres][:3]
        dur    = item.duration and f"{item.duration//3600000}h {(item.duration//60000)%60}min"
        rating = item.audienceRating or item.rating or ''
        parts  = [str(item.year)] + genres + ([dur] if dur else []) + ([item.contentRating] if item.contentRating else []) + ([f"IMDb: {rating}"] if rating else [])
    else:
        genres = [g.tag for g in item.genres][:3]
        seasons= len(item.seasons())
        parts  = [str(item.year)] + genres + ([f"{seasons} Season" if seasons==1 else f"{seasons} Seasons"]) + ([item.contentRating] if item.contentRating else []) + ([f"IMDb: {item.audienceRating or item.rating}"])
    info_text = "  •  ".join(parts)

    # draw info
    draw_text_with_shadow(draw, (210,650), info_text, ft_info, info_color, shadow_color, (shadow_offset,)*2)

    # summary: truncate then wrap
    max_chars  = max_summary_chars or 150
    max_pixels = max_summary_width or 1800
    summary, _ = truncate_summary(item.summary, max_chars)
    lines      = wrap_text_by_pixel_width(summary, ft_summary, max_pixels, draw)
    wrapped    = "\n".join(lines)
    draw_text_with_shadow(draw, (210,730), wrapped, ft_summary, summary_color, shadow_color, (shadow_offset,)*2)


    # label
    label_map = {'added':added_label + " " + friend + "'s", 'aired':aired_label, 'random':random_label}
    lbl = label_map.get(group_type, default_label)
    # position label + logo
    bbox = draw.textbbox((0,0), wrapped, font=ft_summary)
    y0  = 730 + (bbox[3]-bbox[1]) + 30
    draw_text_with_shadow(draw, (210,y0), lbl, ft_custom, metadata_color, shadow_color, (shadow_offset,)*2)
    w0 = draw.textbbox((0,0), lbl, font=ft_custom)[2]
    lx = 210 + w0 + 20 + plex_logo_horizontal_offset
    lh = plex_logo.height
    asc,des = ft_custom.getmetrics()
    ly = y0 + ((asc+des)-lh)//2 + plex_logo_vertical_offset
    canvas.paste(plex_logo,(lx,ly),plex_logo)

    # clearLogo / fallback title
    clogo = download_logo_in_memory(item, plex._baseurl, plex._token)
    if clogo:
        clogo = resize_logo(clogo,1300,400).convert('RGBA')
        canvas.paste(clogo,(210,650-clogo.height-25),clogo)
    else:
        title, _ = truncate_summary(item.title,30)
        draw_text_with_shadow(draw,(200,420),title,ft_title,main_color,shadow_color,(shadow_offset,)*2)

    # save
    canvas.convert('RGB').save(out_path)
    print(f"Saved: {out_path}")

# === Sorting Helpers ===
def sort_movies(movies,k): return sorted([m for m in movies if getattr(m,k,None)], key=lambda x:getattr(x,k), reverse=True)
def sort_shows(shows,k):
    arr=[]
    for s in shows:
        eps=[e for e in s.episodes() if getattr(e,k,None)]
        if eps: arr.append((s,max(eps,key=lambda e:getattr(e,k))))
    return [s for s,_ in sorted(arr,key=lambda t:getattr(t[1],k),reverse=True)]

# === Download Latest Media ===
def download_latest_media(plex,order,lim,typ,base_bg,over,logo,friend):
    items = plex.library.search(libtype='movie' if typ=='movie' else 'show')
    key   = 'originallyAvailableAt' if order=='aired' else 'addedAt'
    sorted_items = (sort_movies if typ=='movie' else sort_shows)(items,key)[:lim]
    odir = os.path.join(background_dir)
    for itm in sorted_items:
        generate_background_for_item(itm,typ,order,base_bg,over,logo,odir)
        time.sleep(plex_api_delay_seconds)

# === Main per-Friend ===
def main_for_friend(plex,friend):
    global truetype_path
    if download_font(env_font_url,env_font_name):
        truetype_path = env_font_name
    else:
        raise RuntimeError("Font download failed")
    BASE = os.path.dirname(__file__)
    bg   = Image.open(os.path.join(BASE,'bckg.png')).convert('RGBA')
    ov   = Image.open(os.path.join(BASE,'overlay.png')).convert('RGBA')
    logo_file = 'plexlogo_color.png' if logo_variant=='color' else 'plexlogo.png'
    plogo     = Image.open(os.path.join(BASE,logo_file)).convert('RGBA')
    if order_by=='mix':
        if download_movies: download_latest_media(plex,'added',limit,'movie',bg,ov,plogo,friend)
        if download_series: download_latest_media(plex,'aired',limit,'show',bg,ov,plogo,friend)
    else:
        if download_movies: download_latest_media(plex,order_by,limit,'movie',bg,ov,plogo,friend)
        if download_series: download_latest_media(plex,order_by,limit,'show',bg,ov,plogo,friend)

# === Entry Point ===
if __name__ == '__main__':
    servers = get_friend_servers(PLEX_TOKEN, TARGET_FRIEND)
    for friend, plex in servers.items():
        print(f"\n=== Processing {friend} ===")
        main_for_friend(plex, friend)
