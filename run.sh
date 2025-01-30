#!/bin/bash

# Set workdir
cd /app

# copy in config files
cp -f /config/plex.py /config/TMDB.py /config/trakt.py .

# copies config file if needed and then run python scripts
echo "($(date)) [START] Background Retrieval"
rm -f /backgrounds/backgrounds/*
mkdir -p /backgrounds/backgrounds
if [ "${PLEX,,}" == "true" ]; then
  echo "($(date)) [START] Retrieving Plex Backgrounds.."
  python plex.py
  mv -f plex_backgrounds/* /backgrounds/backgrounds/
  rm -rf plex_backgrounds
fi
if [ "${TMDB,,}" == "true" ]; then
  echo "($(date)) [START] Retrieving TMDB Backgrounds.."
  python TMDB.py
  mv -f tmdb_backgrounds/* /backgrounds/backgrounds/
  rm -rf tmdb_backgrounds
fi
if [ "${TRAKT,,}" == "true" ]; then
  echo "($(date)) [START] Retrieving Trakt Backgrounds.."
  python trakt.py
  mv -f trakt_backgrounds/* /backgrounds/backgrounds/
  rm -rf trakt_backgrounds
fi
echo "($(date)) [COMPLETED] Background Retrieval"

# Creates python script if needed and runs existing
if [ "${POST_SCRIPT_PY,,}" == "true" ]; then
  echo "($(date)) [START] python post_script"
  python /config/post_script.py
  echo "($(date)) [COMPLETED] Python post_script"
fi

# Creates shell script if needed and runs existing
if [ "${POST_SCRIPT_SH,,}" == "true" ]; then
  echo "($(date)) [START] shell post_script"
  /config/post_script.sh
  echo "($(date)) [COMPLETED] shell post_script"
fi

# Rotate log if greater than 10Mb
LOG="/config/log.txt"
if [ -f "$LOG" ] && [ $(du -m "$LOG" | cut -f1) -gt 10 ]; then
    mv "$LOG" "$LOG.old"
fi