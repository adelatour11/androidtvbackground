# Android TV Background Docker
  
Dockerized version of [androidtvbackground](https://github.com/adelatour11/androidtvbackground)

### Docker Install Instructions:

- docker-compose.yml file is the preferred way
   1. Update the volume mapping to your local location for the config files as well as where the background images will be saved to.
      Backgrounds can be saved to within a subdir of the config location if you want them both in the same spot, or a different location.
   2. Set the env variables to 'True' for each of the scripts you want run. They are all set to False by default and will not run.
   3. If you want to have the container stay started and create backgrounds on a schedule, set the cron to a cron format expression.  
      ie: set `CRON="0 0 * * *"` to have the backgrounds created once a day at midnight. Set to 'False' to not use a schedule.

    From within your docker-compose.yml directory, run:  
    `docker compose up -d`

- Alternative install is via docker run command line  
   It would look something like this, depending on config options that you want:  
   ```
   docker run -d --name androidtvbackground -v /your/local/path/for/config:/config -v /your/local/path/for/backgrounds:/backgrounds -e PLEX=True -e TMDB=True -e TRAKT=False -e POST_SCRIPT_PY=False -e POST_SCRIPT_SH=True -e CRON="0 0 * * *" ghcr.io/ninthwalker/androidtvbackground:latest
   ```  

- The last install method is to build it yourself locally using the Dockerfile from this repo
   1. Clone this repo and extract contents
   2. From within the extracted folder, open a cmd prompt and run:  
   `docker build . -t androidtvbackground`
   3. Once built, you can reference the local image in your docker-compose.yml file or your run cmd. A run cmd would look something like this, depending on config options that you want:  
   ```
   docker run -d --name androidtvbackground -v /your/local/path/for/config:/config -v /your/local/path/for/backgrounds:/backgrounds -e PLEX=True -e TMDB=True -e TRAKT=False -e POST_SCRIPT_PY=False -e POST_SCRIPT_SH=True -e CRON="0 0 * * *" androidtvbackground
   ```  
  
### First run:

- Script files will be copied into your mapped config volume on your host.
  1. Edit these according to the [instructions](https://github.com/adelatour11/androidtvbackground/blob/main/README.md)
  1. Start the container again with:
  `docker start androidtvbackground`
  
### Docker Usage Instructions: 

- Each script set to 'True' will run when the docker is started. If CRON is set to a schedule, the container will stay running and create backgrounds according to your CRON schedule.  
- If CRON is set to 'False', the container will stop after creating backgrounds and you will need to manually start it again to create more backgrounds with:  
  `docker start <name of docker>`   
  *Note that backgrounds will always be created the first time the container starts, even when a cron schedule is set.*  
  
### Docker Settings:
    
- Scripts can be found in the container /config directory that should be mapped to your local system for access. Edit these files as per the [instructions](https://github.com/adelatour11/androidtvbackground/blob/main/README.md)
  - **PLEX:** If set to True, retrieves backgrounds from your own [Plex Server](plex.tv).
  - **TMDB:** If set to True, retrieves backgrounds from [The Movie Database](themoviedb.org)
  - **TRAKT:** If set to True, retrieves plex backgrounds from [Trakt](trakt.tv)
  - **CRON:** If set to a cron expression (ie: `CRON="0 0 * * *"`) the docker will stay running and create backgrounds during the schedule you set. If you would rather manually start the docker to create backgrounds, set this to False
  - **POST_SCRIPT_PY:** If set to True, you can define your own python code in the 'post_script.py' file and it will be run at the end of the background creation.
  - **POST_SCRIPT_SH**: If set to True, you can define your own shell code in the 'post_script.sh' file and it will be run at the end of the background creation.
    - Useful to copy the files to a specific share, directly to android tv or a subreddit for example. Note that if you define both python and shell post_scripts, the python is run first and then the shell script.
  
- *Note: You can also add PUID and GUID variables if you want to change the user/group the container is run as to match local system. Defaults to 99:100*
- Note 2: Make sure variable names are capitalized as shown in the above examples. ie: `PLEX: True` and *not* `plex: True`

#### Read the [instructions](https://github.com/adelatour11/androidtvbackground/blob/main/README.md) for how to configure each of the scripts with your API/cred information.