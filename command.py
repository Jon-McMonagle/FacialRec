#!/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========
    Control panel for the facial recognition software.

    Tasks:
        - Read config file
        - Start devices
        - Collect data from devices
        - Terminates all processes when finished

    Modules:
        - matplotlib: sudo pip install matplotlib
'''

import tkinter as tk
import tkinter.font as font
from tkinter import filedialog
import os
import sys
import time


Working_directory = os.getcwd()
Project_directory = os.path.dirname(os.path.realpath(__file__))
Device_folder = 'devices'
Device_path = Project_directory + '/' + Device_folder
Config_path = Project_directory + '/' + 'config'

# Add ./devices to python path
sys.path.append(os.path.expanduser(Device_path))

import device_communicator



class ConfirmQuit(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # configuration
        self.title("Command: Confirm")
        self.padding = 5
        tk.Label(self, text="Are you sure you want to quit?").\
            pack(side="top", padx = 70, pady = 30)
        tk.Button(self, text='Yes', command=self.on_quit, fg='red').\
            pack(side=tk.RIGHT, fill=tk.X, padx=self.padding, pady=self.padding)
        tk.Button(self, text='No', command=self.destroy).\
            pack(side=tk.LEFT, fill=tk.X, padx=self.padding, pady=self.padding)

    def on_quit(self):
        self.destroy()
        self.parent.on_quit()



class MenuBar(tk.Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        fileMenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="File", underline=0, menu=fileMenu)
        fileMenu.add_command(label="Quit", underline=1, command=parent.on_quit)



class Frame_leftNav(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        bg1 = "#1BA314"
        self.config(bg=bg1)
        self.config(width=150)
        self.config(height=200)
        self.config(bd=2)
        self.config(relief="ridge")
        self.pack_propagate(False)  # prevents resizing



class Frame_MainFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        bg1= "#9B65BF"
        self.config(bg=bg1)
        self.config(width=400)
        self.config(height=130)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)  # prevents resizing

        ''' Adding elements to frame '''
#        self.label_detect = tk.Label(self, text="Detect Face", bg=bg1)
#        self.button_detect = tk.Checkbutton(self, var=parent.Detection, bg=bg1) # Detection var

#        self.string_interval = tk.StringVar()
#        self.string_interval.set(str(parent.Detection_interval.get()))
#        self.label_interval = tk.Label(self, text="Detection Rate [s]", bg=bg1)
#        self.button_interval_value = tk.Entry(self, width=5, textvariable=self.string_interval)
#        self.button_interval_value.bind('<Return>', self.set_interval)

        ''' Grid configuration '''
        self.columnconfigure(0, weight=1, pad=3)
        self.columnconfigure(2, pad=3)
        self.columnconfigure(3, pad=3)

        self.rowconfigure(0, pad=5)
        self.rowconfigure(1, pad=5)

        ''' Placing controls '''
#        self.label_detect.grid(column=2, row=0, sticky="w")
#        self.button_detect.grid(column=3, row=0, sticky="e")

#        self.label_interval.grid(column=2, row=1, sticky="w")
#        self.button_interval_value.grid(column=3, row=1, sticky="e")

    def set_interval(self, event):
        self.focus()    # takes focus away from the entry

        old_value = str(self.parent.Detection_interval.get())
        new_value = self.string_interval.get()
        try:
            new = int(new_value)
            if new <= 0:
                print("Detection interval must be above 0")
                self.string_interval.set("1")
                new=1
            self.parent.Detection_interval.set(new)
        except ValueError:
            print("Cannot convert to integer")
            self.string_interval.set(old_value)



class MainApp(tk.Tk):
    def __init__(self, master=None, title="MAIN", size="+60+60"):
        super().__init__()
        self.title(title)
        self.geometry(size) # position only
        self.resizable(width=False, height=False)

        self.protocol("WM_DELETE_WINDOW", lambda: ConfirmQuit(self))    # "x" button confirm close
#        self.protocol("WM_DELETE_WINDOW", lambda: None) # "x" button does nothing

        ''' Declaring variables '''
        self.Directory = os.getcwd()

        ''' Hardware '''
        print("Command: Initalizing communicator..")
        self.communicator = device_communicator.Main_Comm(self.Directory)
        self.Devices, Command = self.communicator.Get_devices()
        self.parse_config(Command)

        ''' Creating interface '''
        self.config(menu = MenuBar(self))

        self.LeftNav = Frame_leftNav(self)
        self.MainFrame = Frame_MainFrame(self)

        ''' Setting layout '''
        m=1
        self.LeftNav.grid(column=0, row=0, rowspan=2, padx=m, pady=m)
        self.MainFrame.grid(column=1, row=0, padx=m, pady=m, sticky="news")

        self.killer = device_communicator.Graceful_Killer()

        #< RUN mainloop()>
        self.update_GUI()
        self.mainloop()

    def parse_config(self, Command):
        print("Command: Getting values from config file")
        my_init = {
                'directory':self.Directory,
                'position':'1+1',
        }
        for k, v in my_init.items():
            try: my_init[k] = Command[k]
            except KeyError: pass
        self.Directory = my_init['directory']

    def is_num(self, string):
        try:
            int(string)
            return(True)
        except ValueError:
            return False

    def update_GUI(self):
        update_delay = 500  # ms
        _h, _v = self.parse_variables()
        self.after(update_delay, self.update_GUI)

    def parse_variables(self):
        '''
           This function pulls data dictonaries from all devices.
           It formats the header and values into a string
           with desirable column width controlled by a variable.
           Returns: Header (string) and Values (string)
        '''
        _header = ''
        _all_vals = ''
        try:
            stat, pulled = self.communicator.Pull_data()
            for x in pulled:
                for k, v in x.items():
                    _header += "{:<15}".format(k)
                    _all_vals += "{:<15}".format(v)
        except AttributeError: pass

        return _header, _all_vals

    def on_quit(self):
        print("Command: Shutting down devices: {}".format(self.Devices))
        self.communicator.Stop_devices()

        _all = False
        while not _all:
            stat, pulled = self.communicator.Pull_data()
            _all = all(x == 'CLOSED' for x in stat)
            time.sleep(1)

        print("Command: All devices are off. Quitting...")
        self.destroy()

def main():
    root = MainApp(title="Command")

if __name__ == "__main__":
    main()

# EOF
