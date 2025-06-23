# Android TV Background

This is a simple script to retrieve Plex, Jellyfin, TMDB or Trakt media background and use it as Android TV Wallpaper
I developed this to use it with alternative Android TV launchers

![y](https://github.com/adelatour11/androidtvbackground/assets/1473994/8039b728-469f-4fd9-8ca5-920e57bd16d9)


To use the script, you have to specify : 
- For Plex.py script : your plex token and plex server url either in the script or in a `.env` file
    - Create a `.env` file by copying `.env.example` and update it with your Plex token and server URL
- For TMDB.py or TMDBlogo.py : your TMDB API Read Access Token
- For Trakt.py, your Trakt client key, Trakt username, Trakt list name and TMDB API Read Access Token
- For Jellyfin.py, your server url, token and user id

The scripts retrieves the background of the latests shows (movies or tv shows), resizes the image, add an overlay and add text or image on top

![image](https://github.com/user-attachments/assets/71923ddf-6b5b-4b1c-af46-d12d9a525b6c)

![image](https://github.com/user-attachments/assets/e560ccf7-cc11-49ce-b6c1-8395d2e309f1)

![image](https://github.com/user-attachments/assets/815c3685-2b6d-4ef5-86c3-b2d67038736a)

![image](https://github.com/user-attachments/assets/c01d5d0e-d762-481d-ab66-7110a7101e22)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/b28900a4-4776-4aae-b631-e30334d932dd)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/e0410589-81a4-40ac-a55d-8fd6eb061721)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/2e92f213-21f9-4147-b678-0ee4dd0546ad)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/03aecbcd-e2fd-4969-b0a2-0346d1842705)

**Note :**
If you are looking for the docker version check out this branch https://github.com/adelatour11/androidtvbackground/tree/docker

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
- Shows that do not have the logo on TMDB will just have the title displayed
- You can edit the script to change the color, the text position or font, you can specify exclusion based on origin country code or genre
- By default the script will retrieve the posters for the movies or TV shows whose last air date is older than 30 days from the current date. For the TV Shows, the episode last air date is considered.      
- You can edit the code to change the endpoints for trending shows that is here
  ```
  trending_movies_url = f'{url}trending/movie/week?language=en-US'
  trending_tvshows_url = f'{url}trending/tv/week?language=en-US'
  ```
  and replace it by using TMDB API Discover Endpoint
  You can find details on Discovery endpoints here  :

  https://developer.themoviedb.org/reference/discover-movie

  https://developer.themoviedb.org/reference/discover-tv

  For example you can change the endpoints like this

  ```
  # Endpoint for shows with genre action from 2022
  trending_movies_url = f'{url}discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&with_genres=80&year=2022'
  trending_tvshows_url = f'{url}discover/tv?first_air_date_year=2022&include_adult=false&include_null_first_air_dates=false&language=en-US&page=1&sort_by=popularity.desc&with_genres=80'
  ```
  
  The genre is set by an id, you can get the list from these url
  
  https://developer.themoviedb.org/reference/genre-movie-list
  
  https://developer.themoviedb.org/reference/genre-tv-list
