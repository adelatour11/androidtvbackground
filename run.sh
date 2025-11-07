#!/bin/sh

# Set workdir
cd /app

# copy in config files
cp -f /config/.env /config/plex.py /config/plex_color.py /config/plexfriend.py /config/plexfriend_color.py /config/jellyfin.py /config/radarrsonarr.py /config/radarrsonarr_color.py /config/TMDB.py /config/TMDB_color.py /config/trakt.py .

# Create post-processing scripts if needed
  /bin/sh /create_post_scripts.sh >> /config/log.txt 2>&1

# copies config file if needed and then run python scripts
echo "($(date)) [START] Background Retrieval"
rm -f /backgrounds/backgrounds/*
mkdir -p /backgrounds/backgrounds
if [ "$(echo "$PLEX" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Plex Backgrounds.."
  python plex.py
  mv -f plex_backgrounds/* /backgrounds/backgrounds/
  rm -rf plex_backgrounds
fi
if [ "$(echo "$PLEXCOLOR" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Plex_color Backgrounds.."
  python plex_color.py
  mv -f plex_backgrounds/* /backgrounds/backgrounds/
  rm -rf plex_backgrounds
fi
if [ "$(echo "$PLEXFRIEND" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Plex Backgrounds.."
  python plexfriend.py
  mv -f plexfriend_backgrounds/* /backgrounds/backgrounds/
  rm -rf plexfriend_backgrounds
fi
if [ "$(echo "$PLEXFRIENDCOLOR" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Plex_color Backgrounds.."
  python plexfriend_color.py
  mv -f plexfriend_backgrounds/* /backgrounds/backgrounds/
  rm -rf plexfriend_backgrounds
fi
if [ "$(echo "$JELLYFIN" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Jellyfin Backgrounds.."
  python jellyfin.py
  mv -f jellyfin_backgrounds/* /backgrounds/backgrounds/
  rm -rf jellyfin_backgrounds
fi
if [ "$(echo "$TMDB" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving TMDB Backgrounds.."
  python TMDB.py
  mv -f tmdb_backgrounds/* /backgrounds/backgrounds/
  rm -rf tmdb_backgrounds
fi
if [ "$(echo "$TMDBCOLOR" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving TMDB_color Backgrounds.."
  python TMDB_color.py
  mv -f tmdb_backgrounds/* /backgrounds/backgrounds/
  rm -rf tmdb_backgrounds
fi
if [ "$(echo "$RADARRSONARR" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving RADARRSONARR Backgrounds.."
  python radarrsonarr.py
  mv -f radarrsonarr_backgrounds/* /backgrounds/backgrounds/
  rm -rf radarrsonarr_backgrounds
fi
if [ "$(echo "$RADARRSONARRCOLOR" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving RADARRSONARR_color Backgrounds.."
  python radarrsonarr_color.py
  mv -f radarrsonarr_backgrounds/* /backgrounds/backgrounds/
  rm -rf radarrsonarr_backgrounds
fi
if [ "$(echo "$TRAKT" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Trakt Backgrounds.."
  python trakt.py
  mv -f trakt_backgrounds/* /backgrounds/backgrounds/
  rm -rf trakt_backgrounds
fi
echo "($(date)) [COMPLETED] Background Retrieval"

# Run python post script if enabled
if [ "$(echo "$POST_SCRIPT_PY" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    echo "($(date)) [START] python post_script"
    python /config/post_script.py
fi

# Run shell script if enabled
if [ "$(echo "$POST_SCRIPT_SH" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    echo "($(date)) [START] shell post_script"
    /bin/sh /config/post_script.sh
fi

# Rotate log if greater than 10Mb
LOG="/config/log.txt"
if [ -f "$LOG" ] && [ $(du -m "$LOG" | cut -f1) -gt 10 ]; then
    mv "$LOG" "$LOG.old"
fi
