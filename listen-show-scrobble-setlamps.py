from ShazamAPI import Shazam
import subprocess
import os
import time
import urllib.request
from PIL import Image, ImageOps
from pathlib import Path
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import pylast
from io import BytesIO
from collections import Counter
import statistics
from colorthief import ColorThief
import numpy as np
import json
import requests

API_KEY = "___________"
API_SECRET = "____________"
USERNAME = "_________"
PASSWORD = "_________"

homepath = os.path.expanduser("~")

firstloop = 1
lasttrack = ""
lastartist = ""
timestart = time.time()
anythingplayed = 0
name = ""
lastscrobbled = ""
offset = 0
lastoffset = 0
correctscrobbles = 0
prevname = ""
album_url_old = ""
lapse_timer = 0
lastdisplayed =""

#Even if error

#run forever
while True:

	# Even with error
	try:
		
		# Download sample
		os.system('arecord -r 44100 -d 10 -t wav --device="hw:0,0"  '+homepath+'/test-mic.wav')	
		
		# Get song
		ftr = open(homepath+'/test-mic.wav', 'rb').read()
		shazam = Shazam(ftr)
		recognize_generator = shazam.recognizeSong()
		resp_shazam = next(recognize_generator)
		
		# Get values
		resp2 = resp_shazam[1]
		#print(resp2)
		#print("Length:")
		#print(len(resp2))
		#print("end.")
		
		selected_color = 1  # assume you will get the color
		
		if len(resp2) > 5:
			name = resp2["track"]["title"]		
			artist = resp2["track"]["subtitle"]
			coverurl = resp2["track"]["images"]["coverarthq"]
			offset = resp2["matches"][0]["offset"]		
			print("#################### ",artist,": ",name,"###################")		
			if (name == prevname) and (len(name) > 0):
				correctscrobbles = correctscrobbles + 1		
			prevname = name		
			
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
				
				# Close all previously open windows
				handles = browser.window_handles
				size = len(handles)
				#for x in range(size):
	 			#	driver.switch_to.window(handles[x])
				#	print(driver.title)
				if size > 0:
					browser.close()
	
				browser = webdriver.Chrome("/snap/bin/chromium.chromedriver",0,option)
				browser.get('file://'+homepath+'/songhtml.html')
				firstloop = 0
				anythingplayed = 1
				timestart = time.time()	
				lastoffset = offset
				lastdisplayed = name
			else:
				if (lasttrack != name) and (lastdisplayed != name):
					lastoffset = offset
					#timestart = time.time()
					browser.refresh()
					lastdisplayed = name
	
	      #Set lamps
			resp = requests.get(coverurl)
			assert resp.ok
			img = Image.open(BytesIO(resp.content))
			
			img2 = ImageOps.posterize(img.convert('RGB'), bits=4)
			
			img2.save(homepath+"/albumimage.jpg")
			
			img4 = ColorThief(homepath+"/albumimage.jpg")
			
			dominant_color = img4.get_color(quality=1)
			
			vr,vb,vg = dominant_color
			#print(type(dominant_color))
			print("Dominant color: ",vr,vb,vg)
			#print("Resp: ",resp,", TYPE: ",type(resp))
			
			list_of_colors = [[255,255,255],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[0,255,255],[255,143,191],[255,215,0],[255,0,255],[255,127,80]]
			ha_list_of_colors = [[0,0,127],[0,0,255],[0,127,0],[0,127,127],[0,127,255],[0,255,0],[0,255,127],[0,255,255],[127,0,0],[127,0,127],[127,0,255],[127,127,0],[127,127,255],[127,255,0],[127,255,127],[127,255,255],[255,0,0],[255,0,127],[255,0,255],[255,127,0],[255,127,127],[255,127,255],[255,255,0],[255,255,127]]
			color = [vr,vb,vg]
			
			def closest(colors,color):
				colors = np.array(colors)
				color = np.array(color)
				distances = np.sqrt(np.sum((colors-color)**2,axis=1))
				index_of_smallest = np.where(distances==np.amin(distances))
				smallest_distance = colors[index_of_smallest]
				return smallest_distance
			
			closest_color = closest(ha_list_of_colors,color) # for home assistant changed to ha_list_of_colors
			print("Closest color: ",closest_color )
			#print("Index1: ", closest_color[0][2])
			
			main_color = "pink"
			if(np.array_equal(closest_color,np.asarray([[255,255,255]]))): main_color="white"
			if(np.array_equal(closest_color,np.asarray([[255,0,0]]))): main_color="red"
			if(np.array_equal(closest_color,np.asarray([[0,255,0]]))): main_color="green"
			if(np.array_equal(closest_color,np.asarray([[0,0,255]]))): main_color="blue"
			if(np.array_equal(closest_color,np.asarray([[255,255,0]]))): main_color="yellow"
			if(np.array_equal(closest_color,np.asarray([[0,255,255]]))): main_color="cyan"
			if(np.array_equal(closest_color,np.asarray([[255,143,191]]))): main_color="pink"
			if(np.array_equal(closest_color,np.asarray([[255,215,0]]))): main_color="gold"
			if(np.array_equal(closest_color,np.asarray([[255,0,255]]))): main_color="purple"
			if(np.array_equal(closest_color,np.asarray([[255,127,80]]))): main_color="orange"
			
			ha_url = "http://_____IP ADDRESS OF YOUR HOME ASSISTANT SERVER_____:8123/api/services/light/turn_on"
			ha_headers = {"Authorization": "Bearer ________HA_AUTHORIZATION_KEY______________-fR-o", "content-type": "application/json",}
			if (selected_color == 1):
				ha_data = {"entity_id": "light.____ENTITY_1____", "rgb_color": [int(closest_color[0][0]),int(closest_color[0][1]),int(closest_color[0][2])]} # "brightness": 150}
				ha_data2 = {"entity_id": "light.____ENTITY_2____", "rgb_color": [int(closest_color[0][0]),int(closest_color[0][1]),int(closest_color[0][2])]} # "brightness": 255}
			else:
				ha_data = {"entity_id": "light.____ENTITY_1____", "rgb_color": [50,50,10],} # "brightness": 50}
				ha_data2 = {"entity_id": "light.____ENTITY_2____", "rgb_color": [50,50,10],} # "brightness": 50}
			#print("Calling "+bulb_url)
			print("Calling "+ha_url)
			print("headers: ",ha_headers)
			print("data: ",ha_data)
			ha_resp = requests.post(ha_url, headers=ha_headers, json=ha_data)
			ha_resp2 = requests.post(ha_url, headers=ha_headers, json=ha_data2)
			print(ha_resp)
	
			#Scrobble now playing
			#network = pylast.LastFMNetwork(api_key = API_KEY, api_secret = API_SECRET, username = USERNAME, password_hash = pylast.md5(PASSWORD))
			#network.update_now_playing(artist = artist, title = name)
	
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
			if (correctscrobbles > 2) and (anythingplayed == 1) and (lastscrobbled != lasttrack) and (len(lasttrack) > 0) and ((timenow - timestart) > 180):
				print("Scrobbling last track: ",lasttrack)
				trackstart = timenow - lastoffset			
				network.scrobble(artist = lastartist, title = lasttrack, timestamp = trackstart)
				lastscrobbled = lasttrack
				correctscrobbles = 0
				timestart = time.time()	
			lasttrack = name
			lastartist = artist
					     			
	except:
		print("Some error, trying again...")
			
			
