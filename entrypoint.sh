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
      touch /config/post_script.py
    fi
  fi
  # Creates shell script if needed
  if [ "$(echo "$POST_SCRIPT_SH" | tr '[:upper:]' '[:lower:]')" == "true" ]; then
    if [ ! -f /config/post_script.sh ]; then
      echo "Creating post_script.sh script"
      touch /config/post_script.sh
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