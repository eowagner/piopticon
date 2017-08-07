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

import smtplib

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
# local_dir = "/home/pi/code/piopticon/" # Should probably get by system call--relative addresses do not work if the prog starts on boot

conf = json.load(open(local_dir + "config.json"))

subject = 'piopticon motion detected'  
body = ''

email_text = """\  
From: %s  
To: %s  
Subject: %s

%s
""" % (conf['gmail_user'], conf['send_to'], subject, body)

parser = argparse.ArgumentParser()
parser.add_argument('-showvideo', action="store_true", default=False)
args = vars(parser.parse_args())

print "Waiting for wifi..."
time.sleep(conf['start_delay'])

dbx = dropbox.Dropbox(conf["dropbox_token"])
try:
    dbx.users_get_current_account()
except AuthError as err:
    sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

time.sleep(conf["camera_warmup_time"])

avg = None
lastUploaded = datetime.datetime.now()
lastTexted = datetime.datetime.now()
motionCounter = 0

try:
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = f.array

        timestamp = datetime.datetime.now()
        motion = False

        if conf["resize_to"] != 0:
            frame = imutils.resize(frame, width=conf["resize_to"])
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if avg is None:
            print "Captured Background"
            #avg = gray
            avg = gray.copy().astype("float")
            rawCapture.truncate(0)
            continue

        cv2.accumulateWeighted(gray, avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
        #frameDelta = cv2.absdiff(avg, gray)

        thresh = cv2.threshold(frameDelta, conf['delta_thresh'], 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        (_, contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if cv2.contourArea(c) < conf['min_contour_area']:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            motion = True

        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        if motion:
            if motionCounter >= conf['min_motion_frames']:
                motionCounter = 0

                if (timestamp - lastTexted).seconds >= conf['min_text_seconds']:
                    try:
                        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    			server.ehlo()
    			server.login(conf['gmail_user'], conf['gmail_password'])
    			server.sendmail(conf['gmail_user'], conf['send_to'], email_text)
    			server.close()
    			print('Email sent!')
			lastTexted = timestamp;
		    except:  
    			print('Something went wrong...')

                if (timestamp - lastUploaded).seconds >= conf['min_upload_seconds']:
                    lastUploaded = timestamp

                    name = "{}.jpg".format(timestamp.strftime("%I:%M:%S%p"))
                    localName = local_dir+name
                    dbxName = "/{}/{}".format(timestamp.strftime("%Y-%B-%d"), name)
                    cv2.imwrite(localName, frame)

                    with open(localName, 'r') as f:
                        # We use WriteMode=overwrite to make sure that the settings in the file
                        # are changed on upload
                        print("Uploading " + name + " to Dropbox as " + dbxName + "...")
                        try:
                            dbx.files_upload(f, dbxName, mode=WriteMode('overwrite'))
                        except ApiError as err:
                            client.messages.create(
                                to = conf["destination_number"],
                                from_= conf["origin_number"],
                                body = "Piopticon Dropbox Error!"
                             )
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
