# Android TV Background

This is a simple script to retrieve Plex or TMDB media background and use it as Android TV Wallpaper
I developed this to use it with alternative Android TV launchers

![y](https://github.com/adelatour11/androidtvbackground/assets/1473994/8039b728-469f-4fd9-8ca5-920e57bd16d9)


To use the script, you have to specify : 
- For Plex.py script : your plex token and plex server url
- For TMDB.py or TMDBlogo.py : your TMDB API Read Access Token
- For Trakt.py, your Trakt client key, Trakt username, Trakt list name and TMDB API Read Access Token

The scripts retrieves the background of the latests shows (movies or tv shows), resizes the image, add an overlay and add text or image on top

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/434e7077-daaf-41b6-8e43-08bf380fb2d3)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/da313f5f-287f-430f-b3fd-f56e5f139e40)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/25565525-1958-4944-b47f-b06344d22914)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/b96f3e83-29a6-4e3f-a202-2e33bc80aa8f)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/b28900a4-4776-4aae-b631-e30334d932dd)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/e0410589-81a4-40ac-a55d-8fd6eb061721)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/2e92f213-21f9-4147-b678-0ee4dd0546ad)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/03aecbcd-e2fd-4969-b0a2-0346d1842705)


**How to :**
- install latest version of python (https://www.python.org/downloads/)
- Install pip (follow the process here https://pip.pypa.io/en/stable/installation/)
- Download the content of this repository
- Go into the repository using a terminal and install dependencies :
  ```
  pip install -r requirements.txt
  ```
- Edit each python scripts with your info
    - Specify you credentials
        - for Plex check this article on how to find your plex token https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
        - for TMDB create an account and get you api key here there https://www.themoviedb.org/settings/api
        - for Trakt create your account and go there https://trakt.tv/oauth/applications to create an app and retrieve your client id 
- As you run one of the script it will create a new folder and add the images automatically.
- Each time the scripts will run it will delete the content of the folder and create new images
- if you want to edit the overlay and background image I have included the source file as a vector format 

**If you want to edit the scripts :**
***Plex Script***
- For the plex script you can specify the number of poster to generate, specify if you want to include movies and tv, specify if you want latest added or latest aired items. You can also edit the code to change the text position or content
***TMDB Scripts***
- There is two versions of the TMDB script, one without show logo and one without. Shows that do not have the logo on TMDB will just have the title displayed
- You can edit the script to change the color, the text position or font
- You can edit the code to change the endpoints for trending shows that is here
      ```
      trending_movies_url = f'{url}trending/movie/week?language=en-US'
      trending_tvshows_url = f'{url}trending/tv/week?language=en-US'
      ```
  and replace it by using TMDB API Discover Endpoint
  You can find details on Discovery endpoints here  : https://developer.themoviedb.org/reference/discover-movie or https://developer.themoviedb.org/reference/discover-tv
  For example you can change the endpoints like this
      ```
      # Endpoint for shows with genre action from 2022 
      trending_movies_url = f'{url}discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&with_genres=80&year=2022'
      trending_tvshows_url = f'{url}discover/tv?first_air_date_year=2022&include_adult=false&include_null_first_air_dates=false&language=en-US&page=1&sort_by=popularity.desc&with_genres=80'
      ```
  The genre is set by an id, you can get the list from these url https://developer.themoviedb.org/reference/genre-movie-list or https://developer.themoviedb.org/reference/genre-tv-list
