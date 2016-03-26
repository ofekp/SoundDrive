#!/usr/bin/python2.7

import os
import sys
import httplib2
import subprocess
import webbrowser
# sudo pip install --upgrade google-api-python-client
from oauth2client import client
from oauth2client.file import Storage

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
if not os.path.isdir("playlists/" + playlist_title):
    os.makedirs("playlists/" + playlist_title)    

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

youtube_video_url_prefix = "http://www.youtube.com/watch?v="
youtube_video_to_mp3_service_url = "wwww.youtube-mp3.org"

# sudo pip install youtube-dl
import youtube_dl
options = {
    'outtmpl': 'playlists/' + playlist_title + '/%(id)s',
    'extractaudio': True,
    'format': 'bestaudio/best',
    'audioformat': 'mp3',
    'noplaylist': True
}
with youtube_dl.YoutubeDL(options) as ydl:
    ydl.download([youtube_video_url_prefix + songs[0]['video_id']])





