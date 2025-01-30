#!/bin/bash

# set uid/guid/umask & perms
PUID=${PUID:-99}
PGID=${PGID:-100}
umask 0002
if [ "$(id -u xyz)" != "$PUID" ]; then
  usermod -o -u "$PUID" xyz
fi
if [ "$(id -g xyz)" != "$PGID" ]; then
  groupmod -o -g "$PGID" xyz
fi
if [ "$(id -u xyz)" != "$PUID" ] || [ "$(id -g xyz)" != "$PGID" ]; then
  echo "Updating PUID to $PUID and PGID to $PGID"
  chown -R xyz:xyz /app
fi

# copies config file if needed and then run python scripts 
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
  echo "Setup complete! Please read directions for settings & usage"
fi

# Creates python script if needed
if [ "${POST_SCRIPT_PY,,}" == "true" ]; then
  if [ ! -f /config/post_script.py ]; then
    touch /config/post_script.py
  fi
fi
# Creates shell script if needed
if [ "${POST_SCRIPT_SH,,}" == "true" ]; then
  if [ ! -f /config/post_script.sh ]; then
    touch /config/post_script.sh
    chmod +x /config/post_script.sh
  fi
fi

# configure, verify and start cron
if [ -v CRON ] && [ "${CRON,,}" != "false" ]; then
  echo "$CRON /bin/bash /run.sh >> /config/log.txt 2>&1" > /app/cron
  CRON_VERIFY=$(./supercronic -no-reap -test -quiet /app/cron 2>&1)
  if [ ! -z "$CRON_VERIFY" ]; then
    echo "Bad cron format detected. Fix and remake the container to try again"
    exit 1
  else
    echo "Backgrounds will be created on container start and on this schedule: $CRON"
    # run scripts at container start
    ./run.sh >> /config/log.txt 2>&1
    # Start cron
    exec "$@"
  fi
else
  echo "No cron detected. Backgrounds only created each time container starts."
  # run scripts at container start
  ./run.sh >> /config/log.txt 2>&1
  echo "No cron schedule. Stopping Container"
  exit 0
fi