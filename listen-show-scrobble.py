from ShazamAPI import Shazam
import subprocess
import os
import time
import urllib.request
from PIL import Image
from pathlib import Path
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import pylast

API_KEY = "c30532eb25c2bd740d0251d692e1f09f"
API_SECRET = "918479efb57abff6e23db0209f234914"
USERNAME = "janbenes"
PASSWORD = "Jb842652+"

homepath = os.path.expanduser("~")

firstloop = 1
lasttrack = ""
lastartist = ""
timestart = time.time()
anythingplayed = 0
name = ""
lastscrobbled = ""

#run forever
while True:
	
	# Download sample
	os.system('arecord -r 44100 -d 10 -t wav --device="hw:0,0"  '+homepath+'/test-mic.wav')	
	
	# Get song
	ftr = open(homepath+'/test-mic.wav', 'rb').read()
	shazam = Shazam(ftr)
	recognize_generator = shazam.recognizeSong()
	resp = next(recognize_generator)
	
	# Get values
	resp2 = resp[1]
	print(resp2)
	#print("Length:")
	#print(len(resp2))
	#print("end.")
	
	if len(resp2) > 5:
		name = resp2["track"]["title"]		
		artist = resp2["track"]["subtitle"]
		coverurl = resp2["track"]["images"]["coverarthq"]
		
		# Get image
		urllib.request.urlretrieve(coverurl, homepath+"/albumimage.jpg")
		
		# Compose html
		htp1 = Path(homepath+"/songhtml1.html").read_text()
		htp2 = Path(homepath+"/songhtml2.html").read_text()
		ht_whole = htp1 + artist + "<br>" + name + htp2
		Path(homepath+'/songhtml.html').write_text(ht_whole)
		
		# Open browser and display file
		if firstloop == 1:
			option = Options()
			option.add_argument("--start-maximized")
			option.add_argument("--no-sandbox")
			option.add_argument("--disable-web-security")
			option.add_argument("--ignore-certificate-errors")
			option.add_argument("--kiosk")
			option.add_argument("--disable-password-manager-reauthentication")
			option.add_argument("--disable-infobars")
			option.add_argument("--disable-notifications")
			option.add_experimental_option('excludeSwitches', ['load-extension', 'enable-automation'])			
			browser = webdriver.Chrome("/snap/bin/chromium.chromedriver",0,option)
			browser.get('file://'+homepath+'/songhtml.html')
			firstloop = 0
			anythingplayed = 1
			timestart = time.time()	
		else:
			if lasttrack != name:
				timestart = time.time
				browser.refresh()

		#Scrobble now playing
		network = pylast.LastFMNetwork(api_key = API_KEY, api_secret = API_SECRET, username = USERNAME, password_hash = pylast.md5(PASSWORD))
		network.update_now_playing(artist = artist, title = name)
	
	else:
		print("Nothing found...")		
		name = ""
		artist = ""			
		
	#Scrobble last played
	if lasttrack != name:
		timenow = time.time()
		if (anythingplayed == 1) and (lastscrobbled != lasttrack) and (len(lasttrack) > 0) and ((timenow - timestart) > 180):
			#print("Scrobbling last track: ",lasttrack)
			network.scrobble(artist = lastartist, title = lasttrack, timestamp = timestart)
			lastscrobbled = lasttrack
			timestart = time.time()	
		lasttrack = name
		lastartist = artist
				     			
		