#!/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========
    Control Panel for the Facial Recognition Software.
    It serves several purposes:
        + reads config file;
        + starts all devices;
        + collects all desirable data and keeps a log file;
        + safely terminates all process by issuing a shutdown.
    The configuration file determines which devices will be started.
    This makes the code portable as well as flexible to add/remove
    devices as needed.

    Coded sometime in 2019-2020 during the COVID-19 pandemic.
    Authors: R. Urban, J. McMonagle.

Modules:
    matplotlib: sudo pip install matplotlib
'''

'''
EXECUTION FLOW
==============
    1/ run BRIDGE.py
    2/ declaring variables
    3/ initializes DEVICE/DEVICE_COMMUNICATOR.py
        3.1/ declares QUEUEs and PIPEs
        3.2/ selects & reads CONFIG
        3.3/ passes BRIDGE stansa to the BRIDGE
        3.4/ identifies devices to be started
        3.5/ starts each device and sends appropriate stansa from CONFIG
    4/ devices start
        4.1/ devices receives its own stansa from CONFIG
        4.2/ each device has built-in default SAVE values
        4.3/ each device reads stansa from CONFIG and updates parameters
        4.4/ all devices are running
        4.5/ devices send requested data to the BRIDGE
    5/ BRIDGE continuesly monitors data from devices
'''

import tkinter as tk
import tkinter.font as font
from tkinter import filedialog
import os
import sys
import time


_platform = sys.platform    # linux, darwin, win32, cygwin
print("Platform: ", _platform)

_working_directory = os.getcwd()
_project_directory = os.path.dirname(os.path.realpath(__file__))
_device_folder = 'devices'
if _platform == 'linux' or _platform == 'darwin':
    _separator = '/'
elif _platform == 'win32':
    _separator = '\\'
print("Platform: {} uses separator: {}".format(_platform, _separator))
_device_path = _project_directory + _separator + _device_folder
_config_path = _project_directory + _separator + 'config'

""" add ./devices to python path """
sys.path.append(os.path.expanduser(_device_path))

import device_communicator



class ConfirmQuit(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        """
        parent.update()
        ppp="{}x{}+{}+{}".format(parent.winfo_width(),
                75,
                parent.winfo_x(),
                parent.winfo_y())
        print(ppp)
        self.geometry(ppp)
        """
        self.title("BRIDGE: Confirm")
        self.padding = 5

        tk.Label(self, text="Are you sure you want to quit").\
                pack(side="top", padx = 70, pady = 30)
        tk.Button(self, text='Confirm', command=self.on_quit, fg='red').\
                pack(side=tk.RIGHT, fill=tk.X, padx=self.padding, pady=self.padding)
        tk.Button(self, text='No!', command=self.destroy).\
                pack(side=tk.LEFT, fill=tk.X, padx=self.padding, pady=self.padding)

    def on_quit(self):
        self.destroy()
        self.parent.on_quit()



class ShowVariables(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("BRIDGE: Variables")
        self.padding = 20
        self.protocol("WM_DELETE_WINDOW", self.withdraw)               ## minimize

        """ Declare local colors """
        bg1 = "gray30"
        bg2 = "SlateGray4"
        sp = 2   # padding value
        wid = 500

        """ creat GUI frame first """
        self.Top_frame = tk.Frame(self, height=100, width=wid, bg=bg1,
                bd=sp, relief="ridge")

        self.Bot_frame = tk.Frame(self, height=200, width=wid, bg=bg2,
                bd=sp, relief="ridge")

        """ declare grid settings """

        """ place/organize main frames """
        self.Top_frame.grid(column=0, row=0, sticky="news", padx=sp, pady=sp)
        self.Bot_frame.grid(column=0, row=1, sticky="news", padx=sp, pady=sp)

        self.Top_frame.grid_propagate(False)
        self.Bot_frame.grid_propagate(False)

        """ Elements inside frame ... TOP """
        self.TF1 = tk.Frame(self.Top_frame, bg="black", width=wid/3)
        self.TF2 = tk.Frame(self.Top_frame, bg="black", width=wid/3)
        self.TF3 = tk.Frame(self.Top_frame, bg="black", width=wid/3)

        self.TF_name = tk.Label(self.Top_frame, text="GLOBAL variables", bg=bg1, fg="white")
        self.TF_wdn = tk.Label(self.Top_frame, text="Working dir:", bg=bg1)
        self.TF_wdf = tk.Frame(self.Top_frame, width=333, bg=bg1)
        self.TF_wdv = tk.Label(self.Top_frame, text=parent.Directory)
        self.TF_rin = tk.Label(self.Top_frame, text="Record interval [s]", bg=bg1)
        #self.TF_riv = tk.Label(self.Top_frame, text=str(parent.Record_interval.get()))
        self.TF_riv = tk.Label(self.Top_frame, width=10, textvariable=parent.Recording_interval)

        self.Top_frame.columnconfigure(0, pad=sp, weight=1)
        self.Top_frame.columnconfigure(1, pad=sp, weight=1)
        self.Top_frame.columnconfigure(2, weight=1, pad=sp)
        for i in range(5):
            self.Top_frame.rowconfigure(i, pad=2*sp)

        self.TF_name.grid(column=1, row=0)
        self.TF1.grid(column=0, row=1)
        self.TF2.grid(column=1, row=1)
        self.TF3.grid(column=2, row=1)
        self.TF_wdn.grid(column=0, row=2, sticky="e")
        self.TF_wdv.grid(column=1, columnspan=2, row=2, sticky="we")
        self.TF_rin.grid(column=0, row=3, sticky="e")
        self.TF_riv.grid(column=1, columnspan=2, row=3, sticky="w")

        """ Elements inside frame ... Bottom """
        myFont = font.Font(family='DejaVu Sans Mono', size=7)
        self.BF_name = tk.Label(self.Bot_frame, text="DEVICE values", bg=bg2)
        self.BF_dev_names = tk.Label(self.Bot_frame, text="Device names", bg=bg2)
        self.BF_dev_vals = tk.Label(self.Bot_frame, text="TopLevel__init__", bg=bg2)
        self.BF_dev_names['font'] = myFont
        self.BF_dev_vals['font'] = myFont

        self.Bot_frame.columnconfigure(0, weight=1)
        self.Bot_frame.columnconfigure(1, pad=5)
        self.Bot_frame.columnconfigure(2, weight=1)
        self.Bot_frame.rowconfigure(1, weight=1)

        self.BF_name.grid(column=1, row=0)
        self.BF_dev_names.grid(column=1, row=3)
        self.BF_dev_vals.grid(column=1, row=4)

        # debug

        # minimize by default
        self.withdraw()



class MenuBar(tk.Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        fileMenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="File", underline=0, menu=fileMenu)
        fileMenu.add_command(label="Exit", underline=1, command=parent.on_quit)

        bridgeMenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="Bridge", underline=0, menu=bridgeMenu)
        bridgeMenu.add_command(label="window", command=self.parent.window_position)

        deviceMenu = tk.Menu(self, tearoff=True)
        self.add_cascade(label="Devices", underline=0, menu=deviceMenu)
        #<This menu should be dynamically created as devices are loaded>
        deviceMenu.add_command(label="Show vars", command=self.parent.display_variables)
        deviceMenu.add_separator()
        for en in parent.Devices:
            deviceMenu.add_command(label=en, command=lambda: None)

        """
        deviceMenu.add_command(label="Camera", command=lambda: None)
        deviceMenu.add_command(label="Glassman", command=lambda: None)
        deviceMenu.add_command(label="RGA", command=lambda: None)
        deviceMenu.add_command(label="SRS-screen", command=lambda: None)
        """

        helpMenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="Help", underline=0, menu=helpMenu)
        helpMenu.add_command(label="About", command=lambda: None)
        helpMenu.add_command(label="Help", command=lambda: None)



class Frame_LeftNav(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        bg1 = "mistyrose4"

        self.config(bg=bg1)
        self.config(width=150)
        self.config(height=200)
        self.config(bd=2)
        self.config(relief="ridge")
        self.pack_propagate(False)     # prevents resizing
        """
        self.lbl_1 = tk.Label(self, text="LeftNav")
        self.lbl_1.pack(side="top", padx=5, fill="x", expand=1)
        """



class Frame_MainFrame(tk.Frame):
    def __init__(self, parent):
        #tk.Frame.__init__(self, parent)
        super().__init__(parent)
        self.parent = parent

        bg1 = "lightskyblue4"
        self.bg1 = bg1    # testing

        self.config(bg=bg1)
        self.config(width=400)
        self.config(height=130)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)     # prevents resizing

        """ Building elements """
        self.L_rec_label = tk.Label(self, text="Save data", bg=bg1)
        self.B_rec_value = tk.Checkbutton(self, var=parent.Recording, bg=bg1)

        self.string_interval = tk.StringVar()
        self.string_interval.set(str(parent.Recording_interval.get()))
        self.L_inter_label = tk.Label(self, text="Saving interval [s]", bg=bg1)
        self.B_inter_value = tk.Entry(self, width=5, textvariable=self.string_interval)
        self.B_inter_value.bind('<Return>', self.set_interval)

        """ Grid configuration """
        self.columnconfigure(0, weight=1, pad=3)
        self.columnconfigure(2, pad=3)
        self.columnconfigure(3, pad=3)

        self.rowconfigure(0, pad=5)
        self.rowconfigure(1, pad=5)

        """ Placing elements """
        self.L_rec_label.grid(column=2, row=0, sticky="w")
        self.B_rec_value.grid(column=3, row=0, sticky="e")

        self.L_inter_label.grid(column=2, row=1, sticky="w")
        self.B_inter_value.grid(column=3, row=1, sticky="e")

    def set_interval(self, event):
        # takes focus away from Entry widget
        self.focus()

        old_value = str(self.parent.Recording_interval.get())
        new_value = self.string_interval.get()
        try:
            new = int(new_value)
            if new <= 0:
                print("Saving interval must be above zero!")
                self.string_interval.set("1")
                new=1
            self.parent.Recording_interval.set(new)
        except ValueError:
            print("Cannot convert to integer!")
            self.string_interval.set(old_value)

        """
        pom = self.parent.Record_interval.get()
        print("Changing value to: {}".format(pom))
        """



class Frame_BotFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        bg1 = "lightsteelblue4"

        self.config(bg=bg1)
        self.config(width=400)
        self.config(height=70)
        self.config(bd=2)
        self.config(relief="ridge")
        self.grid_propagate(False)     # prevents resizing

        """ Building elements """
        self.L_wd_label = tk.Label(self, text="Working directory", bg=bg1)
        self.L_wd_value = tk.Label(self, justify=tk.LEFT, text=parent.Directory)
        self.B_br = tk.Button(self, text="change dir", command=self.change_dir)

        """ Grid configuration """
        self.columnconfigure(0, weight=1, pad=3)
        self.rowconfigure(0, pad=5)

        """ Placing elements """
        self.L_wd_label.grid(column=0, row=0, sticky="sw")
        self.L_wd_value.grid(column=0, row=1, columnspan=3, sticky="we")
        self.B_br.grid(column=2, row=0, sticky="ne")

    def change_dir(self):
        self.parent.Directory = filedialog.askdirectory(
                initialdir=self.parent.Directory,
                title="Select working directory"
                )
        self.L_wd_value["text"] = self.parent.Directory



class MainApp(tk.Tk):
    def __init__(self, master=None, title="MAIN", size="+50+50"):
        super().__init__()
        self.title(title)
        """ POSITION ONLY! Size is defined by sub-frames """
        self.geometry(size)
        self.resizable(width=False, height=False)

        #<Also could use withdraw(): no taskbar icon | use deiconify to restore>
        # self.protocol("WM_DELETE_WINDOW", self.iconify)               ## minimize
        self.protocol("WM_DELETE_WINDOW", lambda: None)                 ## do nothing
        # self.protocol("WM_DELETE_WINDOW", lambda: ConfirmQuit(self))  ## confirm close

        """ Declaring variables """
        """ initial directory: should be set in config file when implemented """
        self.Directory = os.getcwd()
        self.highest = 0 # Highest directory number
        print("BRIDGE: Bridge directory: {}".format(self.Directory))

        self.Recording = tk.BooleanVar()
        self.Recording.set(False)

        self.Recording_interval = tk.IntVar()
        self.Recording_interval.set(15)

        # save directory should come from config file
        self.savedir = ""

        self.directory_set = False
        self.timing_reference = time.time()
        self.frame_number = 1
        self.savetime = time.time() * 2
        self.newrecordingtime = False
        self.camerastarted = False
        self.saveinfosent = False

        """ Hardware ... two places ... before or after GUI """
        print("BRIDGE: Initializing communication ...")
        self.communicator = device_communicator.Main_Comm(self.Directory)
        self.Devices, Bridge = self.communicator.Get_devices()
        self.parse_config(Bridge)
        """ ----------------------------------------------- """

        """ Building the interface """
        """ ************************************************************ """
        """ Menus """
        self.config(menu = MenuBar(self))

        """ Creating frames """
        #self.TopBar = Frame_TopBar(self)
        self.LeftNav = Frame_LeftNav(self)
        self.MainFrame = Frame_MainFrame(self)
        self.BotFrame = Frame_BotFrame(self)

        """ Creating a layout """
        m=1
        #self.TopBar.pack(side="top")
        self.LeftNav.grid(column=0, row=0, rowspan=2, padx=m, pady=m)
        self.MainFrame.grid(column=1, row=0, padx=m, pady=m, sticky="news")
        self.BotFrame.grid(column=1, row=1, padx=m, pady=m, sticky="news")

        """ Initializing a TopLevel window """
        self.Var_window = ShowVariables(self)
        """ ************************************************************ """
        """ Interface is DONE! """

        self.killer = device_communicator.GracefulKiller()        # not sure here?!

        #<RUN mainloop()>
        self.update_GUI()
        self.mainloop()

    def parse_config(self, Bridge):
        # default values for all possible keys
        print("BRIDGE: getting values from CONFIG ...")
        my_init = {
                'directory':self.Directory,
                'position':'+1+1',
        }
        for k, v in my_init.items():
            try: my_init[k] = Bridge[k]
            except KeyError: pass
            #print("{} = {}".format(k, my_init[k]))
        self.Directory = my_init['directory']

    def get_save_dir(self):
        self.DirectoryName = self.save_dir()
        path = os.path.join(self.Directory, self.DirectoryName)
        os.mkdir(path)
        self.savedir = "/" + self.Directory + "/" + self.DirectoryName + "/"

    def save_dir(self):
        mainD = os.getcwd()
        subD = os.listdir(mainD)
        for files in subD:
            folder = files.split("_")
            savefolder = self.is_num(folder[0])
            if savefolder:
                holder = int(folder[0])
                if holder > self.highest:
                    self.highest = holder
                else:
                    pass
        self.highest += 1
        name = str("{:04d}".format(self.highest) + "_")
        return name

    def is_num(self, string):
        try:
            int(string)
            return(True)
        except ValueError:
            return False

    def update_GUI(self):
        update_delay = 500

        _h, _v = self.parse_variables()

        if self.Var_window.state() == "normal":
            self.Var_window.TF_wdv["text"] = self.Directory

            self.Var_window.BF_dev_names["text"] = _h
            self.Var_window.BF_dev_vals["text"] = _v

        ''' Camera Recording '''
        ### Sets time to current time plus timing interval
        if self.newrecordingtime == False and self.Recording.get() == True:
            self.timing_reference = time.time()
            self.newrecordingtime = True
        ### Sending data to camera and recording
        if self.Recording.get():
            if self.directory_set == False:
                self.get_save_dir()
                self.directory_set = True
            period = self.Recording_interval.get()
            # If recording interval changes send to camera
            if self.savetime != self.timing_reference + period:
                self.savetime = self.timing_reference + period
                self.saveinfosent = False
            self.savetime = self.timing_reference + period
            imagename = str("{:05d}".format(self.frame_number) + ".png")
            if self.camerastarted == False:
                self.communicator.Camera_Saving("start")
                self.communicator.Camera_Saving("Directory")   # Send directory with start
                self.communicator.Camera_Saving(self.savedir)  # command
                self.camerastarted = True
            if self.saveinfosent == False:  # Send image time and name
                 self.communicator.Camera_Saving(self.savetime)
                 self.communicator.Camera_Saving(imagename)
                 self.saveinfosent = True
            saveref = self.savetime - time.time()
            if saveref <= 0:
               print("BRIDGE: Saving now: {}".format(time.strftime("%H:%M:%S")))
               self.frame_number += 1
               self.timing_reference = time.time()
               self.saveinfosent = False
        else:
            self.frame_number = 1  ## If recording stopped, frame # reset
            self.communicator.Camera_Saving("stop")
            self.camerastarted = False
            self.newrecordingtime = False
            self.directory_set = False
        self.after(update_delay, self.update_GUI)

    def parse_variables(self):
        '''
        Description:
        The function PULLs data dictionaries from all devices.
        It formats both the HEADER and VALUES into a string
        with desirable column width controlled by a variable.

        Returns:
        Two strings: HEADER and VALUES
        '''
        _header = ''
        _all_vals = ''
        try:
            stat, pulled = self.communicator.Pull_Data()
            #print("BRIDGE: status byte: ", stat)
            #print("BRIDGE: data: ", pulled)
            for x in pulled:
                for k, v in x.items():
                    _header += "{:<15}".format(k)
                    _all_vals += "{:<15}".format(v)
        except AttributeError: pass

        return _header, _all_vals

    def display_variables(self):
        self.Var_window.deiconify()

    def window_position(self):
        self.update()
        ppp="Window position: +{}+{}".format(self.winfo_x(), self.winfo_y())
        print(ppp)

    def on_quit(self):
        print("BRIDGE: Shutting down devices: {}".format(self.Devices))
        self.communicator.Stop_Devices()

        _all = False
        while not _all:
            stat, pulled = self.communicator.Pull_Data()
            _all = all(x == 'CLOSED' for x in stat)
            time.sleep(1)

        print("BRIDGE: HAL, all devices are off!  Power off ...")
        self.destroy()

def main():
    #<Can specify "title" and "size" here>
    root = MainApp(title="Control Center")

if __name__ == "__main__":
    main()

# EOF
