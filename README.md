# Android TV Background

This is a simple script to retrieve Plex or TMDB media background and use it as Android TV Wallpaper
I developed this to use it with alternative Android TV launchers

To use the script, you have to specify : 
- For Plex.py script : your plex token and plex server url
- For TMDB.py or TMDBlogo.py : your TMDB API Read Access Token

The scripts retrieves the background of the latests shows (movies or tv shows), resizes the image, add an overlay and add text or image on top

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/434e7077-daaf-41b6-8e43-08bf380fb2d3)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/da313f5f-287f-430f-b3fd-f56e5f139e40)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/25565525-1958-4944-b47f-b06344d22914)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/b96f3e83-29a6-4e3f-a202-2e33bc80aa8f)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/b28900a4-4776-4aae-b631-e30334d932dd)

![image](https://github.com/adelatour11/androidtvbackground/assets/1473994/e0410589-81a4-40ac-a55d-8fd6eb061721)


How to :
- install latest version of python 
- Download the content of this repository
- Install dependencies : pip install -r requirements.txt
- Edit the python scripts to specify you credentials
    - For plex media you can specify the number of poster to generate, specify if you want to include movies and tv, specify if you want latest added or latest aired items. You can also edit the code to change the text position or content
    - There is two versions of the TMDB script, one without show logo and one without. Shows that do not have the logo on TMDB will just have the title displayed
- As you run one of the script  it will create a new folder and add the images automatically. Each time the scripts will run it will delete the content of the folder and create new images


