# !/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========

Python script to send names and images of door entrants using email notifications
Will also activate a GPIO pin for 25 seconds

'''

import tkinter as tk
import sys
import time
import random
import os
import multiprocessing as mp
import device_communicator as dc
import configparser
import cv2

import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PIL
from PIL import Image

user = os.uname()
if user[1] == "raspberrypi":
    import RPi.GPIO as GPIO


class Controls(tk.Frame):
    def __init__(self):
        super().__init__(parent)
        pass



class Main_Panel(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        bg1 = "#CE4C53"
        wid = 350
        self.config(bg=bg1)
        self.config(width=wid)
        self.config(height=100)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)  # Prevents resizing

        ''' Adding parameters '''
        L_name = tk.Label(self, text="Email Settings", bg=bg1)
        F0 = tk.Frame(self, height=3, width = wid/2+20, bg="black")
        F1 = tk.Frame(self, height=3, width = wid/2+20, bg="white")
        L_send_em = tk.Label(self, text="Send Email?", bg=bg1)
        B_send_em = tk.Button(self, text="Send", command=parent.start_connection)

        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        for i in range(15):
            self.rowconfigure(i, pad=cc)
        self.configure(padx=cc)

        ''' Placing parameters '''
        L_name.grid(column=0, columnspan=2, row=0, sticky="new")
        F0.grid(column=0, row=1, pady=10, sticky="we")
        F1.grid(column=1, row=1, sticky="we")
        L_send_em.grid(column=0, row=5, sticky="e")
        B_send_em.grid(column=1, row=5, sticky="w")



class MainApp_Email():
    def __init__(self, parent=None, title="default",
            conf=False, kq=None, dq=None, eq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf

#        self.geometry("+100+500")
#        self.title(title)

        ''' GPIO setup '''
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.relay = 26     # Value to change if we need a different pin!!!!!!!!!!!!
        GPIO.setup(self.relay, GPIO.OUT)
        self.time_off = time.time()

        ''' Setting email variables '''
        self.port = 465     # For SSL
        self.email_address = "python.door.capstone@gmail.com"
        self.password = ""      # From config
        self.receiver_address = ""  # From config
        self.subject = "Person at Door!"
        self.body = "This message was sent from an RPi Python script"
        self.message = f"Subject: {self.subject}\n\n{self.body}"
        self.run_update = True

        ''' Setting Frames: Can remove later '''
#        self.MainPanel = Main_Panel(self)
#        self.MainPanel.grid(column=0, row=0, sticky="ns")

        # Hardware and Communication
        if conf:
#            self.protocol("WM_DELETE_WINDOW", lambda:None)
            self.kq = kq
            self.dq = dq
            self.eq = eq
            self.comm_agent = dc.Dev_Communicator()
        else:
#            self.protocol("WM_DELETE_WINDOW", self.on_quit)
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            self.eq = mp.Queue()
            os.chdir("..")

        self.initialization()
        self.update_GUI()
#        self.mainloop()

    def initialization(self):
        my_init = {
                'position':'+100+500',
                'password':'none',
                'receiver':'none',
        }
        for k, v in my_init.items():
            try: my_init[k] = self.conf[k]
            except KeyError: pass
            except AttributeError: pass
            except TypeError: pass

        # Assigning variables
        self.password = my_init['password']
        self.receiver_adresss = my_init['receiver']

    def start_connection(self):
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=context) as server:
            server.login(self.email_address, self.password)
            server.sendmail(self.email_address, self.receiver_address, self.msg.as_string())

    def create_msg(self):
        self.msg = MIMEMultipart()
        self.msg['Subject'] = self.subject
        self.msg['From'] = self.email_address
        self.msg['To'] = self.receiver_address
        self.msgText = MIMEText('<b>%s</b>' % (self.body), 'html')
        self.msg.attach(self.msgText)
        with open('Entrant.png', 'rb') as fp:
            img = MIMEImage(fp.read())
            img.add_header('Content-Disposition', 'attachment', filename="Entrant.png")
            self.msg.attach(img)

    def update_GUI(self):       # NEED to add the pin code to this section for approved names
        while self.run_update:
            try:
                cfg = configparser.ConfigParser()
                cfg.read('config/config_FR.cfg')
                cfgemail = cfg["email_notifier"]
                self.receiver_address = cfgemail["receiver"]
            except KeyError: pass
            # COMMUNICATOR
            if not self.eq.empty():
                name_received = self.eq.get()
                frame_received = self.eq.get()
                if not name_received == "Unknown person":
                    self.time_off = time.time() + 25
                    GPIO.output(self.relay, 1)
                frame_converted = cv2.cvtColor(frame_received, cv2.COLOR_RGB2GRAY)
#                print("EMAIL: Received Name: {}!!!!!".format(name_received))
                time_rec = time.strftime("%H:%M:%S")
                self.body = "Person recorded at  door: {}<br>At time: {}".format(name_received, time_rec)
                self.message = f"Subject: {self.subject}\n\n{self.body}"
                frame_convert = PIL.Image.fromarray(frame_converted)
                frame_convert = frame_convert.save("Entrant.png")
                self.create_msg()
                self.start_connection()
            if not self.kq.empty():
                string_received = self.kq.get()
                print("Email: Received {} command from kill_queue!".format(string_received))
                self.on_quit()
            if self.time_off <= time.time():
                GPIO.output(self.relay, 0)
#            self.after(1, self.update_GUI)

    def on_quit(self):
        print("Email Notifier: Quitting...")
        self.run_update = False
        print("Email: Emptying pipe...")
        while not self.eq.empty():
            cleanup = self.eq.get()



# MAIN
def main():
    root_email = MainApp_Email(
            parent = None,
            title = "Email Notifications (PID: {})".format(os.getpid()),
            conf = None,
            kq = None,
            dq = None,
            eq = None
            )

def my_dev(conf_sect, kill_queue, detect_queue, email_queue):
    root_email = MainApp_Email(
            parent=None,
            title = "CHILD: Email Settings",
            conf = conf_sect,
            kq = kill_queue,
            dq = detect_queue,
            eq = email_queue
            )

if __name__ == "__main__":
    main()

#EOF
