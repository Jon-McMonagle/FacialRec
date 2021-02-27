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
        self.new_time = 15
        self.time_differential = 15
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
            ''' Facial Recognition statement '''
            if not self.dq.empty():
                self.encoder_data()
                init_frame = self.dq.get()
                # Convert from BGR to RGB
                rgb = cv2.cvtColor(init_frame, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(rgb)
                names = []
                ## Loop over facial embeddings in case of mutliple emeddings for faces
                name = None
                matches = False
                for encoding in encodings:
                    for n in range(self.nof):
                        encdata = 'encodings/' + str(self.list[n])
                        self.data = pickle.loads(open(encdata, "rb").read())
                        matches = face_recognition.compare_faces(self.data["encodings"],
                            encoding)
                    ## If No matches:
                    name = "Unknown person"
                    if matches == False:
                        pass
                    else:
                        gray = cv2.cvtColor(init_frame, cv2.COLOR_BGR2GRAY)
                        faces = self.faceCascade.detectMultiScale(gray, scaleFactor = 1.1,
                            minNeighbors = 5, minSize = (60,60))
                        ## Find positions at which we get True and store them
                        matchedIdxs = [i for (i,b) in enumerate(matches) if b]
                        counts = {}
                        for i in matchedIdxs:
                            name = self.data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        name = max(counts, key = counts.get)
                    names.append(name) # Update the list of names
                    ## Loop over the recognized faces
#                   for((x,y,w,h), name) in zip(faces, names):
#                      ''' Rescale the face coordinates and add name to image of face '''
#                       cv2.rectangle(init_frame, (x,y), (x+w, y+h), (0,255,0), 2)
#                       cv2.putText(init_frame, name, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
#                           (0,255,0), 2)
                if self.conf:
                    if name and (self.time_differential <=0):
                        self.comm_agent.Email_info_queue(self.eq, name)
                        self.comm_agent.Email_info_queue(self.eq, rgb)
                        self.sent_time = time.time()
                        self.new_time = self.sent_time + 15
                    else:
                        pass
                else:
                    pass # Running alone
            if not self.kq.empty():
                  string_received = self.kq.get()
                  print("Recognition: Received {} from kill_queue.".format(string_received))
                  self.on_quit()
            self.time_differential = self.new_time - time.time()

    def on_quit(self):
        print("Recognition: Qutting..")
        self.run_update = False
        print("Recognition: Emptying pipe...")
        while not self.dq.empty():
            cleanup = self.dq.get()



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
