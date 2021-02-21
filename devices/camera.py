#!/bin/python3
# coding: utf-8

'''
DESCRIPTION:

Python script that recognizes faces from a camera from a encoding file
The encoding file is created separately by analyzing presaved images
If a face is not saved in the encoding it will be labelled as unknown

'''

# Recognition modules
import face_recognition
import imutils
import pickle
import time
import cv2
import os

# Other modules
import tkinter as tk
import sys
import PIL
from PIL import Image
from PIL import ImageTk
import time
import random
import numpy as np

import multiprocessing as mp

import device_communicator as dc



class Controls(tk.Frame):
    def __init__(self):
        super().__init__(parent)
        pass


class Frame_Image(tk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent)
        bg1 = "#00A8B3"
        self.config(bg=bg1)
        self.config(width=650)
        self.config(height=500)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)  # Prevents resizing


class Frame_Info(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        bg1 = "grey"
        wid = 225
        self.config(bg=bg1)
        self.config(width=wid)
        self.config(height=500)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)  # Prevents resizing

        ''' Adding list parameters '''
        L_name = tk.Label(self, text="Camera Settings", bg=bg1)
        F0 = tk.Frame(self, height=3, width = wid/2+20, bg="black")
        F1 = tk.Frame(self, height=3, width = wid/2+20, bg="white")
        L_fr = tk.Label(self, text="Frame Rate", bg=bg1)
        L_frv = tk.Label(self, textvariable=parent.frame_rate)  # Frame Rate Variable

        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        for i in range(21):
            self.rowconfigure(i, pad=cc)
        self.configure(padx=cc)     # Check this !!!

        ''' Placing parameters '''
        L_name.grid(column=0, columnspan=2, row=0, sticky="new")
        F0.grid(column=0, row=1, pady=10, sticky="we")
        F1.grid(column=1, row=1, sticky="we")
        L_fr.grid(column=0, row=5, sticky="e")
        L_frv.grid(column=1, row=5, sticky="w")



class MainApp_Camera(tk.Tk):
    def __init__(self, parent=None, title="default",
            conf=False, kq=None, chc=None, dq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf
        self.chc = chc

        self.geometry("+700+100")
        self.title(title)

        ''' Setting variables '''
        self.frame_rate = tk.DoubleVar()
        self.frame_rate.set(-1)

        self.sent_time = 0
        self.new_time = 15
        self.time_differential = 15

        ''' Setting Frames '''
        self.ImageFrame = Frame_Image(self)
        self.FrameInfo = Frame_Info(self)

        self.ImageFrame.grid(column=0, row=0)
        self.FrameInfo.grid(column=1, row=0, sticky="ns")

        self.canvas = tk.Canvas(self.ImageFrame, width=640, height=480)
        self.canvas.pack(side="left", padx=10, pady=10)

        # Hardware and Communication
        if conf:
            self.protocol("WM_DELETE_WINDOW", lambda:None)
            self.kq = kq
            self.dq = dq    # detection queue
            self.comm_agent = dc.Dev_Communicator()
        else:
            self.protocol("WM_DELETE_WINDOW", self.on_quit)
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            os.chdir("..")
        self.capture_device = VideoCapture(video_source=0, parent=self)

        self.initialization()
        self.update_GUI()
        self.mainloop()

    def initialization(self):
        my_init = {
                'position':'+800+70',
                'update':5,
        }
        for k, v in my_init.items():
            try: my_init[k] = self.conf[k]
            except KeyError: pass               # missing key in CONFIG
            except AttributeError: pass         # no CONFIG at all...running solo
            except TypeError: pass              # conf=None

        # Assigning variables
        self.geometry(my_init['position'])
        self.delay = int(my_init['update'])

    def update_GUI(self):
        self.fr  = self.capture_device.get_frame_rate()
        self.frame_rate.set(round(self.fr, 3))
        answer, frame, name, or_frame = self.capture_device.recognition()
        ###
        if answer:
            self.frame_array = frame    # create array from frame
            self.image = PIL.Image.fromarray(frame)
            self.photo = PIL.ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)  # GUI
        # COMMUNICATOR
        if not self.kq.empty():
            string_received = self.kq.get()
            print("Camera: Received {} from kill_queue!".format(string_received))
            self.on_quit()
        ###
        if self.conf:
            if name and (self.time_differential <= 0):
                self.comm_agent.Camera_detect_queue(self.dq, name)
                self.comm_agent.Camera_detect_queue(self.dq, or_frame)
                self.sent_time = time.time()
                self.new_time = self.sent_time + 15
            else:
                pass
        else:
            pass    # Running alone
        self.time_differential = self.new_time - time.time()
        self.after(self.delay, self.update_GUI)

    def on_quit(self):
        self.capture_device.release_video()
        print("CAMERA: Camera device successfully released ... closing...")
        self.destroy()



class VideoCapture():
    def __init__(self, video_source=0, parent=None):
        self.parent = parent
        self.cascPath = "haarcascade_frontalface_default.xml"
#        self.enc_data = 'face_enc'
        self.faceCascade = cv2.CascadeClassifier(self.cascPath)
        # load the known faces and embeddings saved in the last file
#        self.data = pickle.loads(open(self.enc_data, "rb").read())
        self.video_cap = cv2.VideoCapture(video_source)
        ''' If camera doesn't start, abandon process '''
        if not self.video_cap.isOpened():
            raise ValueError("Unable to open video...", video_source)
        ''' Video image size '''
        self.picx = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.picy = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("CAMERA: Image Size: {} x {}". format(self.picx, self.picy))
        self.frame_counter()
        self.encoder_data()

    def encoder_data(self):
        self.list = os.listdir('encodings')
        self.nof = len(self.list)    # number of files

    def frame_counter(self):
        self.frame_counter = 0
        self.f_old = 0
        self.t_old = time.time()
        self.frate = -1
        self.images = np.zeros((2, self.picy, self.picx))

    def get_frame_rate(self):
        if self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if ret:
                frame_np = np.array(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), np.float)
                frame_np = frame_np[np.newaxis,:,:]
                self.frame_counter += 1
                idx = self.frame_counter % 2
                self.images[idx:idx+1,:,:] = frame_np
                time_diff = time.time() - self.t_old
                if (time_diff) > 0.5:
                    self.frate = (self.frame_counter - self.f_old) / time_diff
                    self.f_old = self.frame_counter
                    self.t_old = time.time()
                return self.frate
            else:
                return self.frate
        else: return None

    def recognition(self):
        self.encoder_data()
        ret, frame = self.video_cap.read()
        orig_frame = frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.faceCascade.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5,
                                             minSize = (60, 60))
        # convert from BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        names = []
        '''Loop over facial embeddings in case we have multiple embeddings for multiple faces '''
        name = None
        matches = False
        for encoding in encodings:
            for n in range(self.nof):
                encdata = 'encodings/' + str(self.list[n])
                self.data = pickle.loads(open(encdata, "rb").read())
                matches = face_recognition.compare_faces(self.data["encodings"], encoding)
            # If no matches !!!
            name = "Unknown"
            if matches == False:
                break
            else:
                if True in matches:
                    # Find positions at which we get True and store them
                    matchedIdxs = [i for (i,b) in enumerate(matches) if b]
                    counts = {}
                    for i in matchedIdxs:
                        name = self.data["names"][i]
                        counts[name] = counts.get(name, 0) + 1
                    name = max(counts, key = counts.get)
                # Update the list of the names
                names.append(name)
                # Loop over the recognized faces
                for((x,y,w,h), name) in zip(self.faces, names):
                    '''Rescale the face coordinates, draw the predicted face name on the image'''
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        return ret, frame, name, rgb


    def release_video(self):
        if self.video_cap.isOpened():
            self.video_cap.release()



# MAIN BODY
def main():
    root_camera = MainApp_Camera(
            parent = None,
            title = "Camera (PID: {})".format(os.getpid()),
            conf = None,
            kq = None,
            chc = None,
            dq = None
            )

def my_dev(conf_sect, kill_queue, child_comm, detect_queue):
    root_camera = MainApp_Camera(
            parent = None,
            title = "CHILD: Camera",
            conf = conf_sect,
            kq = kill_queue,
            chc = child_comm,
            dq = detect_queue
            )

if __name__ == "__main__":
    main()

# EOF
