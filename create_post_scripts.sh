#!/bin/sh

# Normalize env vars to lowercase for comparison
post_py="$(echo "${POST_SCRIPT_PY:-false}" | tr '[:upper:]' '[:lower:]')"
post_sh="$(echo "${POST_SCRIPT_SH:-false}" | tr '[:upper:]' '[:lower:]')"

# Helper: Create python post_script.py
create_python_script() {
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
}

# Helper: Create shell post_script.sh
create_shell_script() {
  if [ ! -f /config/post_script.sh ]; then
    echo "($(date)) Creating post_script.sh script"
    cat << 'EOF' > /config/post_script.sh
#!/bin/bash

LOG_FILE="/config/log.txt"
SRC_DIR="/config/backgrounds"
DEST_DIR="/config/tvbackgrounds"

if [ ! -d "$DEST_DIR" ]; then
    # Destination folder missing: silently skip moving files
    :
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
}

if [ "$post_py" = "true" ] && [ "$post_sh" = "true" ]; then
  # Both enabled: create default python script and an empty shell script
  create_python_script

  # Create empty shell script if missing
  if [ ! -f /config/post_script.sh ]; then
    echo "($(date)) Creating empty post_script.sh"
    touch /config/post_script.sh
    chmod +x /config/post_script.sh
  fi

elif [ "$post_py" = "true" ]; then
  create_python_script

elif [ "$post_sh" = "true" ]; then
  create_shell_script
fi
