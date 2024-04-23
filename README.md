# Android TV Background

This is a simple script to retrieve plex or TMDB media background, i developed this to use it with alternative android tv launcher

To use the script, you have to specify : 
- your plex token and plex server url
- Your TMDB API

The script retrieves the background of the latests shows (movies or tv shows)
it resizes the image, add an overlay and add text on top

![image](https://github.com/adelatour11/plexbackground/assets/1473994/3cf48b69-1b4f-45d5-8f46-565864994660)

![image](https://github.com/adelatour11/plexbackground/assets/1473994/d1886abd-5102-476c-b020-7466b5aa4be1)

![image](https://github.com/adelatour11/plexbackground/assets/1473994/e7ab41b2-f731-4db5-8e22-cd8f0b81b0e5)

![image](https://github.com/adelatour11/plexbackground/assets/1473994/fedb7822-acb6-47e5-af83-37ad8831204f)

How to :
- install python and dependencies
- Download the content of this repository and put the script and images in a specific folder
- Edit the script "script.py" to specify you credentials,
- For plex media you can specify the number of poster to generate, specify if you want to include movies and tv, specify if you want latest added or latest aired items. You can also edit the code to change the text position or content
- As you run one of the script  it will create a new folder called backgrounds and it will create the images automatically. Each time the script runs it will delete the content of the folder and create new images


