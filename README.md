# piopticon

A lightweight security camera using OpenCV that runs on a Raspberry Pi.

Constantly records video, and if significant motion is detected it sends an alert using gmail and uploads a photo to dropbox.



To run on a Raspberry Pi at startup:

 sudo nano ~/.config/lxsession/LXDE-pi/autostart

 and add the following line:

 @lxterminal -e "/home/pi/code/piopticon/piopticon.py"

