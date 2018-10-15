#model
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from PyQt5.QtCore import pyqtSignal, QThread
from database import Database
import imageio
import time


class GlobalModel:
    def __init__(self):
        self.database = Database()
        self.database.load_json("database.json")
    def add_observer(self, observer):
        raise NotImplementedError

class VideoModel(QThread):
    total_frames = None
    observers = set()
    cap = None
    filepath = ""
    start_in_eeg = 0
    dyad = 0
    camera = 0
    read_frame_via_opencv = False

    frame = pyqtSignal(np.ndarray)
    framenumber = pyqtSignal(int)
    eeg_pos = pyqtSignal(int)


    def __init__(self, dyad, camera):
        super().__init__()
        self.database = Database()
        self.database.load_json("database.json")

        self.current_frame = 10
        self.dyad = dyad
        self.camera = camera
        self.filepath = self.get_filepath()
        self.cap = cv2.VideoCapture(self.filepath)
        self.video_reader = imageio.get_reader(self.filepath)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.set_start_pos()
        self.keep_playing = True # Finished flag

        if(self.filepath != None):
            self.parse_filepath_attributes()

    def start_play(self):
        self.playback_start_frame = self.get_framenumber()
        self.keep_playing = True
        self.start()# Start playback thread

    def stop_play(self):
        self.keep_playing = False

    def run(self):#Used by playback thread
        playback_start = time.time()
        pvrs = 0
        while(self.keep_playing):
            elapsed = time.time() - playback_start
            framenumber = self.playback_start_frame + int((elapsed/25)*620)#Why 600 not 1000?
            if(framenumber > pvrs):
                self.set_framenumber(framenumber)
            pvrs = framenumber
            #self.get_frame(via_emit = True)

    def parse_filepath_attributes(self):
        dyad = -1
        camera = -1
        try:
            dyad = int(re.search("P[0-9]+", self.filepath).group(0)[1:])
            camera = int(re.search("C[0-9]+", self.filepath).group(0)[1:])
        except:
            pass

        self.dyad = dyad
        self.camera = camera

    def get_start_pos(self):
        """ Returns beginning of video. Unit = EEG sampling frequency."""
        return self.start_in_eeg

    def set_dyad(self, dyad):
        self.dyad = dyad

    def set_start_pos(self):###########################!!!!!!!!!!!!!!!!!!!!!!!!!!toxic
        dyad = self.dyad
        pos = 10000000000000000
        pair = self.database.get_dict()
        try:
            for key, value in pair[str(dyad)]['eeg']['metainfo']['description'].items():#Search for R128
                if(value == 'R128'):
                    newpos = int(pair[str(dyad)]['eeg']['metainfo']['position'][key])
                    if(newpos < pos):#find smallest R128 value
                        pos = newpos
        except:
            pass

        if(pos == 10000000000000000):
            pos = 0

        self.start_in_eeg = pos

    def get_filepath(self):
        ret = None
        try:
            ret = self.database.dictionary[str(self.dyad)]['video'][str(self.camera)]['path']
        except:
            raise FileNotFoundError("Filepath not found in database")
        return ret

    def add_observer(self, observer):
        self.observers.add(observer)

    def get_pos(self):
        pos = self.get_start_pos()+(self.current_frame/25)*500
        return pos

    def get_frame(self, via_emit = False):
        frame = None
        if(self.read_frame_via_opencv):
            self.cap.set(1,self.current_frame)
            trial = 0
            ret = False
            while(not ret):
                ret, frame = self.cap.read()
                if(trial > 100):
                    break
            if(ret == False):
                raise FileNotFoundError("Opencv couldnt retrive frames")
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame = self.video_reader.get_data(self.current_frame)

        if(via_emit):
            self.frame.emit(frame)
        else:
            return frame

    def set_framenumber(self, x):
        if(x > self.total_frames):
            self.current_frame = self.total_frames-1
        else:
            self.current_frame = x

        self.framenumber.emit(x)
        self.eeg_pos.emit(self.get_pos())
        self.frame.emit(self.get_frame())#Necessary for sliderpos to update

    def get_framenumber(self):
        return self.current_frame

    def frame_forward(self):
        n = self.get_framenumber()+1
        if(n < self.get_amount_of_frames()):
            self.set_framenumber(n)

    def frame_back(self):
        n = self.get_framenumber()-1
        if(n >= 0):
            self.set_framenumber(n)

    def get_amount_of_frames(self):
        return self.total_frames

    #def add_observer(self, observer):
    #    self.observers.add(observer)

    #def notify_observers(self):
    #    self.msg_to_observers.emit("video")

class DataModel(GlobalModel):
    data = None
    filepath = None
    title = None
    channel = None
    observers = set()
    is_deleted = False #When model is to be removed

    def __init__(self, filepath = None, channel = 0, dyad = None, datatype = None):
        super().__init__()
        self.filepath = filepath
        self.is_deleted = False
        self.datatype = None

        if(channel!=None):
            self.channel = channel

        if(type(filepath) != type(None)):#Init with filepath
            #TODO check if .eeg in filepath and raise error otherwise
            self.set_filepath(filepath)
            self.load_eeg_file()

        elif(type(dyad) != type(None)):
            if(type(datatype) == type(None)):
                raise ValueError("Init via dyad requires specification of datatype")
            self.datatype = datatype
            self.set_dyad(dyad)#Also sets filepath

    def get_channel(self):
        return self.channel

    def set_datatype(self, datatype):
        self.datatype = datatype

    def set_dyad(self, dyad):
        self.dyad = dyad
        self.filepath = self.get_filepath()
        if(self.datatype == "eeg"):
            self.load_eeg_file()
        elif(self.datatype == None):
            pass
        else:
            raise NotImplementedError("Motion not supported yet")
        self.notify_observers()

    def get_filepath(self):
        if(self.datatype == "eeg"):
            try:
                ret = self.database.get_dict()[str(self.dyad)]['eeg']['path']
            except:
                raise FileNotFoundError("Filepath was not found in database")
            return ret
        elif(self.datatype == None):
            pass
        else:
            raise NotImplementedError("Motion not supported yet")

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

    def get_data(self):
        return self.data

    def delete(self):
        self.is_deleted = True
        self.notify_observers()

    def deleted(self):
        return self.is_deleted

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

        self.set_title(os.path.basename(self.filepath) )

        n_channels = 64
        bytes_per_sample = 2 #Because int16

        my_type = np.dtype([("channel"+str(x),np.int16) for x in range(0,n_channels)])
        byte_size = os.path.getsize(self.filepath)

        nFrames =  byte_size // (bytes_per_sample * n_channels);
        data = np.array(np.fromfile(self.filepath,dtype=my_type))["channel"+str(self.get_channel())]

        data = np.array(data, dtype= np.float32)
        data[data==32767] = np.nan
        data[data==-32768] = np.nan
        data[data==-32767] = np.nan

        self.data = data

        self.notify_observers()
