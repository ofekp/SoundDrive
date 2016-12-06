#!/usr/bin/python2.7

import os, errno
import sys
import time
import httplib2
import urllib2
from subprocess import Popen, PIPE, check_output
import webbrowser
# sudo pip install --upgrade google-api-python-client
from oauth2client import client
from oauth2client.file import Storage
from threading import Thread
import re
import logging
import ConfigParser
import json
import filecmp
import multiprocessing

# ******
# Consts
# ======
config_file_name = "sound_drive.cfg"


def save_global_config(config_obj):
    with open(config_file_name, 'wb') as config_file:
        config_obj.write(config_file)


def internet_on():
    try:
        response = urllib2.urlopen('http://www.google.com', timeout=5)
        return True
    except urllib2.URLError as err:
        pass
    return False


def getNumOfCores():
    numOfCores = multiprocessing.cpu_count()
    return numOfCores


# **********
# youtube_dl
# ==========
# sudo pip install youtube-dl
# Important to update! use 'sudo pip install -U youtube-dl' for that
import youtube_dl

# MAC: Requires 'brew install ffmpeg' (not libav!)
# Linux: Requires 'sudo apt-get install libav-tools'
c = 0
def downloadSong(yt_song_url):
    global c
    global playlist_path
    # Download the video
    
    if c > 0:
        return
    #c += 1

    options = {
        'writethumbnail': True,
        'outtmpl': playlist_path + '/%(title)s.%(ext)s',
        'extractaudio': True,
        'noplaylist': True,
        'format': 'bestaudio/best',
        'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        {'key': 'FFmpegMetadata'}, 
        {'key': 'EmbedThumbnail'},
        ]
    }
    try:
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([yt_song_url])
    except:
        print "EXCEPTION: Skipping [" + yt_song_url + "]..."

def isVideoAvailable(youtube, video_id):
    # Get the playlist name
    response = youtube.videos().list(
        part="status",
        id=video_id
        ).execute()
    if response["items"] == []:
        return False
    video = response["items"][0]
    return (video['status']['uploadStatus'] == 'processed')


# (Not used)
# Get the playlist name using its ID (not being used currently)
def get_playlist_name(youtube, playlist_id):
    response = youtube.playlists().list(
        part="snippet",
        id=playlist_id
        ).execute()
    playlist_name = response["items"][0]["snippet"]["title"]
    return playlist_name


# Get the playlist id from its name
def get_playlist_id(youtube, playlist_name):
    logging.debug("Retirieving playlist id for playlist [" + playlist_name + "] ")
    nextPageToken = ""
    while True:
        response = youtube.playlists().list(
            part="snippet",
            maxResults=10,
            pageToken=nextPageToken,
            mine=True
            ).execute()

        for playlist_item in response["items"]:
            playlist_title = playlist_item["snippet"]["title"]
            #playlist_title = unicode(playlist_title).encode('utf8')
            if playlist_title == playlist_name:
                playlist_id = playlist_item["id"]
                print "Found playlist [" + playlist_title + "] with id [" + playlist_id + "]"
            	logging.debug("Found playlist [" + playlist_title + "] with id [" + playlist_id + "]")
            	return playlist_id

        if "nextPageToken" in response:
            nextPageToken = response["nextPageToken"]
        else:
            break;
    return None


def start_sync_playlist_thread():
    # Sync playlist
    logging.debug("BT command: SYNC PLAYLIST")
    sync_playlist_thread = Thread(target=sync_playlist)
    #sync_playlist_thread.daemon = True
    sync_playlist_thread.start()


def sync_playlist():
    global songs
    global keep_current_song_index
    global is_song_playing
    global curr_song_play_pipe
    global playlist_id

    if not internet_on():
        # Sound taken from http://soundbible.com/1540-Computer-Error-Alert.html
        logging.debug("No internet connection, aborting playlist sync process.")
        return

    try:
        curr_song_play_pipe.stdin.write('p')
    except:
        logging.warning("No song to stop playing for the sync process")
        
    # TODO: this is for debug only (remove when done!)
    try:
        ipaddr = check_output("ifconfig | grep -A 1 wlan0 | grep 'inet addr:' | cut -d':' -f2 | cut -d' ' -f1", shell=True)
        sendNotification(ipaddr)
    except:
        logging.warning("Could not send message to phone...")

    # Sound taken from https://appraw.com/ringtone/input-xxk4r
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
    
    if playlist_id == None or len(playlist_id) == 0:
        # Need to retrieve the playlist id
        logging.debug("Playlist id must be retrieved before continuing")
        if playlist_name == None or len(playlist_name) == 0:
        	logging.debug("ERROR: Playlist name must be set before continuing")
        	exit(1)
        # Retrieve the playlist id
        playlist_id = get_playlist_id(youtube, playlist_name)
        if playlist_id == None or len(playlist_id) == 0:
        	logging.debug("ERROR: Could not get playlist ID for playlist [" + playlist_name + "]")
        	exit(1)
        # Write the playlist id to the config file
        config.set('youtube', 'playlist_id', playlist_id)
        save_global_config(config)

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
            song_title = unicode(song_title).encode('utf8')
            video_id = playlist_item["snippet"]["resourceId"]["videoId"]
            video_id = unicode(video_id).encode('utf8')
            songs.append({"title": song_title, "video_id": video_id});

        if "nextPageToken" in response:
            nextPageToken = response["nextPageToken"]
        else:
            break;

    # Get local folder playlist
    files = [f for f in os.listdir(playlist_path) if os.path.isfile(os.path.join(playlist_path, f)) and os.path.getsize(os.path.join(playlist_path, f))]
    files = sorted(files)
    logging.debug("Files in folder [" + playlist_path + "] are " + str(files))

    youtube_video_url_prefix = "http://www.youtube.com/watch?v="

    # Check which songs should be downloaded
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool(int(getNumOfCores()))
    yt_vids_to_download = []
    for song in songs:
        song_file = song['title'] + ".mp3"
        song_photo_file = song['title'] + ".jpg"
        if song_file in files and not song_photo_file in files:
            logging.debug("File [" + song_file + "] already exists.")
        else:
            if isVideoAvailable(youtube, song['video_id']):
                logging.debug("Marked YouTube song [" + song['video_id'] + "] for download")
                yt_vids_to_download.append(youtube_video_url_prefix + song['video_id'])
            else:
                logging.debug("Video [" + song['title'] + "] with id [" + song['video_id'] + "] is not available")

    yt_vids_to_delete = []
    needed_song_files = [song['title'] + ".mp3" for song in songs]
    for song_file in files:
        if song_file not in needed_song_files:
            yt_vids_to_delete.append(os.path.join(playlist_path, song_file))
            logging.debug("Marked song file [" + song_file + "] to be rermoved")

    if len(yt_vids_to_download) == 0 and len(yt_vids_to_delete) == 0:
        logging.debug("SoundDrive is synched with YouTube, continuing to play where the song stopped")
        try:
            curr_song_play_pipe.stdin.write('p')
        except:
            logging.warning("Pause received but no song is playing at the moment")
    else:
        logging.debug("Started downloading songs...")
        startDLTimestamp = int(time.time())
        pool.map(downloadSong, yt_vids_to_download)
        pool.close()
        pool.join()
        logging.debug("YouTube download is DONE in [" + str(int(time.time()) - startDLTimestamp) + "] seconds")

        for song_file in yt_vids_to_delete:
            logging.debug("Removing file [" + song_file + "]...")
            os.remove(song_file)

        # Write the songs array to the config file
        config.set('youtube', 'playlist', songs)
        save_global_config(config)

        # Start playing the playlist from the beginning
        config.set('playback', 'last_played_song_index', '0')
        save_global_config(config)


config = ConfigParser.RawConfigParser()
# Config file is created for the first time
if not os.path.isfile(config_file_name) or os.stat(config_file_name).st_size == 0 or config.read(config_file_name) == []:
    logging.debug("Could not find config");
    config.add_section('playback')
    config.set('playback', 'last_played_song_index', '0')
    config.add_section('youtube')
    config.set('youtube', 'playlist_name', 'music')  # TODO: Need to find a way for the user to config this
    config.set('youtube', 'playlist_id', '')  # Dynamically set using the youtube API and the name of the playlist
    config.set('youtube', 'playlist', '[]')  # Depicts the playlist songs order and info  # TODO: this config should be in a config file inside the corresponding playlist folder
    config.add_section('bluetooth')
    config.set('bluetooth', 'device_names', '[\"SKODA\", \"AP5037\"]')  # TODO: Need to find a way for the user to config this
    save_global_config(config)


# Get important config fields
playlist_name = config.get('youtube', 'playlist_name')
playlist_id = config.get('youtube', 'playlist_id')
songs = eval(config.get('youtube', 'playlist'))
# Fields deduced from config
playlist_path = "playlists/local/" + playlist_name

# Create playlist folder if needed
if not os.path.isdir(playlist_path):
    os.makedirs(playlist_path)

print "Sync starting..."
sync_playlist()
print "DONE."

# Print songs summary
for song in songs:
    print "    Title [" + song['title'] + "] video_id [" + song['video_id'] + "]"
