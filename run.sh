#!/bin/sh

# Set workdir
cd /app

# copy in config files
cp -f /config/plex.py /config/jellyfin.py /config/TMDB.py /config/trakt.py .

# Creates python script if needed
if [ "$(echo "$POST_SCRIPT_PY" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  if [ ! -f /config/post_script.py ]; then
    echo "($(date)) Creating post_script.py script"
    cat << 'EOF' > /config/post_script.py
#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

log_file = "/config/log.txt"
src_dir = "/config/backgrounds"
dest_dir = "/config/tvbackgrounds"

def log(msg):
    timestamp = datetime.now().strftime("(%Y-%m-%d %H:%M:%S)")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} {msg}\n")

def main():
    if not os.path.isdir(dest_dir):
        # Destination missing: silently skip
        return

    if not os.access(dest_dir, os.W_OK):
        log(f"[ERROR] Destination directory {dest_dir} is not writable.")
        return

    if os.path.isdir(src_dir) and any(os.scandir(src_dir)):
        log(f"Found files in {src_dir}, updating {dest_dir}...")

        try:
            for entry in os.scandir(dest_dir):
                path = entry.path
                if entry.is_file() or entry.is_symlink():
                    os.unlink(path)
                elif entry.is_dir():
                    shutil.rmtree(path)
            log(f"Cleared old files in {dest_dir}.")
        except Exception as e:
            log(f"[ERROR] Failed to clear files in {dest_dir}: {e}")

        try:
            for entry in os.scandir(src_dir):
                shutil.move(entry.path, dest_dir)
            log(f"Moved new files to {dest_dir}.")
        except Exception as e:
            log(f"[ERROR] Failed to move files from {src_dir} to {dest_dir}: {e}")
    else:
        log(f"No files found in {src_dir}, skipping update.")

if __name__ == "__main__":
    main()
    log("[COMPLETED] python post_script")
EOF
  fi
fi

# Creates shell script if needed
if [ "$(echo "$POST_SCRIPT_SH" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  if [ ! -f /config/post_script.sh ]; then
    echo "($(date)) Creating post_script.sh script"
    cat << 'EOF' > /config/post_script.sh
#!/bin/bash

LOG_FILE="/config/log.txt"
SRC_DIR="/config/backgrounds"
DEST_DIR="/config/tvbackgrounds"

if [ ! -d "$DEST_DIR" ]; then
    # Destination folder missing: silently skip moving files
else
    if [ ! -w "$DEST_DIR" ]; then
        echo "($(date)) [ERROR] Destination directory $DEST_DIR is not writable." >> "$LOG_FILE"
    else
        if [ -d "$SRC_DIR" ] && [ "$(find "$SRC_DIR" -mindepth 1 -print -quit)" ]; then
            echo "($(date)) Found files in $SRC_DIR, updating $DEST_DIR..." >> "$LOG_FILE"

            find "$DEST_DIR" -mindepth 1 -exec rm -rf -- {} + && \
            echo "($(date)) Cleared old files in $DEST_DIR." >> "$LOG_FILE" || \
            echo "($(date)) [ERROR] Failed to clear files in $DEST_DIR." >> "$LOG_FILE"

            find "$SRC_DIR" -mindepth 1 -exec mv -t "$DEST_DIR" -- {} + && \
            echo "($(date)) Moved new files to $DEST_DIR." >> "$LOG_FILE" || \
            echo "($(date)) [ERROR] Failed to move files from $SRC_DIR to $DEST_DIR." >> "$LOG_FILE"
        else
            echo "($(date)) No files found in $SRC_DIR, skipping update." >> "$LOG_FILE"
        fi
    fi
fi

echo "($(date)) [COMPLETED] shell post_script" >> "$LOG_FILE"
EOF
    chmod +x /config/post_script.sh
  fi
fi

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
if [ "$(echo "$TRAKT" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  echo "($(date)) [START] Retrieving Trakt Backgrounds.."
  python trakt.py
  mv -f trakt_backgrounds/* /backgrounds/backgrounds/
  rm -rf trakt_backgrounds
fi
echo "($(date)) [COMPLETED] Background Retrieval"

# Creates python script if needed and runs existing
if [ "$(echo "$POST_SCRIPT_PY" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    echo "($(date)) [START] python post_script"
    python /config/post_script.py
fi

# Creates shell script if needed and runs existing
if [ "$(echo "$POST_SCRIPT_SH" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    echo "($(date)) [START] shell post_script"
    /bin/sh /config/post_script.sh
fi

# Rotate log if greater than 10Mb
LOG="/config/log.txt"
if [ -f "$LOG" ] && [ $(du -m "$LOG" | cut -f1) -gt 10 ]; then
    mv "$LOG" "$LOG.old"
fi
