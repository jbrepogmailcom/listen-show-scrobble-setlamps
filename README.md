# listen-show-scrobble
Python script that listens by microphone what you play, display fullscreen album art and scrobbles to last.fm

Installation:

download all three files
install all necessary libraries in #includes
get last.fm API key and secret and fill it into py code
allow listen-loop.sh to run: sudo chmod +x listen-loop.sh
install chromium and get proper location by whereis chromium and modify py script if necessary

the script is not failproof, it may end with error if no image is provided, therefore it is better to run it in loop by ./listen-loop.sh

