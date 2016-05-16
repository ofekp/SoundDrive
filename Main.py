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


# To setup the network for WiFi refer to:
# (awesome!) http://www.algissalys.com/how-to/how-to-raspberry-pi-multiple-wifi-setup-through-the-command-line
# also look at: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md
# (did not work) http://raspberrypi.stackexchange.com/questions/11631/how-to-setup-multiple-wifi-networks
# Can set multiple possibilities for WiFi networks using this post
# Then restart WiFi using:
# 'sudo service network-manager restart'
# or:
# sudo /etc/init.d/networking restart

# For auto start at boot time:
# sudo vim /etc/rc.local
# add the following line (before the exit command)
# sudo su - pi -c "cd /home/pi/ofek/SoundDrive/; python Main.py &"
# It is important to add the & at the end as this is a never ending script
# It is also important to run as pi and not as root


# ******
# Consts
# ======
config_file_name = "sound_drive.cfg"
time_string = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
curr_log_file_dir = "logs"
curr_log_file_path = curr_log_file_dir + '/output_' + time_string + '.log'
last_log_file_name = 'output.log'


# =================
# Private Functions
# +++++++++++++++++

def save_global_config(config_obj):
    with open(config_file_name, 'wb') as config_file:
        config_obj.write(config_file)


def symlink_force(target, link_name):
    try:
        os.symlink(target, link_name)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e


def internet_on():
    try:
        response = urllib2.urlopen('http://www.google.com', timeout=5)
        return True
    except urllib2.URLError as err:
        pass
    return False


def getNumOfCores():
    proc = Popen("nproc", shell=True, stdout=PIPE)
    numOfCores = proc.communicate()[0].strip()
    logging.debug("Number of cores [" + numOfCores + "]")
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
        'format': 'm4a',  # Crucial so that mplayer will be able to play the songs
        #'audioformat': 'best',
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([yt_song_url])


# Get the playlist name using its ID (not being used currently)
# TODO: should create the opposite function
def get_playlist_name_from_id(youtube):
    response = youtube.playlists().list(
        part="snippet",
        id=playlist_id
        ).execute()
    playlist_name = response["items"][0]["snippet"]["title"]
    return playlist_name


# **************
# Initialization
# ==============

config = ConfigParser.RawConfigParser()

# Create the logs dir if needed
if not os.path.isdir(curr_log_file_dir):
    os.makedirs(curr_log_file_dir)
# Create a log file for this run
logging.basicConfig(filename=curr_log_file_path, level=logging.DEBUG)
# Create a symbolic link for easy access to the last log file
symlink_force(curr_log_file_path, last_log_file_name)

logging.debug('Starting SoundDrive... [' + time_string + ']')

# Config file is created for the first time
if config.read('sound_drive.cfg') == []:
    config.add_section('playback')
    config.set('playback', 'last_played_song_index', '0')
    config.add_section('youtube')
    config.set('youtube', 'playlist_name', 'music')  # TODO: Need to find a way for the user to config this
    config.set('youtube', 'playlist_id', 'PLHNuMM2EDWXPmYA5g5WR818Hc08cCK6WV')  # TODO: Should be dynamically set according to the list's name
    config.set('youtube', 'playlist', '')  # Depicts the playlist songs order and info  # TODO: this config should be in a config file inside the corresponding playlist folder
    config.add_section('bluetooth')
    config.set('bluetooth', 'device_name', 'SKODA')  # AP5037  # TODO: Need to find a way for the user to config this
    save_global_config(config)


# ====
# Main
# ++++

# Get important config fields
playlist_name = config.get('youtube', 'playlist_name')
playlist_id = config.get('youtube', 'playlist_id')
songs = eval(config.get('youtube', 'playlist'))
curr_song_index = config.getint('playback', 'last_played_song_index')
if songs != None and len(songs) != 0:
    curr_song_index = curr_song_index % len(songs)  # Just to be on the safe side
bt_device_name = config.get('bluetooth', 'device_name')

# Fields deduced from config
playlist_path = "playlists/" + playlist_name

# Create playlist folder if needed
if not os.path.isdir(playlist_path):
    os.makedirs(playlist_path)

logging.debug("Playlist name [" + playlist_name + "]")
logging.debug("==")

if internet_on():

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

    # Write the songs array to the config file
    config.set('youtube', 'playlist', songs)
    save_global_config(config)

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
        song_file = song['video_id'] + ".mp3"
        if song_file in files:
            logging.debug("File [" + song_file + "] already exists.")
        else:
            if isVideoAvailable(youtube, song['video_id']):
                logging.debug("Marked YouTube song [" + song['video_id'] + "] for download")
                yt_vids_to_download.append(youtube_video_url_prefix + song['video_id'])
            else:
                logging.debug("Video [" + song['title'] + "] with id [" + song['video_id'] + "] is not available")

    if len(yt_vids_to_download) == 0:
        logging.debug("All playlist songs present")
    else:
        logging.debug("Started downloading songs...")
        startDLTimestamp = int(time.time())
        #pool.map(ydl.download, yt_vids_to_download)
        pool.map(downloadSong, yt_vids_to_download)
        pool.close()
        pool.join()
        logging.debug("YouTube download is DONE in [" + str(int(time.time()) - startDLTimestamp) + "] seconds")
        if len(yt_vids_to_download) > 0:
            # Start playing the playlist from the beginning
            config.set('playback', 'last_played_song_index', '0')
            save_global_config(config)
else:
    logging.info("No internet connection found")


# Print songs summary
for song in songs:
    logging.debug("    Title [" + song['title'] + "] video_id [" + song['video_id'] + "]")
logging.debug("Total of [" + str(len(songs)) + "] songs")

# TODO: remove songs from the playlist
# TODO: global config file should keep the current state of the playlist and when it changes - play from first song

# To play the song in AUX
#play_song_command = "omxplayer -o local \"playlists/" + playlist_title + "/" + songs[0]['video_id'] + ".mp3\""
#print("Playing " + songs[0]['title'] + "...")
#subprocess.Popen(play_song_command, shell=True, stdout=subprocess.PIPE)

# To play songs with Bluetooth
# install pulseaudio pulseaudio-module-x11 pulseaudio-utils pavucontrol
# install pulseaudio-module-bluetooth
# bluetoothctl - power on, agent on, default-agent, devices, pair <MAC>, trust <MAC>, connect <MAC>
# To stream music to bluetooth need ALSA - not sure what to download for that, perhaps bluez or bluez-alsa
# now we need mplayer which can direct sound to bluetooth

# To contrl bluetoothctl using python:
# first create a new file call bluetoothctl.py
# inside paste the python script found in 'https://gist.github.com/egorf/66d88056a9d703928f93'
# Line # 38 'out = subprocess.check_output("rfkill unblock bluetooth", shell = True)' might be needed to be commented out
# also before the script can be used, python's 'pexpect' module must be installed
# To do that use 'pip install pexpect'

logging.debug('BT start')

from bluetoothctl import Bluetoothctl
time_between_scans = 5;  # Seconds
max_num_of_attempts_to_scan = 3;

bt = Bluetoothctl()
bt.start_scan()
logging.debug("Searching for BT device [" + bt_device_name + "]")
bt_mac = None
scan_attempt_num = 0
conn_success = False
while not conn_success:
    devices = bt.get_available_devices()
    logging.debug("Devices " + str(devices))
    devMap = {}
    for dev in devices:
        devMap[dev['name']] = dev['mac_address'];
    if bt_device_name in devMap:
        bt_mac = devMap[bt_device_name]

        # To find if already Connected
        # subprocess.check_output("hcitool con")

        logging.debug('trying to connect to [' + bt_device_name + ']')

        logging.debug("Trust device [" + bt_device_name + "] with MAC [" + bt_mac + "]...")
        result = bt.trust(bt_mac)
        logging.debug("Trust result [" + str(result) + "]")

        logging.debug("Paring device [" + bt_device_name + "] with MAC [" + bt_mac + "]...")
        result = bt.pair(bt_mac)
        logging.debug("Paring result [" + str(result) + "]")

        logging.debug("Connecting to device [" + bt_device_name + "] with MAC [" + bt_mac + "]...")
        result = bt.connect(bt_mac)
        logging.debug("Connection result [" + str(result) + "]")
        if result:
            logging.debug('successful connection to [' + bt_device_name + ']')
            conn_success = True

    if not conn_success:
        logging.debug("Could not find device [" + bt_device_name + "] searching again in [" + str(time_between_scans) + "] seconds")
        scan_attempt_num += 1
        if scan_attempt_num > max_num_of_attempts_to_scan:
            logging.debug("Could not find device [" + bt_device_name + "] total number of attempts was [" + max_num_of_attempts_to_scan + "] aborting...")
            os.system("sudo shutdown -h now")
        time.sleep(time_between_scans)

logging.debug('BT end')
time.sleep(15)  # This is crucial to get things working in Skoda!
logging.debug('starting main threads')

# Now playing the song but also listening to events from the bluetooth device
# in order to detect muttimedia button presses (pause, play, previous, next)
# To listen to this buttons' events do the following:
# 1. sudo apt-get install blues-hcidump
# 2. sudo hcidump --raw -i hci0
# sudo is very important, otherwise only BT events (and not data) are detected
# Literally saved the day with that sudo is the following link:
# http://unix.stackexchange.com/questions/234114/hcidump-not-acquiring-data-packets-in-ubuntu-14-04
# https://www.youtube.com/watch?v=TPxw0V42p1o
# Connecting to SKODA for the first time was a bit more complex:
# scan on, trust <MAC>, pair <MAC>, agent on, default-agent, 'yes'

# To get more buttons on a car for example change the cabailities of the bluetooth device
# to include telephony
# This can be done by editting the file '/etc/bluetooth/main.conf'
# refer to 'http://linux.die.net/man/5/hcid.conf' to find out what changes to make

# Another important thing to do is to add a module to /etc/pulse/deafule.pa:
# load-module module-switch-on-connect
# This will change the device to BT when it is connected
# for more information refer to: https://wiki.debian.org/BluetoothUser/a2dp

curr_song_play_pipe = None
is_song_playing = True

raw_play = ["> 02 46 20 0C 00 08 00 42 00 30 11 0E 00 48 7C 44 00", r"> (:?[0-9]{2}\s){6} 40 11 0E 00 48 7C C4 00"]
raw_prev = ["> 02 46 20 0C 00 08 00 42 00 30 11 0E 00 48 7C 4C 00", "> 02 46 20 0C 00 08 00 42 00 40 11 0E 00 48 7C CC 00"]
raw_next = ["> 02 46 20 0C 00 08 00 42 00 30 11 0E 00 48 7C 4B 00", "> 02 46 20 0C 00 08 00 42 00 40 11 0E 00 48 7C CB 00"]

# raw_play_re = re.compile(r"^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C C4 00|^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C C6 00") # AP
raw_prev_re = re.compile(r"^> (?:[0-9,A-F]{2} ){10}11 0E 00 48 7C CC 00") # SKODA
# raw_next_re = re.compile(r"^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C CB 00")
raw_next_re = re.compile(r"^> (?:[0-9,A-F]{2} ){10}11 0E 00 48 7C CB 00") # SKODA
# General code to print the relevant BT mutimedia buttons presses:
def detect_bt_mm_press():
    global curr_song_play_pipe
    global curr_song_index
    global curr_song_play_thread
    global is_song_playing
    global shutdown_pi
    last_pause_ts = 0.0
    logging.debug("Listening to BT multimedia key presses")
    mm_press_re = re.compile(r'^>.{50}')
    proc = Popen(['sudo', 'hcidump', '--raw', '-i', 'hci0'], stdout=PIPE)
    press_state = 0
    for line in iter(proc.stdout.readline, ''):
        if curr_song_play_pipe != None and len(line) == 54 and mm_press_re.match(line) != None:
            logging.debug(line)
            if raw_prev_re.match(line) != None:
                logging.debug("pause")
                try:
                    curr_song_play_pipe.stdin.write('p')
                except:
                    logging.warning("Pause received but no song is playing at the moment")
                curr_time = time.time()
                if curr_time < last_pause_ts + 0.8:
                    # Shutting down PI
                    shutdown_pi = True
                    is_song_playing = False
                    logging.debug("Requested to shutdown, bye bye!")
                    os.system("sudo shutdown -h now")
                    return
                last_pause_ts = curr_time
            if raw_next_re.match(line) != None:
                logging.debug("next")
                try:
                    curr_song_play_pipe.stdin.write('q')
                except:
                    logging.debug("Next received but no song is being played at the moment")
                # Switching to the next song
                if curr_song_play_thread.is_alive():
                    logging.debug("Skipping current song...")
                    is_song_playing = False


def play_songs():
    global curr_song_play_pipe
    global curr_song_index
    global is_song_playing
    global shutdown_pi
    logging.debug("play-songs-thread has started")
    while True:
        time.sleep(1)
        curr_song_index = curr_song_index % len(songs)  # Loop over the playlist
        song = songs[curr_song_index]
        song_file_name = song['video_id'] + ".mp3"
        song_file_path = playlist_path + "/" + song_file_name
        song_file_path = unicode(song_file_path).encode('utf8')
        logging.debug("Playing " + song['title'] + "... path to song [" + song_file_path + "]")
        curr_song_play_pipe = None
        curr_song_play_pipe = Popen(['mplayer', '-quiet', '-ao', 'pulse', '{0}'.format(song_file_path)], stdin=PIPE, stdout=PIPE)
        #curr_song_play_pipe.communciate()
        is_song_playing = True
        while is_song_playing:
            try:
                curr_song_play_pipe.stdin.write('j')  # Should do nothing
                time.sleep(1)
            except:
                is_song_playing = False
        if shutdown_pi == True:
            return

        curr_song_index += 1
        # Write this to the global config file
        config.set('playback', 'last_played_song_index', curr_song_index)
        save_global_config(config)


# Create a thread to listen to BT multimedia key presses
logging.debug("Starting mm bt listen tread")
bt_dump_therad = Thread(target=detect_bt_mm_press)
#bt_dump_therad.daemon = True
bt_dump_therad.start()

# Play the first song
shutdown_pi = False
logging.debug("Initializing play-songs-thread")
curr_song_play_thread = Thread(target=play_songs)
#curr_song_play_thread.daemon = True
curr_song_play_thread.start()

while True:
    time.sleep(10)
exit(1)




# get position in current song:?
# Set the stdout argument to PIPE and you'll be able to listen to the output of the command:
#
# p= subprocess.Popen(['mplayer', url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
# for line in p.stdout:
#     if line.startswith('ICY Info:'):
#         info = line.split(':', 1)[1].strip()
#         attrs = dict(re.findall("(\w+)='([^']*)'", info))
#         print 'Stream title: '+attrs.get('StreamTitle', '(none)')


# sudo apt-get install devscripts
# rmadison mplayer



# sudo apt-get purge smplayer
# sudo apt-get purge mplayer2
# sudo apt-get autoremove
# sudo apt-get install mplayer smplayer




# sudo apt-get --purge --reinstall install libasound2 alsa-utils alsa-oss
