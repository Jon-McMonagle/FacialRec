import multiprocessing as mp
import os
import sys
from time import sleep
import signal
from tkinter import filedialog
import configparser

""" add ./devices to python path """
sys.path.append(os.path.expanduser("./devices"))


"""
    The modules should be imported as needed.
    That means they will be loaded AFTER config file is processed.
    For now the config file will be read as a part of MAIN_COMM class.
    Note: keys and values will be passed to devices incl. the bridge as
    a dictionary.
    There is no need to process config file repeatedly.
"""
try:
    import camera           # camera module
except ModuleNotFoundError as err:
    print("ERROR: {}!  Exitting ...".format(err))
    sys.exit(True)

class Main_Comm:
    def __init__(self, init_conf_path='.'):
        self.init_conf_path = init_conf_path
        mp.set_start_method('spawn')
        self.kill_queue = mp.Queue()
        self.save_queue = mp.Queue()   # Adding Save Queue
        self.p_conns = []
        self.ch_conns = []
        self.processes = []

        self.devs = self.Read_config()
        print("COMM: Devices from config: {}".format(self.devs))
        self.devs.remove('Bridge')
        print("COMM: Removed: {}".format(self.devs))
        # looking for key 'executable'
        to_run = []
        init_dict = []
        for d in self.devs:
            run = self.cfg[d]['executable']
            to_run.append(run)
            init_dict.append(self.cfg[d])

        print("All to run: {}".format(to_run))

        for pr, conf in zip(to_run, init_dict):     # self.devices or to_run
            run_me = pr
            # unidirectional pipe: p_conn <-- ch,conn
            self.p_conn, self.ch_conn = mp.Pipe(duplex=False)
            self.proc = mp.Process(target=eval(run_me), \
                    args=( \
                        conf,                 # device section of config
                        self.kill_queue,      # kill queue
                        self.ch_conn,         # CHILD end of the PIPE
                        self.save_queue,      # save queue for CAMERA
                        ))
            self.proc.start()
            self.p_conns.append(self.p_conn)
            self.ch_conns.append(self.ch_conn)
            self.processes.append(self.proc)

        self.results = [None] * len(self.processes)
        self.stat = [None] * len(self.processes)


    def Read_config(self):
        """
        Add some meaningful text here ... explain config strategy.
        """
        self.cfg_file = filedialog.askopenfilename(
                initialdir=".",\
                title="Select config file", initialfile="config.cfg",\
                filetypes=(("cfg files","*.cfg"),("all files","*.*")))

        print("COMM: Reading config file ...")

        try:
            os.path.isfile(self.cfg_file)
            self.cfg = configparser.ConfigParser()
            what_is_this = self.cfg.read(self.cfg_file)
            print("COMM: config file found .... {}".format(what_is_this))

            self.Bridge = self.cfg['Bridge']
            print("COMM: Config dictionary: ", self.Bridge)
        except TypeError:
            print("Empty path to cfg file! Default values are used ...")
        except configparser.MissingSectionHeaderError:
            print("Wrong file format! Default values are used ...")

        return self.cfg.sections()

    # Dummy function to pass devices to BRIDGE
    def Get_devices(self):
        return self.devs, self.Bridge


    def Pull_Data(self):
        for i, p_conn in enumerate(self.p_conns):
            #print("COMM: Pipe.poll() status: ", p_conn.poll())
            while p_conn.poll():
                try:
                    self.results[i] = p_conn.recv()
                    #print("COMM: p_conn.recv = {}".format(self.results[i]))
                    self.stat[i] = str(i)
                except EOFError as err:
                    #print("COMM: pipe is closed ... sending CLOSED ... LINUX")
                    self.results[i] = None
                    self.stat[i] = 'CLOSED'
                    break
                except BrokenPipeError as err2:         #needed on Windows
                    #print("COMM: pipe is closed ... sending CLOSED ... WINDOWS")
                    self.results[i] = None
                    self.stat[i] = 'CLOSED'
                    break
                except Exception as err:
                    #print("COMM: Other error ...", err)
                    self.results[i] = None
                    self.stat[i] = 'unknown'
                    break


        return self.stat, self.results

    def Camera_Saving(self, reftime):
        self.save_queue.put(reftime)

    def Stop_Devices(self):
        print("COMM: Delete child PIPE before triggerint kill.queue ...")
        for pi in self.ch_conns:
            pi.close()

        for i in enumerate(self.processes):
            self.kill_queue.put(True)
        """
        for proc in self.processes:
            proc.join()
        """
        print("MAIN_COMM: Waiting for processes to finish ...")

class Dev_communicator():
    def __init__(self):    # Added sq : Save Queue
        pass

    def send_data(self, to_send):
        # connect to device to send data to main.py
        self.chc.send(to_send)

    def camera_save_queue(self, save_queue):
        if not save_queue.empty():
            save_string = save_queue.get()
            return save_string
        else:
            return False

    def poll_queue_better(self):
        #print("CHILD: inside poll_queue function")
        if not self.kq.empty():
            kill_flag = self.kq.get()
            print("CHILD({}): Got {} from kill_queue ...".\
                    format(self.mypid, kill_flag))
            return kill_flag
        else:
            return False

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        print("\n")
        print("Caught an interrupt signal ... cleaning up ...")
        print("Terminating processes ...", process.terminate())
        sys.exit(0)

# EOF device_communicator.py
