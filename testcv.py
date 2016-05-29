from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import imutils
import time
import datetime


camera = PiCamera()
rawCapture = PiRGBArray(camera)

time.sleep(0.1)

camera.capture(rawCapture, format="bgr")
image = rawCapture.array

cv2.imshow("Image", image)
cv2.waitKey(0)