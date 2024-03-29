#!/bin/python3
# coding: utf-8

'''
DESCRIPTION:

Python script that produces a live feed from a camera and then
sends the images to the recognition module to be analyzed.

'''

import time
import cv2
import os
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


class Frame_Image(tk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent)
        bg1 = "#CE0444"
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
        bg1 = "#CE0444"
        wid = 225
        self.config(bg=bg1)
        self.config(width=wid)
        self.config(height=200)     ## CHANGE THIS IF SHOWING IMAGE TO MATCH FRAME_IMAGE
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
            conf=False, kq=None, dq=None, eq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf

        self.geometry("+1000+100")
        self.title(title)

        ''' Setting variables '''
        self.frame_rate = tk.DoubleVar()
        self.frame_rate.set(-1)
        #self.send_time = time.time() + 2

        ''' Setting Frames '''
#        self.ImageFrame = Frame_Image(self)
        self.FrameInfo = Frame_Info(self)

#        self.ImageFrame.grid(column=0, row=0)
        self.FrameInfo.grid(column=1, row=0, sticky="ns")

#        self.canvas = tk.Canvas(self.ImageFrame, width=640, height=480)
#        self.canvas.pack(side="left", padx=10, pady=10)

        # Hardware and Communication
        if conf:
            self.protocol("WM_DELETE_WINDOW", lambda:None)
            self.kq = kq    # Kill queue
            self.dq = dq    # Detection queue
            self.eq = eq    # Email queue
            self.comm_agent = dc.Dev_Communicator()
        else:
            self.protocol("WM_DELETE_WINDOW", self.on_quit)
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            self.eq = mp.Queue()
            os.chdir("..")

        self.capture_device = VideoCapture(video_source=0, parent=self)

        self.initialization()
        self.update_GUI()
        self.mainloop()

    def initialization(self):
        my_init = {
                'position':'+860+70',
                'update':20,
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
        self.fr, curr_frame, answer = self.capture_device.get_frame_rate()
        self.frame_rate.set(round(self.fr, 3))
        #Kill queue
        if not self.kq.empty():
            string_received = self.kq.get()
            print("Camera: Received {} from kill_queue!".format(string_received))
            self.on_quit()
#        if answer:
#            self.image = PIL.Image.fromarray(curr_frame)
#            self.photo = PIL.ImageTk.PhotoImage(self.image)
#            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)  # GUI
        if self.conf and self.dq.empty():
           self.comm_agent.Camera_detect_queue(self.dq, curr_frame)
        else:
           pass    # Running alone
        self.after(self.delay, self.update_GUI)

    def on_quit(self):
        self.capture_device.release_video()
        print("CAMERA: PID: {}".format(os.getpid()))
        print("Camera: Camera device successfully released ... closing...")
        self.destroy()



class VideoCapture():
    def __init__(self, video_source=0, parent=None):
        self.parent = parent
        self.video_cap = cv2.VideoCapture(video_source)
        ''' If camera doesn't start, abandon process '''
        if not self.video_cap.isOpened():
            raise ValueError("Unable to open video...", video_source)
        ''' Video image size '''
        self.picx = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.picy = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("CAMERA: Image Size: {} x {}". format(self.picx, self.picy))
        self.frame_counter()

    def frame_counter(self):
        self.frame_counter = 0
        self.f_old = 0
        self.t_old = time.time()
        self.frate = -1
        self.images = np.zeros((1, self.picy, self.picx))

    def get_frame_rate(self):
        if self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if ret:
                frame_np = np.array(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), np.float)
                frame_np = frame_np[np.newaxis,:,:]
                self.frame_counter += 1
                idx = self.frame_counter % 1
                self.images[idx:idx+1,:,:] = frame_np
                time_diff = time.time() - self.t_old
                if (time_diff) > 0.5:
                    self.frate = (self.frame_counter - self.f_old) / time_diff
                    self.f_old = self.frame_counter
                    self.t_old = time.time()
                return self.frate, frame, ret
            else:
                return self.frate, frame, ret
        else: return None

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
            dq = None,
            eq = None
            )

def my_dev(conf_sect, kill_queue, detect_queue, email_queue):
    root_camera = MainApp_Camera(
            parent = None,
            title = "Camera",
            conf = conf_sect,
            kq = kill_queue,
            dq = detect_queue,
            eq = email_queue
            )

if __name__ == "__main__":
    main()

# EOF
