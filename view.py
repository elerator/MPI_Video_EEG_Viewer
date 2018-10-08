from PyQt5 import QtGui,QtCore
import sys
import numpy as np
import pylab
import time
import pyqtgraph
from PyQt5.QtGui import QGraphicsView
from pyqtgraph import PlotWidget, PlotItem
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QSizePolicy, QSlider)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
        QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QLabel, QSpinBox)

from model import *
from controller import *

import random

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


def _translate(context, text, disambig):
    return QtGui.QApplication.translate(context, text, disambig)

class MainApp(QtGui.QMainWindow):
    eeg_displays = [] #type DataView
    models = []

    def __init__(self, data_models, video, parent=None):
        super(MainApp, self).__init__(parent)
        self.models = data_models#type eeg display
        self.video = video#type video display
        self.eeg_displays == None

        # Subscribe: Add self to all models that will be displayed in it (i.e. all models)
        for m in self.models:
            m.add_observer(self)
        self.video.add_observer(self)

        #Draw User Interface
        pyqtgraph.setConfigOption('background', 'w') #White background
        self.resize(1280, 640)
        #app.aboutToQuit.connect(app.deleteLater)

        self.setupUi()

    def add_data_display(self):
        #Create new MODEL and append it to self.models
        model = EEGModel()
        self.models.append(model)

        #Subscribe
        model.add_observer(self)

        #Create VIEW and add it (widget) to layout
        optiondisplay = DataView(model)
        self.eeg_displays.append(optiondisplay)
        self.verticalLayout.addWidget(optiondisplay)

        #redraw Add button at bottom
        self.verticalLayout.removeWidget(self.addDataDisplays)
        self.verticalLayout.addWidget(self.addDataDisplays)

    def setupUi(self):
        self.centralwidget = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        self.verticalLayout.removeWidget
        self.video_view = VideoPlot(self.video)
        self.verticalLayout.addWidget(self.video_view)#ADD VIDEO HERE
        self.video_view.update()

        self.sld = QSlider(Qt.Horizontal, self)
        self.sld.setRange(0, 10000)
        self.verticalLayout.addWidget(self.sld)
        self.sld.setTickPosition(QSlider.TicksAbove)

        self.sld.valueChanged.connect(self.video.change_time_to)

        #Draw (+) button to add data displays
        # Connect navigation elements to respective slots

        self.addDataDisplays = QtGui.QPushButton(self.centralwidget)
        self.verticalLayout.addWidget(self.addDataDisplays)
        self.addDataDisplays.setText("+")
        self.addDataDisplays.clicked.connect(self.add_data_display)

        #Draw EEG models
        self.draw_eeg_models()
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle(QtGui.QApplication.translate("EEG Viewer", "EEG Viewer", None))
        QtCore.QMetaObject.connectSlotsByName(self)

    def update(self, msg = ""):
        if(type(self.eeg_displays)==type(None)):
            return -1 #No update if not already GUI was initialized

        if(msg=="video"):
            self.video_view.update()

        elif(msg == "eeg"):
            for m,view,count in zip(self.models,self.eeg_displays,range(0,len(self.eeg_displays))):
                if(type(m) == type(EEGModel())):
                    if(m.deleted()):
                        del(self.eeg_displays[count])
                        del(self.models[count])
                        self.setupUi()
                        view.update()

        else:#Update all views
            self.video_view.update()
            for m,view,count in zip(self.models,self.eeg_displays,range(0,len(self.eeg_displays))):
                if(type(m) == type(EEGModel())):
                    if(m.deleted()):
                        del(self.eeg_displays[count])
                        del(self.models[count])
                        self.setupUi()
                        view.update()
                    else:
                        view.update()



    def draw_eeg_models(self):
        self.eeg_displays=[]#Make sure list is empty BEEEEEFORE redrawing!!!

        for m in self.models:
            if(type(m) == type(EEGModel())):
                wrapped = DataView(m)

                self.eeg_displays.append(wrapped)
                self.verticalLayout.addWidget(wrapped)
                self.verticalLayout.removeWidget(self.addDataDisplays)
                self.verticalLayout.addWidget(self.addDataDisplays)


class DataView(QWidget):

    def __init__(self, model, parent=None):
        super(QtGui.QWidget,self).__init__(parent)
        self.model = model
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.setLayout(self.horizontalLayout)####IMPORTANT

        self.setMinimumSize(120, 120)

        self.grPlot = InteractiveDataPlot(self.model, self)
        self.horizontalLayout.addWidget(self.grPlot)

        self.horizontalLayout.addWidget(self.createOptionsGroup())

    def update(self):
        self.grPlot.plot()
        self.l1.setText("Channel: " + str(self.model.get_channel()))
        self.groupBox.setTitle(self.model.get_title())


    def createOptionsGroup(self):
        self.groupBox = QGroupBox(self.model.get_title())
        self.groupBox.setAlignment(4)

        self.load_button = QtGui.QPushButton()
        self.close_button = QtGui.QPushButton()

        self.l1 = QLabel("Channel: " + str(self.model.get_channel()))
        self.spin_box = QSpinBox()

        vbox = QVBoxLayout()
        vbox.addWidget(self.l1)
        vbox.addWidget(self.spin_box)
        vbox.addWidget(self.load_button)
        vbox.addWidget(self.close_button)

        self.load_button.setText("Load...")
        self.close_button.setText("Close")

        #USE EEG DISPLAY CONTROLLER TO HAVE THE MODEL LOAD ITS DATA
        loader = EEGController(self.model)
        self.load_button.clicked.connect(loader)

        #LET THE MODEL COMMUNICATE IT'S DEAD
        self.close_button.clicked.connect(self.delete)

        #Use spin box to switch through channels
        self.spin_box.valueChanged.connect(self.model.set_channel)

        vbox.addStretch(1)
        self.groupBox.setLayout(vbox)

        return self.groupBox

    def delete(self):
        self.model.delete()

class VideoPlot(QGraphicsView):
    def __init__(self, video, parent=None):
        super(VideoPlot, self).__init__(parent)
        self.video = video
        self.parent=parent
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.setMinimumSize(120, 210)

        #Create Layout and add self
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.canvas.show()

    def update(self):
        self.figure.clear()
        self.axes=self.figure.add_subplot(1,1,1)
        frame = self.video.get_frame()
        im = self.axes.imshow(frame)
        self.figure.subplots_adjust(left=0.0,bottom=0.0, top=1.0, right = 1.0)#Dont waste space
        self.axes.axis('off')
        self.canvas.draw()
        self.canvas.show()


class DataPlot(FigureCanvas):
    def __init__(self, model, parent=None, width=5, height=4, dpi=100):
        self.model = model

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        data = self.model.get_data()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(data, 'r-')
        ax.set_title(self.model.get_title())
        self.draw()

class InteractiveDataPlot(PlotWidget):
    def __init__(self, model, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.model = model
        self.plot()

    def plot(self):
        data = self.model.get_data()
        X=np.arange(len(data))
        C=pyqtgraph.hsvColor(1)
        pen=pyqtgraph.mkPen(color=C,width=1)
        self.getPlotItem().plot(X,data,pen=pen,clear=True)
        #PlotItem.plot(X,data,pen=pen,clear=True)
