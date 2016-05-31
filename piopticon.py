#!/usr/bin/python

from picamera.array import PiRGBArray
from picamera import PiCamera
import imutils
import cv2

import sys
import os
import datetime
import time

import json
import argparse

import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from twilio.rest import TwilioRestClient

conf = json.load(open("config.json"))

min_text_seconds = 3600
min_upload_seconds = 3.0
min_motion_frames = 8
camera_warmup_time = 2
delta_thresh = 5
min_area = 5000

parser = argparse.ArgumentParser()
parser.add_argument('-showvideo', action="store_true", default=False)
args = vars(parser.parse_args())

client = TwilioRestClient(conf["twilio_sid"], conf["twilio_token"])

dbx = dropbox.Dropbox(conf["dropbox_token"])
try:
    dbx.users_get_current_account()
except AuthError as err:
    sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=(640, 480))

time.sleep(camera_warmup_time)

avg = None
lastUploaded = datetime.datetime.now()
lastTexted = datetime.datetime.now()
motionCounter = 0

try:
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = f.array

        timestamp = datetime.datetime.now()
        motion = False

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
            motion = True

        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        if motion:
            if motionCounter >= min_motion_frames:
                motionCounter = 0

                if (timestamp - lastTexted).seconds >= min_text_seconds:
                    client.messages.create(
                        to="4404768415",
                        from_="+12164506265",
                        body="Motion Detected"
                    )
                    lastTexted = timestamp

                if (timestamp - lastUploaded).seconds >= min_upload_seconds:
                    lastUploaded = timestamp

                    localName = "{}.jpg".format(timestamp.strftime("%I:%M:%S%p"))
                    # dbxName = "/"+localName
                    dbxName = "/{}/{}".format(timestamp.strftime("%Y-%B-%d"), localName)
                    cv2.imwrite(localName, frame)

                    with open(localName, 'r') as f:
                        # We use WriteMode=overwrite to make sure that the settings in the file
                        # are changed on upload
                        print("Uploading " + localName + " to Dropbox as " + dbxName + "...")
                        try:
                            dbx.files_upload(f, dbxName, mode=WriteMode('overwrite'))
                        except ApiError as err:
                            # This checks for the specific error where a user doesn't have
                            # enough Dropbox space quota to upload this file
                            if err.error.is_path() and err.error.get_path().error.is_insufficient_space():
                                sys.exit("ERROR: Cannot back up; insufficient space.")
                            elif err.user_message_text:
                                print(err.user_message_text)
                                sys.exit()
                            else:
                                print(err)
                                sys.exit()

                    os.remove(localName)

            else:
                motionCounter += 1

        if args['showvideo']:
            cv2.imshow("Security Feed", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        rawCapture.truncate(0)

except KeyboardInterrupt:
    print "exiting"
    rawCapture.truncate(0)
