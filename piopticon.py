from picamera.array import PiRGBArray
from picamera import PiCamera
import imutils
import cv2

import datetime
import time

min_upload_seconds = 3.0
min_motion_frames = 8
camera_warmup_time = .2
delta_thresh = 5
min_area = 5000

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=(640, 480))

time.sleep(camera_warmup_time)

avg = None

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = f.array

    timestamp = datetime.datetime.now()
    text = "Unoccupied"

    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if avg is None:
        print "Starting background model"
        #avg = gray
        avg = gray.copy().astype("float")
        rawCapture.truncate(0)
        continue

    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    #frameDelta = cv2.absdiff(avg, gray)    

    thresh = cv2.threshold(frameDelta, delta_thresh, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    (_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    

    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue	
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        text = "Occupied"

    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(frame, "Room Status: {}".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    cv2.imshow("Security Feed", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

    rawCapture.truncate(0)
