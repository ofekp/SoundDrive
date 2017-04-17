#!/usr/bin/python2.7

from __future__ import unicode_literals

import os, errno
import sys
import time
import httplib2
import urllib2
from subprocess import Popen, PIPE, check_output
import webbrowser
# USE THIS: sudo pip install oauth2client==3.0.0
# Give full permissions to both .json credetial files
# DO NOT USE (this will update to version 4.0 which will creates a File Cache Error): sudo pip install --upgrade google-api-python-client
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
logging.basicConfig(filename='output.log',level=logging.DEBUG)

config_file_name = "sound_drive_local.cfg"

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

def youtubeDlHook(d):
    if d['status'] == 'finished':
        file_tuple = os.path.split(os.path.abspath(d['filename']))
        logging.debug("Done downloading [" + file_tuple[1] + "]")
    if d['status'] == 'downloading':
        logging.debug("[" + d['filename'] + "] [" + d['_percent_str'] + "] [" + d['_eta_str'] + "]")

# Download the video
# Requires 'brew install ffmpeg' (not libav!)
# also may require 'brew update && brew upgrade ffmpeg'
# 
# MAC: Requires 'brew install ffmpeg' (not libav!)
# Linux: Requires 'sudo apt-get install libav-tools'
c = 0
def downloadSong(yt_song_structure):
    global c
    
    if c > 0:
        return
    #c += 1

    options = {
        'writethumbnail': True,
        'outtmpl': yt_song_structure['playlist_path'] + '/' + yt_song_structure['title'] + '.%(ext)s',
        'extractaudio': True,
        'noplaylist': True,
        'max_downloads': 1,
        'progress_hooks': [youtubeDlHook],
        'format': 'bestaudio/best',
        #'ignoreerrors': True,
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
            ydl.download([str(yt_song_structure['url'])])
    except Exception, e:
        logging.debug("EXCEPTION: Skipping [" + yt_song_structure['url'] + "]...")
        logging.debug("Exception message: " + str(e))
        logging.debug(e.__doc__)
        logging.debug(e.message)
        

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


def sync_playlist(playlist_name_list):
    global songs
    global keep_current_song_index
    global is_song_playing
    global curr_song_play_pipe
    global playlist_root_path

    if not internet_on():
        # Sound taken from http://soundbible.com/1540-Computer-Error-Alert.html
        logging.debug("No internet connection, aborting playlist sync process.")
        return

    try:
        curr_song_play_pipe.stdin.write('p')
    except:
        logging.warning("No song to stop playing for the sync process")
        
    # TODO: this is for debug only (remove when done!)
    #try:
    #    ipaddr = check_output("ifconfig | grep -A 1 wlan0 | grep 'inet addr:' | cut -d':' -f2 | cut -d' ' -f1", shell=True)
    #    sendNotification(ipaddr)
    #except:
    #    logging.warning("Could not send message to phone...")

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

    youtube = build('youtube', 'v3', http = http_auth)
    
    playlist_id_list = []
    for playlist_name in playlist_name_list:    
        logging.debug("Playlist id must be retrieved before continuing")
        if playlist_name == None or len(playlist_name) == 0:
            logging.debug("ERROR: Playlist name must be set before continuing")
            exit(1)
        # Retrieve the playlist id
        playlist_id = get_playlist_id(youtube, playlist_name)
        if playlist_id == None or len(playlist_id) == 0:
            logging.debug("ERROR: Could not get playlist ID for playlist [" + playlist_name + "]")
            exit(1)
        playlist_id_list.append(playlist_id)
        # Write the playlist id to the config file
        config.set('youtube', 'playlist_id_list', playlist_id_list)
        save_global_config(config)

    logging.debug("playlist_id_list: " + str(playlist_id_list))
        
    # Get videos list from the playlist response
    songs = []

    for i, playlist_id in enumerate(playlist_id_list):
        nextPageToken = ""
        playlist = {}
        playlist = {"playlist_name": playlist_name_list[i], "songs": []}
        while True:
            response = youtube.playlistItems().list(
                part="snippet",
                maxResults=10,
                pageToken=nextPageToken,
                playlistId=playlist_id
                ).execute()

            for playlist_item in response["items"]:
                song_title = playlist_item["snippet"]["title"]
                song_title = re.sub('[^A-Za-z0-9 \(\)\[\]_-]+', '', song_title)
                song_title = unicode(song_title).encode('utf8')
                song_title = song_title.replace(":", " -")
                song_title = song_title.replace("^", "")
                song_title = song_title.replace("  ", " ")
                song_title = song_title.replace("  ", " ")
                song_title = song_title.replace("  ", " ")
                song_title = song_title.replace("  ", " ")
                song_title = song_title.replace("  ", " ")
                song_title = re.sub('^ - ', '', song_title)
                song_title = song_title.replace("[", "(").replace("]", ")")
                logging.debug("song title ==> " + song_title)
                video_id = playlist_item["snippet"]["resourceId"]["videoId"]
                video_id = unicode(video_id).encode('utf8')
                if (song_title == ""):
                    logging.warning("Song name is empty. Video ID [" + video_id + "]")
                playlist['songs'].append({"title": song_title, "video_id": video_id});

            if "nextPageToken" in response:
                nextPageToken = response["nextPageToken"]
            else:
                break;
        songs.append(playlist)
        
    logging.debug("songs structure: " + str(songs))
        
    yt_vids_to_download = []
    yt_vids_to_delete = []
    # List all needed songs
    needed_song_files = {}
    for playlist in songs:
        needed_song_files[playlist['playlist_name']] = [song['title'] + ".mp3" for song in playlist['songs']];
        
    logging.debug("needed_song_files " + str(needed_song_files))
    stats = []

    for playlist in songs:
        playlist_name = playlist['playlist_name']
        playlist_stats = {"playlist_name": playlist_name, "current": 0, "remove": 0, "download": 0, "final": 0}
        playlist_path = playlist_root_path + playlist_name
        # Get local folder playlist
        files = [f for f in os.listdir(playlist_path) if os.path.isfile(os.path.join(playlist_path, f)) and os.path.getsize(os.path.join(playlist_path, f))]
        files = sorted(files)
        logging.debug("Files in folder [" + playlist_path + "] are " + str(files))
        playlist_stats['current'] = len(files)
        playlist_stats['final'] += playlist_stats['current']

        youtube_video_url_prefix = "http://www.youtube.com/watch?v="

        # Check which songs should be downloaded
        from multiprocessing.dummy import Pool as ThreadPool
        pool = ThreadPool(int(getNumOfCores()))
        for song in playlist['songs']:
            song_title = song['title']
            song_file = song['title'] + ".mp3"
            if song_file in files:
                logging.debug("File [" + song_file + "] already exists.")
            else:
                if isVideoAvailable(youtube, song['video_id']):
                    playlist_stats['download'] += 1
                    playlist_stats['final'] += 1
                    logging.debug("[TO_DOWNLOAD] tag applied to [" + song['title'] + "] with ID [" + song['video_id'] + "]")
                    yt_vids_to_download.append({"playlist_path": playlist_path, "title": song_title, "url": youtube_video_url_prefix + song['video_id']})
                else:
                    logging.warning("Video [" + song['title'] + "] with id [" + song['video_id'] + "] is not available")
            
        for song_file in files:
            if song_file not in needed_song_files[playlist_name]:
                yt_vids_to_delete.append(os.path.join(playlist_path, song_file))
                logging.debug("[TO_REMOVE] tag applied to [" + song_file + "]")
                playlist_stats['remove'] += 1
                playlist_stats['final'] -= 1
    
        stats.append(playlist_stats)

    logging.debug("stats: " + str(stats))
                
    if len(yt_vids_to_download) == 0 and len(yt_vids_to_delete) == 0:
        logging.debug("SoundDrive is synched with YouTube, continuing to play where the song stopped")
        try:
            curr_song_play_pipe.stdin.write('p')
        except:
            logging.warning("Pause received but no song is playing at the moment")
    else:
        for song_file in yt_vids_to_delete:
            logging.debug("Removing file [" + song_file + "]...")
            os.remove(song_file)

        logging.debug("Starts downloading songs...")
        startDLTimestamp = int(time.time())
        pool.map(downloadSong, yt_vids_to_download)
        pool.close()
        pool.join()
        logging.debug("YouTube download is DONE in [" + str(int(time.time()) - startDLTimestamp) + "] seconds")

    # Write the songs array to the config file
    config.set('youtube', 'songs', songs)
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
    config.set('youtube', 'playlist_name_list', '["music", "music archive"]')  # TODO: Need to find a way for the user to config this
    config.set('youtube', 'playlist_id_list', '[]')  # Dynamically set using the youtube API and the name of the playlist
    config.set('youtube', 'songs', '[]')  # Depicts the playlist songs order and info  # TODO: this config should be in a config file inside the corresponding playlist folder
    config.add_section('bluetooth')
    config.set('bluetooth', 'device_names', '[\"SKODA\", \"AP5037\"]')  # TODO: Need to find a way for the user to config this
    save_global_config(config)


# Get important config fields
playlist_name_list = eval(config.get('youtube', 'playlist_name_list'))
playlist_id_list = eval(config.get('youtube', 'playlist_id_list'))
songs = eval(config.get('youtube', 'songs'))
playlist_root_path = "playlists/local/"

# Create playlist folder if needed
for playlist_name in playlist_name_list:
    playlist_path = playlist_root_path + playlist_name
    logging.debug("Creating playlist_path [" + playlist_path + "]")
    if not os.path.isdir(playlist_path):
        os.makedirs(playlist_path)

logging.debug("Sync starting...")
sync_playlist(playlist_name_list)
logging.debug("DONE.")

# Print songs summary
for playlist in songs:
    logging.debug("Playlist [" + playlist['playlist_name'] + "]")
    for song in playlist['songs']:
        logging.debug("    Title [" + song['title'] + "] video_id [" + song['video_id'] + "]")
