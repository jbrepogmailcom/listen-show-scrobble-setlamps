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
from selenium.webdriver.chrome.service import Service
import sys
import pylast
from io import BytesIO
from collections import Counter
import statistics
from colorthief import ColorThief
import numpy as np
import requests
import code
import paho.mqtt.client as mqtt
import json
import pdb

def apply_linear_correction(x, y):
    # Hypothetical correction factors

    #  translates color from (0.313, 0.329) to 0.323,0.482

    
    ax = 1.0  # Placeholder, adjust based on calibration
    bx = 0.01/0.313  # Adjust to shift x towards 0.323
    ay = 1.0  # Placeholder, adjust based on calibration
    by = 0.153/0.329  # Adjust to shift y towards 0.482

    x_new = ax * x + bx * x
    y_new = ay * y + by * y

    return x_new, y_new

def rgb_to_cie1931(red, green, blue):
    # Normalize the red, green, blue values
    red_normalized = red / 255
    green_normalized = green / 255
    blue_normalized = blue / 255

    # Apply gamma correction
    red_corrected = (red_normalized / 12.92) if (red_normalized <= 0.04045) else ((red_normalized + 0.055) / 1.055) ** 2.4
    green_corrected = (green_normalized / 12.92) if (green_normalized <= 0.04045) else ((green_normalized + 0.055) / 1.055) ** 2.4
    blue_corrected = (blue_normalized / 12.92) if (blue_normalized <= 0.04045) else ((blue_normalized + 0.055) / 1.055) ** 2.4

    # Convert to XYZ space
    X = red_corrected * 0.649926 + green_corrected * 0.103455 + blue_corrected * 0.197109
    Y = red_corrected * 0.234327 + green_corrected * 0.743075 + blue_corrected * 0.022598
    Z = red_corrected * 0.0000000 + green_corrected * 0.053077 + blue_corrected * 1.035763

    # Convert to xy space
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

    return x, y

def control_light(correction_factor, light_sensor_name, red, green, blue):
    # Calculate x and y from RGB

    if correction_factor == 1:
      red = red * 0.74

    if correction_factor == 2:
      red = red * 0.74
      blue = blue * 1.8
      green = green * 1.3  
    

    x, y = rgb_to_cie1931(red, green, blue)
    #x, y = apply_linear_correction(xtmp,ytmp)

    # Define the MQTT server settings
    mqtt_server = "IP"
    mqtt_port = 1883
    mqtt_user = ""
    mqtt_password = ""
    mqtt_timeout = 60  # Ensure timeout is set correctly

    # Calculate brightness from the RGB values (simple average for demonstration)
    brightness = 0.1 * (red + green + blue) // 3

    # Create the payload to set the color and brightness
    payload = {
        "state": "ON",
        "brightness": brightness,
        "color": {
            "x": round(x, 3),
            "y": round(y, 3)
            }
        }

    print(f"MQTT payload: {payload}")

    # Initialize the MQTT client
    client = mqtt.Client()

    # Set the username and password
    client.username_pw_set(username=mqtt_user, password=mqtt_password)

    # Connect to the MQTT server
    print(f"Connecting to MQTT server {mqtt_server}:{mqtt_port} with timeout {mqtt_timeout}")
    client.connect(mqtt_server, mqtt_port, mqtt_timeout)

    # Start the loop
    client.loop_start()

    # Send the payload
    client.publish(f"zigbee2mqttjb3/{light_sensor_name}/set", json.dumps(payload))

    # Stop the loop and disconnect
    client.loop_stop()
    client.disconnect()


API_KEY = "lastfm_api_key"
API_SECRET = "lastfm_api_secret"
USERNAME = "lastfm_user"
PASSWORD = "lastfm_pw"

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
volume_threshold = 1500
count_is_silent = 0

#get hardware of microphone:
#string=$(arecord -l | awk '/\[USB PnP Sound Device]/{print}')

script = """
string=$(arecord -l | awk '/\[ATR4697-USB]/{print}')
a=${string#card }    # remove "card " from the beginning of the string
a=${a%%:*}           # remove everything after the first colon
b=${string#*device } # remove everything before "device "
b=${b%%:*}           # remove everything after the first colon
d=$(echo "hw:$a,$b")
echo $d
"""
output_bytes = subprocess.check_output(script, shell=True)
hardware_str = output_bytes.decode()
hardware_str = hardware_str.replace("\n", "")
print(f"Microphone at {hardware_str}")

#Even if error

undetected = 0

def start_browser_in_kiosk_mode(url):
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

    service = Service("/usr/local/bin/chromedriver")
    print("Initializing Chrome WebDriver...")
    browser = webdriver.Chrome(service=service, options=option)
    print("Chrome WebDriver initialized successfully.")
    browser.get(url)
    return browser

#run forever
while True:

	# Even with error
	try:
		
		# Download sample
		#os.system('arecord -r 44100 -d 10 -c 2 -t wav --device="hw:0,0"  /mnt/ramdisk/test-mic.wav')	
		#os.system(f'arecord -d 10 -D {hardware_str} -r 44100 -c 1  /mnt/ramdisk/test-mic.wav')
		os.system(f'arecord -d 10 -D {hardware_str} -r 44100 -c 1  /mnt/ramdisk/test-mic.wav')
		# arecord -d 10 -r 44100 -c 1 

		# Get volume
		from pydub import AudioSegment
		sound = AudioSegment.from_file("/mnt/ramdisk/test-mic.wav", format="wav")
		maxvolume = sound.max
		is_silent = (maxvolume < volume_threshold)
		print("Max volume detected: ",maxvolume,"  Is silent?",is_silent)


		#quit()
		# Get song
		if not(is_silent):
			ftr = open('/mnt/ramdisk/test-mic.wav', 'rb').read()
			shazam = Shazam(ftr)
			recognize_generator = shazam.recognizeSong()
			try:
				resp_shazam = next(recognize_generator)	
				resp2 = resp_shazam[1]
			except:
				resp2 = " "	
		else:
			resp2 = " "
			#os.popen("killall chromium")
			#os.popen("killall chromedriver")

		# Get values
		#resp2 = resp_shazam[1]
		#print(resp2)
		#print("Length:")
		#print(len(resp2))
		#print("end.")
		
		selected_color = 1  # assume you will get the color
		
		if len(resp2) > 5 or is_silent:
			if not(is_silent):
				name = resp2["track"]["title"]		
				artist = resp2["track"]["subtitle"]
				coverurl = resp2["track"]["images"]["coverarthq"]
				offset = resp2["matches"][0]["offset"]	
				count_is_silent = 0
			else:
				name = "No sound"
				artist = ""
				count_is_silent = count_is_silent + 1

			print("#################### ", artist, ": ", name, "###################")
			#pdb.set_trace()  # Start the debugger here

			if (name == prevname) and (len(name) > 0):
				correctscrobbles = correctscrobbles + 1		
			prevname = name		
			
			# Get image
			if not(is_silent):
				urllib.request.urlretrieve(coverurl, "/mnt/ramdisk/albumimage.jpg")
			
			# If no music copy over default image
			if is_silent:
				os.popen('cp '+homepath+"/nosound.jpg /mnt/ramdisk/albumimage.jpg")			

			# Compose html
			htp1 = Path(homepath+"/songhtml1.html").read_text()
			htp2 = Path(homepath+"/songhtml2.html").read_text()
			ht_whole = htp1 + artist + "<br>" + name + htp2
			#Path(homepath + '/songhtml.html').write_text(ht_whole)
			Path('/mnt/ramdisk/songhtml.html').write_text(ht_whole)
			# Open browser and display file
			if firstloop == 1:
				#pdb.set_trace()  # Start the debugger here
				browser = start_browser_in_kiosk_mode('file:///mnt/ramdisk/songhtml.html')
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
			if not(is_silent):
				resp = requests.get(coverurl)
				assert resp.ok
				img = Image.open(BytesIO(resp.content))
			
				img2 = ImageOps.posterize(img.convert('RGB'), bits=4)
			
				img2.save("/mnt/ramdisk/albumimage.jpg")
			
			img4 = ColorThief("/mnt/ramdisk/albumimage.jpg")
			
			dominant_color = img4.get_color(quality=1)
			
			vr,vb,vg = dominant_color
			#print(type(dominant_color))
			print("Dominant color: ",vr,vb,vg)
			#print("Resp: ",resp,", TYPE: ",type(resp))
			
			list_of_colors = [[255,255,255],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[0,255,255],[255,143,191],[255,215,0],[255,0,255],[255,127,80]]
			ha_list_of_colors = [[0,0,127],[0,0,255],[0,127,0],[0,127,127],[0,127,255],[0,255,0],[0,255,127],[0,255,255],[127,2,2],[127,0,127],[127,0,255],[127,127,0],[127,127,255],[127,255,0],[127,255,127],[127,255,255],[255,2,2],[255,0,127],[255,0,255],[255,127,0],[255,127,127],[255,127,255],[255,255,0],[255,255,127]]
			color = [vr,vb,vg]
			
			def closest(colors,color):
				color = np.array(color)
				return color.reshape(1, -1)   # Return true color
				"""
				colors = np.array(colors)
				color = np.array(color)
				distances = np.sqrt(np.sum((colors-color)**2,axis=1))
				index_of_smallest = np.where(distances==np.amin(distances))
				smallest_distance = colors[index_of_smallest]
				return smallest_distance
				"""
			
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
			

			# Set lamps
			if (count_is_silent < 2):
				control_light(1,"Z-Lampa art deco (240203)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))
				control_light(2,"Z-Lampa žlutá (240203)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))
				control_light(3,"Z-RGB LED pasek (gauc)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))
	
			#Scrobble now playing
			if not(is_silent):
				network = pylast.LastFMNetwork(api_key = API_KEY, api_secret = API_SECRET, username = USERNAME, password_hash = pylast.md5(PASSWORD))
				network.update_now_playing(artist = artist, title = name)
		
		else:
			print("Nothing found...")	
			#code.interact(local=locals()) 	
			name = ""
			artist = ""			
			
		#Scrobble last played
		if (lasttrack != name) and not(is_silent):
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
					     			
	except Exception as e: 
		if isinstance(e, BdbQuit):
			raise		
		pass
		print(f"Error: {e}")
		#code.interact(local=locals())
		#quit()



