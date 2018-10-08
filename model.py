#model
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from PyQt5.QtCore import pyqtSignal, QThread

class GlobalModel:
    def add_observer(self, observer):
        raise NotImplementedError

class VideoModel(GlobalModel):
    total_frames = None
    observers = set()
    cap = None
    filepath = ""

    def __init__(self, filepath = None):
        self.current_frame = 10
        self.filepath = filepath
        self.cap = cv2.VideoCapture(self.filepath)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.factor = self.total_frames//10000

    def add_observer(self, observer):
        self.observers.add(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update("video")

    def change_time_to(self, pos_in_time):
        self.set_current_video_frame(pos_in_time//self.factor)
        self.notify_observers()


    def get_frame(self):
        self.cap.set(1,self.current_frame)
        ret, frame = self.cap.read()
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #return self.cap.retrieve(self.current_frame)[1]

    def set_current_video_frame(self, x):
        #print("The position in the video is " + str(x))
        if(x > self.total_frames):
            self.current_frame = self.total_frames-1
        else:
            self.current_frame = x


    def get_amount_of_frames():
        return self.total_frames

    def add_observer(self, observer):
        self.observers.add(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update()

class EEGModel(GlobalModel):
    data = None
    filepath = None
    title = None
    channel = None
    updated = pyqtSignal()
    observers = set()
    is_deleted = False #When model is to be removed

    def get_channel(self):
        return self.channel

    def set_channel(self, channel):
        self.channel = channel
        self.load_eeg_file()
        self.notify_observers()

    def set_filepath(self, filepath):
        self.filepath = filepath
        self.set_title(os.path.basename(self.filepath) + "    Channel " + str(self.channel))

    def set_title(self, title):
        self.title = title

    def get_title(self):
        return self.title

    def get_filepath(self, filepath):
        return self.filepath

    def get_data(self):
        return self.data

    def delete(self):
        self.is_deleted = True
        self.notify_observers()

    def deleted(self):
        return self.is_deleted

    def __init__(self, filepath = None, channel = 0):
        self.filepath = filepath
        self.is_deleted = False

        if(channel!=None):
            self.channel = channel

        if(filepath != None):
                self.set_filepath(filepath)
                self.load_eeg_file()
        else:
            self.filepath = "Load data...!"
            self.data = np.zeros(100)
        self.set_title(os.path.basename(self.filepath) + "    Channel " + str(self.channel) )

    def add_observer(self, observer):
        self.observers.add(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update("eeg")

    def change_channel(self, channel):
        self.channel = channel
        self.load_eeg_file()
        self.notify_observers(self)

    def load_eeg_file(self):
        if(self.filepath==None):
            print("No filepath set")
            return None

        n_channels = 64
        bytes_per_sample = 2 #Because int16

        my_type = np.dtype([("channel"+str(x),np.int16) for x in range(0,n_channels)])
        byte_size = os.path.getsize(self.filepath)

        nFrames =  byte_size // (bytes_per_sample * n_channels);
        self.data = np.fromfile(self.filepath,dtype=my_type)["channel"+str(self.channel)]

        self.notify_observers()
