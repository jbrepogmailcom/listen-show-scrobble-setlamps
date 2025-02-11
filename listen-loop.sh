#!/bin/bash

sudo mkdir /mnt/ramdisk
sudo mount -t tmpfs -o rw,size=5M tmpfs /mnt/ramdisk
sudo chmod 777 /mnt/ramdisk

while true
do
  #python3 /home/janbenes/listen-show-scrobble-setlamps-new-zigbee.py
  python3 /home/janbenes/listen-show-scrobble-setlamps-new-zigbee-realcolors.py
  killall chrome
  killall chromium
  killall chromedriver
  sleep 5
done

