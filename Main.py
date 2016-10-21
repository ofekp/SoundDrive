#!/usr/bin/python2.7

# To setup the network for WiFi refer to:
# (awesome!) http://www.algissalys.com/how-to/how-to-raspberry-pi-multiple-wifi-setup-through-the-command-line
# also look at: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md
# (did not work) http://raspberrypi.stackexchange.com/questions/11631/how-to-setup-multiple-wifi-networks
# Can set multiple possibilities for WiFi networks using this post
# Then restart WiFi using:
# 'sudo service network-manager restart'
# or:
# sudo /etc/init.d/networking restart
#
# My WiFi setup:
# /etc/network/interfaces:
#    # interfaces(5) file used by ifup(8) and ifdown(8)
#    
#    # Please note that this file is written to be used with dhcpcd
#    # For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'
#    
#    # Include files from /etc/network/interfaces.d:
#    source-directory /etc/network/interfaces.d
#    
#    auto lo
#    iface lo inet loopback
#    iface eth0 inet dhcp
#    
#    allow-hotplug wlan0
#    auto wlan0
#    iface wlan0 inet manual
#    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
#    
#    #iface wlan0 inet dhcp
#    #    wpa-ssid "****"
#    #    wpa-psk "***********"
#    
#    #allow-hotplug wlan1
#    #iface wlan1 inet manual
#    #wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
#
# /etc/wpa_supplicant/wpa_supplicant.conf:
#    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#    update_config=1
#    
#    network={
#           	ssid="****"
#           	scan_ssid=1
#           	psk="***********"
#           	proto=RSN
#           	key_mgmt=WPA-PSK
#    }
#    
#    network={
#           	ssid="AndroidAP"
#           	scan_ssid=1
#           	psk="************"
#           	proto=RSN
#           	key_mgmt=WPA-PSK
#    }

# Ad-Hoc network for configuration:
# Refer to https://spin.atomicobject.com/2013/04/22/raspberry-pi-wireless-communication/
# Do not forget the DHCP part (package dhcp3-server from the tutorial is deprecated)
# DHCP server:
# sudo apt-get install isc-dhcp-server
# sudo vim /etc/dhcp/dhcpd.conf
#   default-lease-time 600;
#   max-lease-time 7200;
#   option subnet-mask 255.255.255.0;
#   option broadcast-address 192.168.1.255;
#   #option routers 192.168.1.254;
#   option domain-name-servers 192.168.1.1;
#   option domain-name "mydomain.example";
#   
#   subnet 192.168.1.0 netmask 255.255.255.0 {
#     range 192.168.1.10 192.168.1.10;
#   } 
# sudo service isc-dhcp-server restart
# sudo service isc-dhcp-server start
# sudo service isc-dhcp-server stop 

# For auto start at boot time:
# sudo vim /etc/rc.local
# add the following line (before the exit command)
# sudo su - pi -c "cd /home/pi/ofek/SoundDrive/; python Main.py &"
# It is important to add the & at the end as this is a never ending script
# It is also important to run as pi and not as root

# ** Intermittent BT sound stops bug: **
# Experiments:
#    1) Refer to: https://www.bitpi.co/2015/02/14/prevent-raspberry-pi-from-sleeping/
#    2) Also did this and not sure if it helps: https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=35054
#    3) in /etc/pulse/default.pa - commented out package 'load-module module-suspend-on-idle'
#       refer to: https://dbader.org/blog/crackle-free-audio-on-the-raspberry-pi-with-mpd-and-pulseaudio
#       "tsched=0"
#       --> This actually made things worse and pausing the playback did not clear the hcidump so I was not able to
#           perform commands that involved more than a single click
#       (reverted)
#    4) Need to try and disable hcidump to see if this is causing the sound stops
#       To get the ip address: os.system("ifconfig | grep -A 1 wlan0 | grep 'inet addr:' | cut -d':' -f2 | cut -d' ' -f1")
#    5) Tried this: https://fedoraproject.org/wiki/How_to_debug_PulseAudio_problems
#    6) Tried to change settings in /etc/pulse/daemon.conf
#       cpu-limit was changed from no to yes (reverted to no)
#       realtime-priority was changed from 5 to 8 (remained)
#    7) Checking the system log "cat /var/log/syslog* | grep -i pulse"
#       This shows a lot of good information including the skips od pulseaudio
#    8) Updated bluez 'sudo apt-get upgrade bluez'
#       then checked the version with "dpkg --status bluez | grep '^Version:'" OR "bluetoothd -v"
#    9) Updated Alsa - 'sudo apt-get upgrade alsa-utils' AND 'sudo apt-get upgrade alsa-oss' AND 'sudo apt-get upgrade libasound2'
#    10) Changed /etc/asound.conf to be as written in the end of this page:
#        https://github.com/raspberrypi/firmware/issues/62
#    11) tried configuring according to 'https://www.raspberrypi.org/forums/viewtopic.php?t=68779'
#    12) tried to edit '/etc/pulse/daemon.conf' with cpu-limit=yes and realtime-priority=8 again but without the ';'
#
# Track Information Display
# Apparently it is done using AVRCP and not A2DP
# https://www.raspberrypi.org/forums/viewtopic.php?p=635509#p635509
# https://www.reddit.com/r/raspberry_pi/comments/2mpliz/for_all_of_you_that_used_my_incar_bluetooth_guide/
# might need to get bluetooth-player to list the players, because '/org/bluez/hci0/dev_...' specified in the
# previous link is not working
# sudo cat /var/lib/bluetooth/00:1A:7D:DA:71:13/27:76:46:A7:54:BF/info
# OK, to find the path to the device I used cat /var/log/syslog* | grep "org/" and found "/org/bluez/hci0/dev_27_76_46_A7_54_BF/fd2" (fd0 and fd1 also)
# So far I got 'dbus-send --system --type=method_call --print-reply --dest=org.bluez /org/bluez/hci0/dev_27_76_46_A7_54_BF/fd2 \ org.bluez.MediaPlayer1.Stop'
# But this fails. Saw in 'https://bugs.launchpad.net/ubuntu/+source/hwinfo/+bug/775542' suggest to install 'hal' package, but this did not help
#

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
import RPi.GPIO as GPIO  # PIR
import filecmp

# ******
# Consts
# ======
config_file_name = "sound_drive.cfg"
time_string = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
curr_log_file_dir = "logs"
curr_log_file_path = curr_log_file_dir + '/output_' + time_string + '.log'
last_log_file_name = 'output.log'
logs_retention = 30


# =================
# Private Functions
# +++++++++++++++++

def toggleAdHocMode(isAdHocMode):
	interfaces_file_to_use = ""
	if isAdHocMode:
		os.system("sudo service isc-dhcp-server start")
		interfaces_file_to_use = "interfaces_ad_hoc"
	else:
		os.system("sudo service isc-dhcp-server stop")
		interfaces_file_to_use = "interfaces_regular"
	
	if filecmp.cmp("/etc/network/interfaces", interfaces_file_to_use):
		logging.debug("Interfaces file is not changed, skipping interface restart...")
		return
		
	if not isAdHocMode:
		logging.debug("Removing local address [192.168.1.1] to renew DHCP lease")
		os.system("sudo ip address del 192.168.1.1/24 dev wlan0")  # renew DHCP lease
	time.sleep(1.0)
	os.system("sudo cp " + interfaces_file_to_use + " /etc/network/interfaces")
	time.sleep(1.0)
	os.system("sudo ifdown wlan0 --force")
	time.sleep(2.0)
	os.system("sudo ifup wlan0 --force")
	time.sleep(2.0)
	logging.debug("Ad-hoc mode configured. Rebooting...")
	os.system("sudo reboot")
	return


def adHocModeListen():
    logging.debug("Detecting ad-hoc mode...")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    input_pin = 11
    GPIO.setup(input_pin, GPIO.OUT)
    GPIO.output(input_pin, 0)
    GPIO.setup(input_pin, GPIO.IN)
    timestamp_first_on = 0
    val = GPIO.input(input_pin)
    if val == 1:
        timestamp_first_on = int(time.time())
        # Wait for val to be 1 for 6 seconds
        while int(time.time()) - 6 < timestamp_first_on:
            val = GPIO.input(input_pin)
            logging.debug("6 seconds.... " + str(val))
            if val == 0:
                timestamp_first_on = 0
                break
            time.sleep(0.1)
        if timestamp_first_on > 0:
            logging.debug("Switching to ad-hoc mode...")
            toggleAdHocMode(True)
            return
    logging.debug("Continuing in regular mode...")
    toggleAdHocMode(False)


def play_info_sound(sound_file):
    bt_connected_sound_pipe = Popen(['mplayer', '-quiet', '-ao', 'pulse', '{0}'.format(sound_file)], stdin=PIPE, stdout=PIPE)


def apply_log_retention(logs_retention):
    cutoff = time.time() - (logs_retention * 86400)
    log_files = os.listdir(curr_log_file_dir)
    for log_file in log_files:
        log_file_path = curr_log_file_dir + "/" + log_file
        if os.path.isfile(log_file_path):
            t = os.stat(log_file_path)
            c = t.st_ctime

            # delete file if older than 30 days
            if c < cutoff:
                logging.debug("Removing old log file [" + log_file_path + "]")
                os.remove(log_file_path)


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
    

def perform_cmd():
    global button_press_arr
    global curr_song_play_pipe
    global curr_song_index
    global curr_song_play_thread
    global is_song_playing
    global shutdown_pi
    global new_cmd_under_way
    global keep_current_song_index
    global curr_song_start_ts
    global hcidump_enabled

    time.sleep(2.0)  # Better use less, but for Skoda this was optimal
    logging.debug("button_press_arr " + str(button_press_arr))
    new_cmd_under_way = True

    # Add the following to debug the button clicks
    #new_cmd_under_way = False
    #del button_press_arr[:]
    #return

    if len(button_press_arr) == 1 and button_press_arr[0] == "PREV":
        # Pause current song
        logging.debug("BT command: PAUSE")
        try:
            curr_song_play_pipe.stdin.write('p')
        except:
            logging.debug("No song is being played at the moment")
    elif len(button_press_arr) == 1 and button_press_arr[0] == "NEXT":
        # Next song
        logging.debug("BT command: NEXT")
        try:
            curr_song_play_pipe.stdin.write('q')
        except:
            logging.debug("No song is being played at the moment")
        if curr_song_play_thread.is_alive():
            is_song_playing = False
    elif len(button_press_arr) == 2 and button_press_arr[0] == "NEXT" and button_press_arr[1] == "NEXT":
        start_sync_playlist_thread()
    elif len(button_press_arr) == 2 and button_press_arr[0] == "PREV" and button_press_arr[1] == "PREV":
        # Previous song
        logging.debug("BT command: PREV")
        logging.debug(str(time.time()) + " <-> " + str(curr_song_start_ts + 5.0))
        if time.time() < curr_song_start_ts + 10.0:  # 10 seconds
            curr_song_index -= 1

        if curr_song_play_thread.is_alive():
            keep_current_song_index = True
            try:
                curr_song_play_pipe.stdin.write('q')
            except:
                logging.debug("No song is being played at the moment")
    elif len(button_press_arr) == 3 and button_press_arr[0] == "PREV" and button_press_arr[1] == "PREV" and button_press_arr[2] == "PREV":
        # Shutdown Pi
        logging.debug("BT command: SHUTDOWN")
        shutdown_pi = True
        is_song_playing = False
        logging.debug("Requested to shutdown, bye bye!")
        os.system("sudo shutdown -h now")
        return
    elif len(button_press_arr) == 2 and button_press_arr[0] == "PREV" and button_press_arr[1] == "NEXT":
        logging.debug("BT command: RESTART_PLAYLIST")
        curr_song_index = 0

        if curr_song_play_thread.is_alive():
            keep_current_song_index = True
            try:
                curr_song_play_pipe.stdin.write('q')
            except:
                logging.debug("No song is being played at the moment")
    elif len(button_press_arr) == 2 and button_press_arr[0] == "NEXT" and button_press_arr[1] == "PREV":
        logging.debug("BT command: DISABLE_HCIDUMP")
        hcidump_enabled = False
    else:
        logging.debug("Unrecognized BT command")
    new_cmd_under_way = False
    del button_press_arr[:]

# General code to print the relevant BT mutimedia buttons presses:
def detect_bt_mm_press():
    global button_press_arr
    global curr_song_play_pipe
    global curr_song_index
    global curr_song_play_thread
    global is_song_playing
    global shutdown_pi
    global new_cmd_under_way
    global hcidump_enabled

    logging.debug("Listening to BT multimedia key presses")
    mm_press_re = re.compile(r'^.{50}')

    perform_cmd_thread = None
    new_cmd_under_way = False
    button_press_arr = []
    # The following takes too much CPU usage to parse every line:
    #proc = Popen(['sudo', 'hcidump', '--raw', '-i', 'hci0'], stdout=PIPE)
    #for line in iter(gproc.stdout.readline, ''):
    # The folowing is not good as when the hcidump recognizes that is it pieped to
    # another process and not to stdout, it then buffers the data
    #proc = Popen(['sudo', 'hcidump', '--raw', '-i', 'hci0'], stdout=PIPE, stdin=PIPE)
    #gproc = Popen(['grep', '-e', r"^>.\{{{0},\}}".format("50")], stdin=proc.stdout, stdout=PIPE)
    #for line in iter(gproc.stdout.readline, ''):
    # The solution is to use Pexpect
    from hcidump import Hcidump
    hcidump = Hcidump()
    while hcidump_enabled:
        line = hcidump.get_output()
        line = line[0].strip()
        if curr_song_play_pipe != None and len(line) == 50 and mm_press_re.match(line) != None:
            logging.debug(line)
            if raw_prev_re.match(line) != None:
                logging.debug("Button pressed: prev")
                if not new_cmd_under_way:
                    button_press_arr.append("PREV")
            if raw_next_re.match(line) != None:
                logging.debug("Button pressed: next")
                if not new_cmd_under_way:
                    button_press_arr.append("NEXT")
            if perform_cmd_thread == None or not perform_cmd_thread.is_alive():
                # Start perform_cmd thread
                logging.debug("cmd start!")
                perform_cmd_thread = Thread(target=perform_cmd)
                perform_cmd_thread.start()
    logging.debug("Stopped hcidump thread")
    os.system("sudo killall hcidump")
    play_info_sound("sync_failed_01.mp3")  # TODO: remove this
    
    
def play_songs():
    global curr_song_play_pipe
    global curr_song_index
    global is_song_playing
    global shutdown_pi
    global keep_current_song_index
    global curr_song_start_ts
    logging.debug("play-songs-thread has started")

    if len(songs) == 0:
        logging.debug("No songs exist, trying to synch playlist...")
        # Sync playlist
        sync_playlist()
        if len(songs) == 0:
            logging.debug("Could not synch playlist or the playlist is empty, aborting...")
            exit(1)

    while True:
        time.sleep(1)
        curr_song_index = curr_song_index % len(songs)  # Loop over the playlist
        song = songs[curr_song_index]
        song_file_name = song['video_id'] + ".mp3"
        song_file_path = playlist_path + "/" + song_file_name
        song_file_path = unicode(song_file_path).encode('utf8')
        logging.debug("Playing " + song['title'] + "... path to song [" + song_file_path + "]")
        curr_song_play_pipe = Popen(['mplayer', '-quiet', '-ao', 'pulse', '{0}'.format(song_file_path)], stdin=PIPE, stdout=PIPE)
        curr_song_start_ts = time.time()
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

        if not keep_current_song_index:
            curr_song_index += 1
        # Reset flag to default value
        keep_current_song_index = False
		
        # Write this to the global config file
        config.set('playback', 'last_played_song_index', curr_song_index)
        save_global_config(config)


def sync_playlist():
    global songs
    global curr_song_index
    global keep_current_song_index
    global is_song_playing
    global curr_song_play_pipe
    global playlist_id

    if not internet_on():
        # Sound taken from http://soundbible.com/1540-Computer-Error-Alert.html
        play_info_sound("sync_failed_01.mp3")
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
    play_info_sound("sync_started_01.mp3")
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
        	play_info_sound("sync_failed_01.mp3")
        	exit(1)
        # Retrieve the playlist id
        playlist_id = get_playlist_id(youtube, playlist_name)
        if playlist_id == None or len(playlist_id) == 0:
        	logging.debug("ERROR: Could not get playlist ID for playlist [" + playlist_name + "]")
        	play_info_sound("sync_failed_01.mp3")
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
        song_file = song['video_id'] + ".mp3"
        if song_file in files:
            logging.debug("File [" + song_file + "] already exists.")
        else:
            if isVideoAvailable(youtube, song['video_id']):
                logging.debug("Marked YouTube song [" + song['video_id'] + "] for download")
                yt_vids_to_download.append(youtube_video_url_prefix + song['video_id'])
            else:
                logging.debug("Video [" + song['title'] + "] with id [" + song['video_id'] + "] is not available")

    yt_vids_to_delete = []
    needed_song_files = [song['video_id'] + ".mp3" for song in songs]
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

        curr_song_index = 0
        if curr_song_play_thread.is_alive():
            logging.debug("Playing updated playlist from start")
            keep_current_song_index = True # Prevents +1 to the currently set index in the play_songs thread
            is_song_playing = False

    # Sound taken from https://appraw.com/ringtone/cool-notification-2-qjmxk
    play_info_sound("sync_finished_01.mp3")

    
# Send message to phone using GCM - for debug purposes
def sendNotification(message):
    url = "https://android.googleapis.com/gcm/send"
    app_key = "AIzaSyD5uehR9NXaiuGKIEmbJWkMUY3Y23d0XNE"

    json_data = {"data": {"message": message}, "to": "/topics/global"}

    headers = {'Content-Type': 'application/json', 'Authorization': 'key=' + app_key}
    data =  json.dumps(json_data)

    req = urllib2.Request(url, data, headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())

    logging.debug("Rsponse: " + str(response))

    reply = {}
    if 'message_id' in response:
        reply['error'] = '0'
        logging.debug('Message sent!')
    elif 'error' in response:
        reply['error'] = '1'
        logging.debug('Counld not send the message')

    f.close()
      

# **********
# youtube_dl
# ==========
# sudo pip install youtube-dl
# Important to update! use 'sudo pip install -U youtube-dl' for that
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
        

# ****************
# Flask web server
# ================
# refer to https://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972
# requires 'sudo pip install flask' or 'sudo apt-get python-flask'
from flask import Flask, render_template
app = Flask(__name__)

def executeCommand(commandName):
	global button_press_arr
	global hcidump_enabled
	global bt_dump_therad
	
	#button_press_arr = []
	
	print "command received " + commandName
	logging.debug("Received command [" + commandName + "] from Flask webserver")
	
	if commandName == "NEXT":
		button_press_arr.append("NEXT")
		logging.debug("arr: " + str(button_press_arr))
		perform_cmd()
	elif commandName == "PAUSE":
		button_press_arr.append("PREV")
		perform_cmd()
	elif commandName == "PREV":
		button_press_arr.append("PREV")
		button_press_arr.append("PREV")
		perform_cmd()
	elif commandName == "REWIND":
		button_press_arr.append("PREV")
		button_press_arr.append("NEXT")
		perform_cmd()
	elif commandName == "SYNC":
		start_sync_playlist_thread()
	elif commandName == "SHUTDOWN":
		button_press_arr.append("PREV")
		button_press_arr.append("PREV")   
		button_press_arr.append("PREV")   
		perform_cmd() 
	elif commandName == "DISABLE_HCIDUMP":
		hcidump_enabled = False
	elif commandName == "ENABLE_HCIDUMP":
		if hcidump_enabled == True:
			logging.debug("hcidump is already active")
			return
		# TODO: this code is duplicated
		# Create a thread to listen to BT multimedia key presses
		hcidump_enabled = True
		logging.debug("Starting mm bt listen tread")
		bt_dump_therad = Thread(target=detect_bt_mm_press)
		#bt_dump_therad.daemon = True
		bt_dump_therad.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")
    
@app.route('/showHome', methods=['GET', 'POST'])
def showHome():
    return render_template("index.html")
    
@app.route('/showControls', methods=['GET', 'POST'])
def showControls():
    return render_template("controls.html")

@app.route('/next', methods=['GET', 'POST'])
def next():
    executeCommand("NEXT")
    return render_template("controls.html")
    
@app.route('/pause', methods=['GET', 'POST'])
def pause():
    executeCommand("PAUSE")
    return render_template("controls.html")
    
@app.route('/prev', methods=['GET', 'POST'])
def prev():
    executeCommand("PREV")
    return render_template("controls.html")
    
@app.route('/rewind', methods=['GET', 'POST'])
def rewind():
    executeCommand("REWIND")
    return render_template("controls.html")
    
@app.route('/sync', methods=['GET', 'POST'])
def sync():
    executeCommand("SYNC")
    return render_template("controls.html")
    
@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    executeCommand("SHUTDOWN")
    return render_template("controls.html")
    
@app.route('/disableHcidump', methods=['GET', 'POST'])
def disableHcidump():
    executeCommand("DISABLE_HCIDUMP")
    return render_template("controls.html")
    
@app.route('/enableHcidump', methods=['GET', 'POST'])
def enableHcidump():
    executeCommand("ENABLE_HCIDUMP")
    return render_template("controls.html")

# Will be executed from a thread
def start_webserver():
    app.run(host='0.0.0.0', port=8080, debug=False)


# **************
# Initialization
# ==============

# Prevent Pi from sleeping (TODO: not sure if this helps)
# Refer to: https://www.bitpi.co/2015/02/14/prevent-raspberry-pi-from-sleeping/
# Also did this and not sure if it helps: https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=35054
os.system("setterm -blank 0 -powerdown 0")

config = ConfigParser.RawConfigParser()

# Create the logs dir if needed
if not os.path.isdir(curr_log_file_dir):
    os.makedirs(curr_log_file_dir)
# Create a log file for this run
logging.basicConfig(filename=curr_log_file_path, level=logging.DEBUG)
# Create a symbolic link for easy access to the last log file
symlink_force(curr_log_file_path, last_log_file_name)
apply_log_retention(logs_retention)

logging.debug('Starting SoundDrive... [' + time_string + ']')

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
    
# Starting flask webserver
if __name__ == "__main__":  # TODO: is this needed
	adHocModeListen()

	logging.debug("Starting Flask webserver...")
	webserver_therad = Thread(target=start_webserver)
	#webserver_therad.daemon = True
	webserver_therad.start()


# ****
# Main
# ====

# Get important config fields
playlist_name = config.get('youtube', 'playlist_name')
playlist_id = config.get('youtube', 'playlist_id')
songs = eval(config.get('youtube', 'playlist'))
curr_song_index = config.getint('playback', 'last_played_song_index')
if songs != None and len(songs) != 0:
    curr_song_index = curr_song_index % len(songs)  # Just to be on the safe side
bt_device_names = eval(config.get('bluetooth', 'device_names'))
logging.debug("Allowed device names: " + str(bt_device_names))

# Fields deduced from config
playlist_path = "playlists/" + playlist_name

# Create playlist folder if needed
if not os.path.isdir(playlist_path):
    os.makedirs(playlist_path)

logging.debug("Playlist name [" + playlist_name + "]")
logging.debug("==")

# Print songs summary
for song in songs:
    logging.debug("    Title [" + song['title'] + "] video_id [" + song['video_id'] + "]")
logging.debug("Total of [" + str(len(songs)) + "] songs")


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

logging.debug('Starting pulseaudio daemon...')
# must use 'sudo adduser root pulse-access' first
os.system("su - pi -c \"pulseaudio -D\"")
time.sleep(3)
logging.debug('pulseaudio daemon started')

logging.debug('BT section start')

# Contributed code to 'https://gist.github.com/egorf/66d88056a9d703928f93/forks'
from bluetoothctl import Bluetoothctl
time_between_scans = 5;  # Seconds
max_num_of_attempts_to_scan = 30

bt = Bluetoothctl()
bt.start_scan()
bt_mac = None
scan_attempt_num = 0

# Figure out current connection state
conn_success = False
if bt.is_connected():
    logging.debug("BT is already connected")
    conn_success = True

while not conn_success:
    devices = bt.get_connectable_devices()
    logging.debug("Devices near by " + str(devices))
    devMap = {}
    devList = []
    for dev in devices:
        devMap[dev['name']] = dev['mac_address'];
        devList.append(dev['name'])

    pairable_devices = list(set(bt_device_names).intersection(devList))
    logging.debug("intersection: " + str(pairable_devices))
    if "AP5037" in pairable_devices:
        # Prefer the test device
        pairable_devices = ["AP5037"]
    if len(pairable_devices) == 1:
        bt_device_name = pairable_devices[0]
        logging.debug("Found pairable device [" + bt_device_name + "]")
        bt_mac = devMap[bt_device_name]
        # To find if already Connected
        # subprocess.check_output("hcitool con")

        logging.debug('trying to connect to [' + bt_device_name + ']')

        logging.debug("Starting agent device...")
        result = bt.start_agent()
        logging.debug("Agent started")

        logging.debug("Starting default-agent...")
        result = bt.default_agent()
        logging.debug("Default-agent started")

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
        logging.debug("Could not find devices " + str(bt_device_names) + " searching again in [" + str(time_between_scans) + "] seconds")
        scan_attempt_num += 1
        if scan_attempt_num > max_num_of_attempts_to_scan:
            logging.debug("Could not find devices " + str(bt_device_names) + " total number of attempts was [" + str(max_num_of_attempts_to_scan) + "] aborting...")
            os.system("sudo shutdown -h now")
        time.sleep(time_between_scans)

# Beep sound taken from 'http://www.soundjay.com/beep-sounds-3.html'
time.sleep(3)
play_info_sound("bt_connect_01.wav")
logging.debug('BT end')
hcidump_wait = 0
while True:
    if bt.is_connected():
        logging.debug("Connection verified by hcidump")
        break;
    time.sleep(1)
    hcidump_wait += 1
    if hcidump_wait > 20:
        break;

# This is crucial to get things working in Skoda! Need to wait ~15 seconds before starting.
if hcidump_wait < 20:
    time.sleep(20 - hcidump_wait)
play_info_sound("bt_connect_01.wav")
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

# Another important thing to do is to add a module to /etc/pulse/deafult.pa:
# load-module module-switch-on-connect
# This will change the device to BT when it is connected
# for more information refer to: https://wiki.debian.org/BluetoothUser/a2dp

curr_song_play_pipe = None
is_song_playing = True

# raw_play_re = re.compile(r"^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C C4 00|^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C C6 00") # AP
raw_prev_re = re.compile(r"^(?:[0-9,A-F]{2} ){10}11 0E 00 48 7C 4C 00") # SKODA
# raw_next_re = re.compile(r"^> (?:[0-9,A-F]{2} ){8}00 40 11 0E 00 48 7C CB 00")
raw_next_re = re.compile(r"^(?:[0-9,A-F]{2} ){10}11 0E 00 48 7C 4B 00") # SKODA

# Create a thread to listen to BT multimedia key presses
hcidump_enabled = True
logging.debug("Starting mm bt listen tread")
bt_dump_therad = Thread(target=detect_bt_mm_press)
#bt_dump_therad.daemon = True
bt_dump_therad.start()

# BT mm button press detection
new_cmd_under_way = False
button_press_arr = []

# Play the first song
curr_song_start_ts = 0.0
is_song_playing = False
shutdown_pi = False
keep_current_song_index = False
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
