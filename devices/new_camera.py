'''
Python script to control NoIR camera

Modules Installed:

- Tkinter: sudo apt-get install python3-tk
- OpenCV: sudo apt install python3-opencv
- Pip for installing certain packages: sudo apt-get install pip
- Pillow: sudo apt-get install python3-pillow
		: sudo apt-get install python3-pil.ImageTk 
- Numpy: should already be in your library

'''


import tkinter as tk
import cv2
import PIL
#from PIL import ImageTk, Image
import time
import os
import random
import numpy as np


class Controls(tk.Frame):
	def __init__(self):
		super().__init__(parent)
		pass


class Frame_Image(tk.Frame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		#background
		bg1 = "blue"

		self.config(bg=bg1)
		self.config(width=650)
		self.config(height=500)
		self.config(bd=2) #border
		self.config(relief="ridge")
		self.grid_propagate(False) # prevents resizing

class Frame_Info(tk.Frame):
	def __init__(self, parent):
		tk.Frame.__init__(self, parent)
		self.parent=parent
		#background
		bg1="grey"
		wid=200
		self.config(bg=bg1)
		self.config(width=wid)
		self.config(height=500)
		self.config(bd=2)
		self.config(relief="ridge")
		self.grid_propagate(False) # prevents resizing

		# Creating lists
		Label_name = tk.Label(self, text="Camera settings", bg=bg1)








































