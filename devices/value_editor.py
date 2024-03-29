# !/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========
Python script to edit default config values such as:
    - Receiving email
    - Encoded faces

Modules:
'''

import tkinter as tk
import sys
import time
import os
import configparser
import multiprocessing as mp
import device_communicator as dc
import configparser



class Controls(tk.Frame):
    def __init__(self):
        super().__init__(parent)



class Main_Panel(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)



class Main_Panel(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        bg1 = "#B5C5F9"
        wid = 600
        self.config(bg=bg1)
        self.config(width=wid)
        self.config(height=150) # might need to change
        self.config(bd=1)
        self.config(relief="raised")
        self.grid_propagate(False)

        ''' Adding parameters '''
        # L == Label
        # V == Value
        # B == Button
        L_name = tk.Label(self, text="Door Access Settings", bg=bg1)
        L_current_ue = tk.Label(self, text="Current User Email:", bg=bg1)
        V_current_ue = tk.Label(self, justify=tk.RIGHT, textvariable= parent.current_email)
        B_current_ue = tk.Button(self, command=ChangeUE, text="Change")
        B_view_SF = tk.Button(self, command=ViewFaces, text="View Saved Faces")

        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        self.columnconfigure(2, weight=1, pad=cc)
        self.columnconfigure(3, weight=1, pad=cc)
        for i in range(20):
            self.rowconfigure(i, pad=cc)
        self.configure(padx=cc)

        ''' Placing parameters '''
        L_name.grid(column=1, columnspan=2, row=0, sticky="new")
        L_current_ue.grid(column=0,  row=4, sticky="we")
        V_current_ue.grid(column=1, columnspan=2, row=4, sticky="we")
        B_current_ue.grid(column=3, row=4, sticky="we")
        B_view_SF.grid(column=1, columnspan=2, row=12, sticky="we")



class ChangeUE(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Change User Email")
        self.padding = 5
        bg1 = "#2589B0"
        self.config(bg=bg1)
        self.config(width=100)
        self.config(height=30)
        ''' Adding parameters '''
        L_ne = tk.Label(self, text="New Email:", bg=bg1)
        self.T_ne = tk.Entry(self, width=30)    # T_ne == text, new email
        B_ne = tk.Button(self, text="Change", command=lambda:self.set_email(), fg='red')
        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        self.columnconfigure(2, weight=1, pad=cc)
        self.rowconfigure(0, pad=cc)
        ''' Placing parameters '''
        L_ne.grid(column=0, row=0, sticky="we")
        self.T_ne.grid(column=1, row=0, sticky="we")
        B_ne.grid(column=2, row=0, sticky="we")

    def set_email(self):
        value = self.T_ne.get()
        if value:
            self.cfg = configparser.ConfigParser()
            self.cfg.read('config/config_FR.cfg')
            emailnotifier = self.cfg["email_notifier"]
            emailnotifier["receiver"] = value
            valueeditor = self.cfg["value_editor"]
            valueeditor["receiver"] = value
            with open('config/config_FR.cfg', 'w') as conf:
                self.cfg.write(conf)
        self.destroy()



class ViewFaces(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("View Saved Faces")
        self.padding = 5
        bg1 = "#2589B1"
        self.config(width=100)
        self.config(height=100)
        ''' Adding parameters '''
        listlabel = tk.Label(self, text="Saved Faces:", bg=bg1)
        scrollbar = tk.Scrollbar(self)
        self.nlist = tk.Listbox(self, yscrollcommand=scrollbar.set)
        delbutton = tk.Button(self, text="Delete", command=lambda:self.del_name(), fg='red')
        ''' Grid configuration '''
        cc = 5
        self.columnconfigure(0, weight=1, pad=cc)
        self.columnconfigure(1, weight=1, pad=cc)
        self.columnconfigure(2, weight=1, pad=cc)
        for i in range(10):
            self.rowconfigure(i, pad=cc)
        ''' Placing parameters '''
        listlabel.grid(column=0, columnspan=3, row=0, sticky="we")
        self.nlist.grid(column=0, row=3, sticky="we")
        scrollbar.grid(column=1, row=3, sticky="ns")
        delbutton.grid(column=2, row=3, sticky="we")
        ''' Adding values to list '''
        self.update_list()
        scrollbar.config(command = self.nlist.yview)

    def update_list(self):
            addingnames = True
            n = 0
            self.cfg = configparser.ConfigParser()
            self.cfg.read('config/config_FR.cfg')
            numNames = len(self.cfg.options("saved_faces"))
            if numNames == 0:
                addingnames = False
            self.cfgnames = self.cfg["saved_faces"]
            while addingnames:
                try:
                    name = self.cfgnames[str(n)]
                    self.nlist.insert(n, name)
                    numNames -= 1
                    if numNames == 0:
                        addingnames = False
                except KeyError: pass
                n += 1

    def del_name(self):
        try:
            namesel = self.nlist.get(self.nlist.curselection())
            name_enc = "encodings/" + "face_enc" + namesel
            unmatched = True
            n = 0
            name = ""
            print("Deleting:", namesel)
            while unmatched:
                try:
                    name = self.cfgnames[str(n)]
                except KeyError: pass
                if namesel == name:
                    unmatched = False
                    # Add feature to remove encoding
                    self.cfg.remove_option("saved_faces", str(n))
                    with open('config/config_FR.cfg', 'w') as conf:
                         self.cfg.write(conf)
                else:
                    n += 1
            self.nlist.delete(tk.ANCHOR)
            os.remove(name_enc)
        except tk.TclError: pass



class MainApp_Settings(tk.Tk):
    def __init__(self, parent=None, title="defualt",
            conf=False, kq=None, dq=None, eq=None):
        super().__init__()
        self.parent = parent
        self.conf = conf

        self.geometry("+200+500")
        self.title(title)

        ''' Setting Variables '''
        self.current_email = tk.StringVar()

        ''' Setting Frames '''
        self.MainPanel = Main_Panel(self)
        self.MainPanel.grid(column=0, row=0, sticky="ns")

        # Hardware and Communication
        if conf:
            self.protocol("WM_DELETE_WINDOW", lambda:None)
            self.kq = kq
            self.dq = dq
            self.eq = eq
            self.comm_agent = dc.Dev_Communicator()
        else:
            self.protocol("WM_DELETE_WINDOW", self.on_quit)
            self.kq = mp.Queue()
            self.dq = mp.Queue()
            self.eq = mp.Queue()
            os.chdir("..")

        self.initialization()
        self.update_GUI()
        self.mainloop()

    def initialization(self):
        my_init = {
            'position':'400+600',
            'receiver':'none',
        }
        for k, v in my_init.items():
            try: my_init[k] = self.conf[k]
            except KeyError: pass           # missing key in CONFIG
            except AttributeError: pass     # no CONFIG at all
            except TypeError: pass          # conf=None

         # Assigning variables
        email_holder =  my_init['receiver']
        self.current_email.set(email_holder)
        self.old_email = email_holder

    def update_GUI(self):
        cfg = configparser.ConfigParser()
        try:
            cfg.read('config/config_FR.cfg')
            cfgemail = cfg["value_editor"]
            self.current_email.set(cfgemail["receiver"])
        except KeyError: pass
        if not self.old_email == self.current_email.get():
            #print("HITTING CHANGE LOOP, SENDING NEW EMAIL THROUGH PIPE!!!")
            self.old_email = self.current_email.get()
            if self.conf:
                self.comm_agent.Email_info_queue(self.eq, self.old_email)
        # COMMUNICATOR
        if not self.kq.empty():
            string_received = self.kq.get()
            print("Settings: Received {} command from kill_queue!".format(string_received))
            self.on_quit()
        self.after(10, self.update_GUI)

    def on_quit(self):
        print("SETTINGS: PID: {}".format(os.getpid()))
        print("Settings: Quitting...")
        self.destroy()



# MAIN
def main():
    root_settings = MainApp_Settings(
            parent = None,
            title = "Settings",
            conf = None,
            kq = None,
            dq = None,
            eq = None
            )

def my_dev(conf_sect, kill_queue, detect_queue, email_queue):
    root_settings = MainApp_Settings(
            parent = None,
            title = "Settings",
            conf = conf_sect,
            kq = kill_queue,
            dq = detect_queue,
            eq = email_queue
            )

if __name__ == "__main__":
    main()

# EOF
