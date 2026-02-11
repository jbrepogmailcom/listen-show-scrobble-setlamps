from ShazamAPI import Shazam
import subprocess
import os
import time
import urllib.request
from PIL import Image, ImageOps, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

from bdb import BdbQuit
from pathlib import Path
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import pylast
from io import BytesIO
import numpy as np
from colorthief import ColorThief
import requests
import paho.mqtt.client as mqtt
import json


def apply_linear_correction(x, y):
    # Hypothetical correction factors
    ax = 1.0
    bx = 0.01 / 0.313
    ay = 1.0
    by = 0.153 / 0.329

    x_new = ax * x + bx * x
    y_new = ay * y + by * y
    return x_new, y_new


def rgb_to_cie1931(red, green, blue):
    # Normalize the red, green, blue values
    red_normalized = red / 255
    green_normalized = green / 255
    blue_normalized = blue / 255

    # Apply gamma correction
    red_corrected = (
        red_normalized / 12.92
        if (red_normalized <= 0.04045)
        else ((red_normalized + 0.055) / 1.055) ** 2.4
    )
    green_corrected = (
        green_normalized / 12.92
        if (green_normalized <= 0.04045)
        else ((green_normalized + 0.055) / 1.055) ** 2.4
    )
    blue_corrected = (
        blue_normalized / 12.92
        if (blue_normalized <= 0.04045)
        else ((blue_normalized + 0.055) / 1.055) ** 2.4
    )

    X = (
        red_corrected * 0.649926
        + green_corrected * 0.103455
        + blue_corrected * 0.197109
    )
    Y = (
        red_corrected * 0.234327
        + green_corrected * 0.743075
        + blue_corrected * 0.022598
    )
    Z = red_corrected * 0.0 + green_corrected * 0.053077 + blue_corrected * 1.035763

    denom = X + Y + Z
    if denom == 0:
        denom = 1e-9
    x = X / denom
    y = Y / denom

    return x, y


def control_light(correction_factor, light_sensor_name, red, green, blue):
    if correction_factor == 1:
        red = red * 0.74
    if correction_factor == 2:
        red = red * 0.74
        blue = blue * 1.8
        green = green * 1.3

    x, y = rgb_to_cie1931(red, green, blue)

    mqtt_server = os.getenv("MQTT_SERVER", "your_mqtt_server_address")
    mqtt_port = 1883
    mqtt_user = os.getenv("MQTT_USER", "your_mqtt_username")
    mqtt_password = os.getenv("MQTT_PASSWORD", "your_mqtt_password")
    mqtt_timeout = 60

    brightness = 0.1 * (red + green + blue) // 3

    payload = {
        "state": "ON",
        "brightness": brightness,
        "color": {"x": round(x, 3), "y": round(y, 3)},
    }

    print(f"MQTT payload: {payload}")

    client = mqtt.Client()
    client.username_pw_set(username=mqtt_user, password=mqtt_password)
    client.connect(mqtt_server, mqtt_port, mqtt_timeout)
    client.loop_start()
    client.publish(f"zigbee2mqttjb3/{light_sensor_name}/set", json.dumps(payload))
    client.loop_stop()
    client.disconnect()


API_KEY = os.getenv("LASTFM_API_KEY", "your_lastfm_api_key")
API_SECRET = os.getenv("LASTFM_API_SECRET", "your_lastfm_api_secret")
USERNAME = os.getenv("LASTFM_USERNAME", "your_lastfm_username")
PASSWORD = os.getenv("LASTFM_PASSWORD", "your_lastfm_password")

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
lastdisplayed = ""
volume_threshold = 1500
count_is_silent = 0

# get hardware of microphone
script = '''
string=$(arecord -l | awk '/\[ATR4697-USB]/{print}')
a=${string#card }
a=${a%%:*}
b=${string#*device }
b=${b%%:*}
d=$(echo "hw:$a,$b")
echo $d
'''
output_bytes = subprocess.check_output(script, shell=True)
hardware_str = output_bytes.decode().strip()
print(f"Microphone at {hardware_str}")


def start_browser_in_kiosk_mode(url):
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--kiosk")
    opts.add_argument("--disable-password-manager-reauthentication")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-notifications")
    opts.add_experimental_option("excludeSwitches", ["load-extension", "enable-automation"])

    # First try explicit system chromedriver path
    service = Service("/usr/local/bin/chromedriver")
    print("Initializing Chrome WebDriver (system chromedriver)...")
    try:
        browser = webdriver.Chrome(service=service, options=opts)
        print("Chrome WebDriver initialized successfully (system chromedriver).")
        browser.get(url)
        return browser
    except WebDriverException as e:
        msg = str(e)
        print(f"Chrome WebDriver start failed: {msg}")

    # If we get here, try webdriver-manager fallback if available
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("Attempting to install a matching chromedriver via webdriver-manager...")
        service2 = Service(ChromeDriverManager().install())
        browser = webdriver.Chrome(service=service2, options=opts)
        print("Chrome WebDriver initialized successfully (webdriver-manager).")
        browser.get(url)
        return browser
    except Exception as e:
        print(f"webdriver-manager fallback failed or not available: {e}")

    # Final guidance
    print("Could not start Chrome WebDriver.")
    print("If you see a ChromeDriver/Chrome version mismatch, either:")
    print("  - Install a chromedriver that matches your Chrome version (e.g. download matching chromedriver and place at /usr/local/bin/chromedriver)")
    print("  - Or install webdriver-manager in the Python environment: pip install webdriver-manager")
    raise RuntimeError("Chrome WebDriver start failed; see messages above.")


def closest_color_for_ha(color):
    # placeholder: return the color itself in expected shape
    color = np.array(color)
    return color.reshape(1, -1)


while True:
    try:
        cmd1 = "sudo find /tmp -maxdepth 1 -type d -name '.com.google.Chrome*' -print0 | xargs -0 rm -rf"
        cmd2 = "sudo find /tmp -maxdepth 1 -type d -name '.org.chromium*' -print0 | xargs -0 rm -rf"
        subprocess.run(cmd1, shell=True, check=True)
        subprocess.run(cmd2, shell=True, check=True)

        os.system(f'arecord -d 10 -D {hardware_str} -r 44100 -c 1  /mnt/ramdisk/test-mic.wav')

        from pydub import AudioSegment
        sound = AudioSegment.from_file("/mnt/ramdisk/test-mic.wav", format="wav")
        maxvolume = sound.max
        is_silent = (maxvolume < volume_threshold)
        print("Max volume detected:", maxvolume, "Is silent?", is_silent)

        if not is_silent:
            ftr = open('/mnt/ramdisk/test-mic.wav', 'rb').read()
            shazam = Shazam(ftr)
            recognize_generator = shazam.recognizeSong()
            try:
                resp_shazam = next(recognize_generator)
                resp2 = resp_shazam[1]
            except Exception:
                resp2 = " "
        else:
            resp2 = " "

        if len(resp2) > 5 or is_silent:
            if not is_silent:
                name = resp2["track"]["title"]
                artist = resp2["track"]["subtitle"]
                coverurl = resp2["track"]["images"]["coverarthq"]
                offset = resp2["matches"][0]["offset"]
                count_is_silent = 0
            else:
                name = "No sound"
                artist = ""
                count_is_silent = count_is_silent + 1

            print("####################", artist, ":", name, "###################")

            if (name == prevname) and (len(name) > 0):
                correctscrobbles = correctscrobbles + 1
            prevname = name

            if not is_silent:
                urllib.request.urlretrieve(coverurl, "/mnt/ramdisk/albumimage.jpg")
            if is_silent:
                os.popen('cp ' + homepath + "/nosound.jpg /mnt/ramdisk/albumimage.jpg")

            htp1 = Path(homepath + "/songhtml1.html").read_text()
            htp2 = Path(homepath + "/songhtml2.html").read_text()
            ht_whole = htp1 + artist + "<br>" + name + htp2
            Path('/mnt/ramdisk/songhtml.html').write_text(ht_whole)

            if firstloop == 1:
                browser = start_browser_in_kiosk_mode('file:///mnt/ramdisk/songhtml.html')
                firstloop = 0
                anythingplayed = 1
                timestart = time.time()
                lastoffset = offset
                lastdisplayed = name
            else:
                if (lasttrack != name) and (lastdisplayed != name):
                    lastoffset = offset
                    browser.refresh()
                    lastdisplayed = name

            if not is_silent:
                resp = requests.get(coverurl)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content))
                img2 = ImageOps.posterize(img.convert('RGB'), bits=4)
                img2.save("/mnt/ramdisk/albumimage.jpg")

            img4 = ColorThief("/mnt/ramdisk/albumimage.jpg")
            dominant_color = img4.get_color(quality=1)
            vr, vb, vg = dominant_color
            print("Dominant color:", vr, vb, vg)

            closest_color = closest_color_for_ha([vr, vb, vg])
            print("Closest color:", closest_color)

            if (count_is_silent < 2):
                control_light(1, "Z-Lampa art deco (240203)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))
                control_light(2, "Z-Lampa žlutá (240203)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))
                control_light(3, "Z-RGB LED pasek (gauc)", int(closest_color[0][0]), int(closest_color[0][1]), int(closest_color[0][2]))

            if not is_silent:
                network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=USERNAME, password_hash=pylast.md5(PASSWORD))
                network.update_now_playing(artist=artist, title=name)

        else:
            print("Nothing found...")
            name = ""
            artist = ""

        if (lasttrack != name) and not is_silent:
            timenow = time.time()
            if (
                correctscrobbles > 2
                and anythingplayed == 1
                and lastscrobbled != lasttrack
                and len(lasttrack) > 0
                and (timenow - timestart) > 180
            ):
                print("Scrobbling last track:", lasttrack)
                trackstart = timenow - lastoffset
                network.scrobble(artist=lastartist, title=lasttrack, timestamp=trackstart)
                lastscrobbled = lasttrack

    except Exception as e:
        if isinstance(e, BdbQuit):
            raise
        print(f"Error: {e}")
        time.sleep(1)
        continue



