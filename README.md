# listen-show-scrobble
Python script that listens by microphone what you play, obtains track details from Shazam, displays fullscreen album art, scrobbles to last.fm and sets color of lamps connected to Home Assistant.
<br>HTML page is optimized only for 1920x1080 resolution. If you want to use it on other display then change songhtml1.html

<h1>Installation:</h1>

<ul>
<li>download all files to home directory</li>
<li>install all necessary libraries in #includes</li>
<li>get last.fm API key and secret and fill it into py code</li>
<li>get authorization key from Home Assistant and codes of entities you want to control and insert it to code</li>  
<li>listen-loop.sh wrapper directs temporary sound captures to ramdisk and performs sanity clean and restart if there is error</li>
<li>install chromium and get proper location by whereis chromium and modify py script if necessary</li>
</ul>

You may need to adjust line with arecord. Either parameter with correct device may be needed by adding -d "hw:0,0" or similar, or you may need to set microphone as default recording device, or you may need to adjust recording rate in parameter -r. Please do not ask about it, I cannot support. It took me lot of experimenting to get it working for my particular configuration.

Run script as python3 ./listen-show-scrobble-setlamps.py

<strike>the script is not failproof, it may end with error if no image is provided by shazam, therefore it is better to run it in loop by ./listen-loop.sh</strike>

