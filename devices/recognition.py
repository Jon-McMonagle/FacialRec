# !/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========

Python script to receive images from the camera and process them for
facial recongition to reduce load on camera and increase frame rate
of camera.
Will process without a GUI

'''

# Modules required for recognition
import face_recognition
import imutils
import pickle

# Modules for blur detection
from imutils import paths

# Modules for general purpose and image processing
import time
import os
import cv2
import tkinter as tk
import sys
import PIL
from PIL import Image
from PIL import ImageTk
import random
import numpy as np

import multiprocessing as mp
import device_communicator as dc



class Controls(tk.Frame):
    def __init__(self):
        super().__init__(parent)
        pass



class MainApp_Recog():
    def __init__(self, parent=None, title="default",
            conf=False, kq=None,  dq=None, eq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf

        ''' Setting required variables '''
        self.sent_time = 0
        self.new_time = time.time()
        self.run_update = True

        # Hardware and Communication
        if conf:
            self.kq = kq
            self.dq = dq
            self.eq = eq    # EMAIL QUEUE
            self.comm_agent = dc.Dev_Communicator()
        else:
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            self.eq = mp.Queue()    # EMAIL QUEUE
            os.chdir("..")
            self.run_update = False

        ''' Setting Recognition parameters '''
        cascPath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascPath)

        self.initialization()
        self.encoder_data()
        self.update_loop()

    def initialization(self):
        my_init = {
            'position':'+0+0',
        }
        for k, v in my_init.items():
            try: my_init[k] = self.conf[k]
            except KeyError: pass
            except AttributeError: pass
            except TypeError: pass

    def encoder_data(self):
        self.list = os.listdir('encodings')
        self.nof = len(self.list) # number of files

    def update_loop(self):
        while self.run_update:
            if not self.kq.empty():
                  string_received = self.kq.get()
                  print("Recognition: Received {} from kill_queue.".format(string_received))
                  self.on_quit()
            if self.new_time <= time.time():
                if not self.dq.empty():
                    init_frame = self.dq.get()
                    if len(init_frame) > 0:
                        blur_test = cv2.Laplacian(init_frame, cv2.CV_64F).var()
                        if blur_test > 40:     # VALUE TO ADJUST TO CHANGE BLUR DETECTION
                            self.fullframe = init_frame
                            small_frame = cv2.resize(init_frame, (0, 0), fx=0.70, fy=0.70)
                            self.facial_recognition(small_frame)
            if self.new_time > time.time():
                if not self.dq.empty():
                    cleanup = self.dq.get()

    def facial_recognition(self, frame):
        self.encoder_data()
        # Convert from BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        capture_encodings = face_recognition.face_encodings(rgb)
        name = None
        matches = False
        if capture_encodings:
            for n in range(self.nof):
                encdata = 'encodings/' + str(self.list[n])
                self.data = pickle.loads(open(encdata, "rb").read())
                for encoding in capture_encodings:
                    matches = face_recognition.compare_faces(self.data["encodings"],
                        encoding)
                    if True in matches:
                        matchedIdxs = [i for (i,b) in enumerate(matches) if b]
                        name = self.data["names"][0]
                        break
                    else:
                        name = "Unknown person"
                if True in matches:
                    break
            if self.nof == 0:
                name = "Unknown person"
            if self.conf:
                if name:
                    self.new_time = time.time() + 15
                    self.comm_agent.Email_info_queue(self.eq, name)
                    self.comm_agent.Email_info_queue(self.eq, self.fullframe)
                else:
                    pass
            else:
                pass # Running alone

    def on_quit(self):
        print("RECOGNITION: PID: {}".format(os.getpid()))
        print("Recognition: Qutting..")
        self.run_update = False
        #print("Recognition: Emptying pipe...")
        #while not self.dq.empty():
        #    cleanup = self.dq.get()



# MAIN
def main():
    root_recog = MainApp_Recog(
            parent = None,
            title = "Recognition",
            conf = None,
            kq = None,
            dq = None,
            eq = None
            )

def my_dev(conf_sect, kill_queue, detect_queue, email_queue):
    root_recog = MainApp_Recog(
            parent = None,
            title = "CHILD: Recog",
            conf = conf_sect,
            kq = kill_queue,
            dq = detect_queue,
            eq = email_queue
            )

if __name__ == "__main__":
    main()

#EOF
