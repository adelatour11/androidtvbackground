#!/bin/sh

# set file creation mode
umask 0002

# copies config files if needed and then runs python scripts 
if [ ! -f /config/plex.py ]; then
# begin initial setup
  echo "
-----------------------------------------
          Android TV Background          
-----------------------------------------
Code by: adelatour11
-----------------------------------------
Docker brought to you by:                
 _  _ _     _   _                        
| \| (_)_ _| |_| |_                      
| .' | | ' \  _| ' \                     
|_|\_|_|_||_\__|_||_|                    
__      __    _ _                        
\ \    / /_ _| | |_____ _ _              
 \ \/\/ / _' | | / / -_) '_|             
  \_/\_/\__,_|_|_\_\___|_|               
                                         
-----------------------------------------
"
  echo "New install detected. Copying config files.."
  cp /app/plex.py /app/TMDB.py /app/trakt.py /config/

# Creates python script if needed
  if [ "$(echo "$POST_SCRIPT_PY" | tr '[:upper:]' '[:lower:]')" == "true" ]; then
    if [ ! -f /config/post_script.py ]; then
      echo "Creating post_script.py script"
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
  if [ "$(echo "$POST_SCRIPT_SH" | tr '[:upper:]' '[:lower:]')" == "true" ]; then
    if [ ! -f /config/post_script.sh ]; then
      echo "Creating post_script.sh script"
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

  echo "Setup complete! Please read directions for settings & usage"
else
  # configure, verify and start cron
  if [ -n "$CRON" ] && [ "$(echo "$CRON" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    echo "$CRON /bin/sh /run.sh >> /config/log.txt 2>&1" > /app/cron
    CRON_VERIFY=$(/supercronic -no-reap -test -quiet /app/cron 2>&1)
    if [ -n "$CRON_VERIFY" ]; then
      echo "Bad cron format detected. Fix and remake the container to try again"
      exit 1
    else
      echo "Backgrounds will be created on container start and on this schedule: $CRON"
      # run scripts at container start
      /bin/sh /run.sh >> /config/log.txt 2>&1
      # Start cron
      exec "$@"
    fi
  else
    echo "No cron detected. Backgrounds only created each time container starts."
    # run scripts at container start
    /bin/sh /run.sh >> /config/log.txt 2>&1
    echo "No cron schedule. Stopping Container"
    exit 0
  fi
fi
