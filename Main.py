#!/usr/bin/python2.7

import os
import sys
import time
import httplib2
import subprocess
import webbrowser
# sudo pip install --upgrade google-api-python-client
from oauth2client import client
from oauth2client.file import Storage

# =================
# Private Functions
# +++++++++++++++++

def getNumOfCores():
    proc = subprocess.Popen("nproc", shell=True, stdout=subprocess.PIPE)
    numOfCores = proc.communicate()[0].strip()
    print("Number of cores [" + numOfCores + "]")
    return numOfCores


def isVideoAvailable(youtube, video_id):
    # Get the playlist name
    response = youtube.videos().list(
        part="status",
        id=video_id
        ).execute()
    video = response["items"][0]
    return (video['status']['uploadStatus'] == 'processed')


# sudo pip install youtube-dl
import youtube_dl

def downloadSong(yt_song_url):
    # Download the video
    options = {
        'outtmpl': playlist_path + '/%(id)s.mp3',
        'extractaudio': True,
        'format': 'bestaudio/best',
        'audioformat': 'mp3',
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([yt_song_url])


# ====
# Main
# ++++
    
storage = Storage("%s-oauth2.json" % sys.argv[0])
credentials = storage.get()

if credentials is None or credentials.invalid:
    print("Authentication needed")
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/youtube',
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_uri = flow.step1_get_authorize_url()
    print(auth_uri)
    webbrowser.open_new(auth_uri)
    auth_code = raw_input('Enter the auth code: ')
    credentials = flow.step2_exchange(auth_code)
    storage.put(credentials)
    
http_auth = credentials.authorize(httplib2.Http())

from apiclient.discovery import build

youtube = build('youtube', 'v3', http_auth)

playlist_id = "PLHNuMM2EDWXPmYA5g5WR818Hc08cCK6WV"

# Get the playlist name
response = youtube.playlists().list(
    part="snippet",
    id=playlist_id
    ).execute()
playlist_title = response["items"][0]["snippet"]["title"]
print(playlist_title)
print("==")

# Create folders if needed
playlist_path = "playlists/" + playlist_title
if not os.path.isdir(playlist_path):
    os.makedirs(playlist_path)

# Create/use the existing metadata file to save/retrieve current play state
sdopfile = open(os.path.join(playlist_path, "SDOP.dat"), 'a')

# Get videos list from the playlist response
songs = []
nextPageToken = ""
while True:
    response = youtube.playlistItems().list(
        part="snippet",
        maxResults=10,
        pageToken=nextPageToken,
        playlistId=playlist_id
        ).execute()

    for playlist_item in response["items"]:
        song_title = playlist_item["snippet"]["title"]
        video_id = playlist_item["snippet"]["resourceId"]["videoId"]
        songs.append({"title": song_title, "video_id": video_id});

    if "nextPageToken" in response:
        nextPageToken = response["nextPageToken"]
    else:
        break;

for song in songs:
    print("Title [" + song["title"] + "] video_id [" + song["video_id"] + "]")

print("Total [" + str(len(songs)) + "] songs")
print("")


# Get local folder playlist
files = [f for f in os.listdir(playlist_path) if os.path.isfile(os.path.join(playlist_path, f)) and os.path.getsize(os.path.join(playlist_path, f))]
files = sorted(files)
print("Files " + str(files))

youtube_video_url_prefix = "http://www.youtube.com/watch?v="


from multiprocessing.dummy import Pool as ThreadPool

pool = ThreadPool(int(getNumOfCores()))
yt_vids_to_download = []
for song in songs:
    song_file = song['video_id'] + ".mp3"
    if song_file in files:
        print("File [" + song_file + "] already exists.")
    else:
        if isVideoAvailable(youtube, song['video_id']):
            print("Marked YouTube song [" + song['video_id'] + "] for download")
            yt_vids_to_download.append(youtube_video_url_prefix + song['video_id'])
        else:
            print("Video [" + song['title'] + "] with id [" + song['video_id'] + "] is not available")

print("Started downloading songs...")
startDLTimestamp = int(time.time())
#pool.map(ydl.download, yt_vids_to_download)
pool.map(downloadSong, yt_vids_to_download)
pool.close()
pool.join()
print("DL DONE in [" + str(int(time.time()) - startDLTimestamp) + "] seconds")
    

play_song_command = "omxplayer -o local \"playlists/" + playlist_title + "/" + songs[0]['video_id'] + ".mp3\""
print("Playing " + songs[0]['title'] + "...")
#subprocess.Popen(play_song_command, shell=True, stdout=subprocess.PIPE)

# TODO: sdopfile.close()

