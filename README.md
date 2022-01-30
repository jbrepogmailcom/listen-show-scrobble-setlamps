# listen-show-scrobble
Python script that listens by microphone what you play, obtains track details from Shazam, displays fullscreen album art and scrobbles to last.fm

<h1>Installation:</h1>

<ul>
<li>download all files to home directory</li>
<li>install all necessary libraries in #includes</li>
<li>get last.fm API key and secret and fill it into py code</li>
<li>allow listen-loop.sh to run: sudo chmod +x listen-loop.sh</li>
<li>install chromium and get proper location by whereis chromium and modify py script if necessary</li>
</ul>

the script is not failproof, it may end with error if no image is provided by shazam, therefore it is better to run it in loop by ./listen-loop.sh

