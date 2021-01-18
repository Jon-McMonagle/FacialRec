#!/bin/python3
# coding: utf-8

'''
DESCRIPTION
===========
Used to create a link between devices and the command.
Creates queues and pipes to transfer data.

'''

import multiprocessing as mp
import os
import sys
from time import sleep
import signal
from tkinter import filedialog
import configparser


# Add /devices path to script
sys.path.append(os.path.expanduser("./devices"))


try:
    import camera           # Detection camera
    import email_notifier   # Email Notifications
    import encoder          # New Face Addtions
    import value_editor     # Device Settings
except ModuleNotFoundError as err:
    print("Error: {} ...Qutting...".format(err))
    sys.exit(True)



class Main_Comm:
    def __init__(self, init_conf_path='.'):
        self.init_conf_path = init_conf_path
        mp.set_start_method('spawn')
        self.kill_queue = mp.Queue()
        self.detect_queue = mp.Queue()  # Detection queue
        self.p_conns = []
        self.ch_conns = []
        self.processes = []

        self.devs = self.Read_config()
        print("Communicator: Devices from config: {}".format(self.devs))
        self.devs.remove('Command')
        print("Communicator: Removed: {}".format(self.devs))
        # Check for 'executable'
        to_run = []
        init_dict = []
        for d in self.devs:
            run = self.cfg[d]['executable']
            to_run.append(run)
            init_dict.append(self.cfg[d])
        print("All to run: {}".format(to_run))

        for pr, conf in zip(to_run, init_dict): # self.devices or to_run
            run_me = pr
            # unidirectional pipe: p_conn <--> ch_conn
            self.p_conn, self.ch_conn = mp.Pipe(duplex=False)
            self.proc = mp.Process(target=eval(run_me), \
                    args=( \
                        conf,                   # Device section of config
                        self.kill_queue,        # Kill queue
                        self.ch_conn,           # Child end of the PIPE
                        self.detect_queue,      # Detection queue for camera
                        ))
            self.proc.start()
            self.p_conns.append(self.p_conn)
            self.ch_conns.append(self.ch_conn)
            self.processes.append(self.proc)

        self.results = [None] * len(self.processes)
        self.stat = [None] * len(self.processes)

    def Read_config(self):
        print("Communicator: Reading config file")
        try:
            self.cfg = configparser.ConfigParser()
            self.cfg.read('config/config_FR.cfg')
            self.Command = self.cfg['Command']
            print("Communicator: Config dictonary: ", self.Command)
        except TypeError:
            print("Empty path to cfg file! Default values being used...")
        except configparser.MissingSectionHeaderError:
            print("Wrong file format! Default values being used...")
        return self.cfg.sections()

    def Get_devices(self):  # Passes devices to Command
        return self.devs, self.Command

    def Pull_data(self):
        for i, p_conn in enumerate(self.p_conns):
            while p_conn.poll():
                try:
                    self.results[i] = p_conn.recv()
                    self.stat[i] = str(i)
                except EOFError as err:
                    self.results[i] = None
                    self.stat[i] = 'CLOSED'
                    break
                except BrokenPipeError as err2:
                    self.results[i] = None
                    self.stat[i] = 'CLOSED'
                    break
                except Exception as err:
                    self.results[i] = None
                    self.stat[i] = 'unknown'
                    break
        return self.stat, self.results

    def Stop_devices(self):
        print("Communicator: Delete child PIPE before triggering Kill Queue...")
        for pi in self.ch_conns:
            pi.close()

        for i in enumerate(self.processes):
            self.kill_queue.put(True)
            print("Communicator: Waiting for processes to finish...")



class Dev_Communicator():
    def __init__(self):
        pass

    def Send_data(self, to_send):
        self.chc.send(to_send)  # connect to device to send data to main.py

    def Camera_detect_queue(self, detect_queue, data):
        detect_queue.put(data)

    def Poll_queue_better(self):
        if not self.kq.empty():
            kill_flag = self.kq.get()
            print("Child({}): Got {} from kill_queue...".format(self.mypid, kill_flag))
            return kill_flag
        else:
            return False



class Graceful_Killer:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.Exit_gracefully)
        signal.signal(signal.SIGTERM, self.Exit_gracefully)

    def Exit_gracefully(self, signum, frame):
        self.kill_now = True
        print("\n")
        print("Caught an interupt signal... cleaning up...")
        print("Terminating processes...", process.terminate())
        sys.exit(0)

# EOF
