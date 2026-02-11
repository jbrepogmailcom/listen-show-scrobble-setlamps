# Listen Show Scrobble Setlamps

Python script that listens through a microphone, detects the currently playing track via Shazam, displays fullscreen album art, scrobbles to Last.fm, and sets Zigbee lamp colors through Zigbee2MQTT.

The HTML template is optimized for `1920x1080`.

## Files

- `listen-show-scrobble-setlamps-new-zigbee-realcolors.py` - main script
- `listen-loop.sh` - restart/loop wrapper
- `songhtml1.html` - main fullscreen template
- `songhtml2.html` - secondary template

## Requirements

- Python 3
- Chromium + matching ChromeDriver
- ALSA (`arecord`)
- Python libraries imported by the script (install with `pip`)

## Environment Variables

Set credentials and endpoints before running:

- `LASTFM_API_KEY`
- `LASTFM_API_SECRET`
- `LASTFM_USERNAME`
- `LASTFM_PASSWORD`
- `MQTT_SERVER`
- `MQTT_USER`
- `MQTT_PASSWORD`

Example:

```bash
export LASTFM_API_KEY="..."
export LASTFM_API_SECRET="..."
export LASTFM_USERNAME="..."
export LASTFM_PASSWORD="..."
export MQTT_SERVER="10.0.0.54"
export MQTT_USER="..."
export MQTT_PASSWORD="..."
```

## Run

Direct run:

```bash
python3 ./listen-show-scrobble-setlamps-new-zigbee-realcolors.py
```

Recommended (auto-restart loop):

```bash
./listen-loop.sh
```

## Notes

- You may need to adjust the `arecord` device/rate settings for your hardware.
- If Chromium path differs, adjust it in the script.
- If you use a different screen resolution, adjust `songhtml1.html`.
