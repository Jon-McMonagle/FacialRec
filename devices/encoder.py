# !/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========
Python script to encode new face data to be recognized

Modules:
- opencv:   sudo pip install opencv-python
- dlib:     sudo apt-get update
            sudo apt-get install build-essential cmake
            sudo apt-get install libopenblas-dev liblapack-dev
            sudo apt-get install libx11-dev libgtk-3-dev
            sudo apt-get install python python-dev python3-pip
            sudo pip install numpy (if not already done)
            sudo pip install dlib
            sudo pip install face_recognition
            sudo pip install imutils
'''

import cv2
import face_recognition
import pickle
import os
from imutils import paths
import configparser

import tkinter as tk
from tkinter import filedialog
import sys
import time
import os
import multiprocessing as mp
import device_communicator as dc



class Controls(tk.Frame):
    def __init__(self):
        super().__init__(parent)



class Main_Panel(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        bg1 = "#2589B8"
        wid = 450
        self.config(bg=bg1)
        self.config(width=wid)
        self.config(height=150)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)  # Prevents resizing

        ''' Adding parameters '''
        L_name = tk.Label(self, text = "Add Approved Entrant", bg=bg1)
        L_select_dir = tk.Label(self, text="Select Image Directory", bg=bg1)
        self.current_dir = tk.Label(self, justify=tk.RIGHT, text=parent.Directory)
        select_dir = tk.Button(self, text="Select Directory", command=self.change_dir)
        # Add button to initiate cascading, not allowed to click if directory is not selected
        start_encoding = tk.Button(self, command=ConfirmEncoding,
                 text="Initiate Encoding")

        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        self.columnconfigure(2, weight=1, pad=cc)
        for i in range(10):
            self.rowconfigure(i, pad=cc)
        self.configure(padx=cc)

        ''' Placing parameters '''
        L_name.grid(column=1, row=0, sticky="new")
        L_select_dir.grid(column=0, row=2, sticky="we")
        self.current_dir.grid(column=0, columnspan=2, row=3, sticky="we")
        select_dir.grid(column=3, row=3, sticky="we")
        start_encoding.grid(column=1, row=7, sticky="ns")

    def change_dir(self):
        self.parent.Directory = filedialog.askdirectory(
                initialdir=self.parent.Directory,
                title="Select Image Directory"
                )
        self.current_dir["text"] = self.parent.Directory
        cfg = configparser.ConfigParser()
        cfg.read('config/config_FR.cfg')
        editor = cfg["value_editor"]
        editor["directory"] = self.parent.Directory
        with open('config/config_FR.cfg', 'w') as conf:
            cfg.write(conf)



class ConfirmEncoding(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Encoder: Confirm")
        self.padding = 5
        tk.Label(self, text="Are the contents of this folder only images?").\
            pack(side="top", padx=70, pady=30)
        tk.Button(self, text='Yes', command=lambda:self.encoder_button_pass(), fg='green').\
            pack(side=tk.RIGHT, fill=tk.X, padx=self.padding, pady=self.padding)
        tk.Button(self, text='No', command=self.destroy, fg='red').\
            pack(side=tk.LEFT, fill=tk.X, padx=self.padding, pady=self.padding)

    def encoder_button_pass(self):
        cfg = configparser.ConfigParser()
        cfg.read('config/config_FR.cfg')
        veditor = cfg["value_editor"]
        dir = veditor["directory"]
        MainApp_Encoder.start_encoding(dir)
        self.destroy()



class MainApp_Encoder(tk.Tk):
    def __init__(self, parent=None, title="default",
            conf=False, kq=None, chc=None, dq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf
        self.chc = chc

        self.geometry("+1000+750")
        self.title(title)

        ''' Setting Variables '''
        self.Directory = os.getcwd()

        ''' Setting Frames '''
        self.MainPanel = Main_Panel(self)
        self.MainPanel.grid(column=0, row=0, sticky="ns")

        # Hardware and Communication
        if conf:
            self.protocol("WM_DELETE_WINDOW", lambda:None)
            self.kq = kq
            self.dq = dq
            self.comm_agent = dc.Dev_Communicator()
        else:
            self.protocol("WM_DELETE_WINDOW", self.on_quit)
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            os.chdir("..")

        self.update_GUI()
        self.mainloop()

    def start_encoding(dir):
        # Get paths of each file in folder
        # Images here contain data
        imagePaths = list(paths.list_images(dir))
        knownEncodings = []
        knownNames = []
        # loop over the image paths
        for(i, imagePath) in enumerate(imagePaths):
            # extract the name from the image path
            name = imagePath.split(os.path.sep)[-2]
            '''
            load the input image and convert it from BGR
            to dlib ordering, RGB
            '''
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Use FACE RECOGNITION to locate faces
            boxes = face_recognition.face_locations(rgb, model='hog')
            # compute the facial embedding for the face
            encodings = face_recognition.face_encodings(rgb, boxes)
            # loop over the encodings
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)
        # pass name to config
        cfg = configparser.ConfigParser()
        cfg.read('config/config_FR.cfg')
        numNames = len(cfg.options("saved_faces"))
        cfgNames = cfg["saved_faces"]
        if numNames == 0:
            cfg.set('saved_faces', '0', '')
            cfgNames["0"] = name
            with open('config/config_FR.cfg','w') as conf:
                cfg.write(conf)
        else:
            unnumbered = True
            n = 0
            while unnumbered:
                try:
                    holder = cfgNames[str(n)]
                    n += 1
                except KeyError:
                    cfg.set('saved_faces', str(n), '')
                    cfgNames[str(n)] = name
                    with open('config/config_FR.cfg','w') as conf:
                        cfg.write(conf)
                    unnumbered = False
        # save encodings along with their names in dictonary data
        enc_title = "encodings/" + "face_enc" + str(name)
        data = {"encodings" : knownEncodings, "names" : knownNames}
        # use pickle to save data into a file for later use
        f = open(enc_title, "wb")
        f.write(pickle.dumps(data))
        f.close()
        print("Encoding finished")

    def update_GUI(self):
        # COMMUNICATOR
        if not self.kq.empty():
            string_received = self.kq.get()
            print("Encoder: Received {} command from kill_queue!".format(string_received))
            self.on_quit()
        self.after(1, self.update_GUI)

    def on_quit(self):
        print("Encoder: Qutting...")
        self.destroy()



# MAIN
def main():
    root_encoder = MainApp_Encoder(
            parent = None,
            title = "Encoder (PID: {})".format(os.getpid()),
            conf = None,
            kq = None,
            chc = None,
            dq = None,
            )

def my_dev(conf_sect, kill_queue, child_comm, detect_queue):
    root_encoder = MainApp_Encoder(
            parent=None,
            title = "Encoder",
            conf = conf_sect,
            kq = kill_queue,
            chc = child_comm,
            dq = None
            )

if __name__ == "__main__":
    main()

# EOF
