from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2

import time



camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))

time.sleep(.2)

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	frame = f.array
	
	cv2.imshow("test", frame)
	
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break

	rawCapture.truncate(0)

