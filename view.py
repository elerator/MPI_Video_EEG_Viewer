from PyQt5 import QtGui,QtCore
import sys
import numpy as np
import pylab
import time
import pyqtgraph
from PyQt5.QtGui import QGraphicsView, QPixmap, QImage, QFrame, QScrollArea
from pyqtgraph import PlotWidget, PlotItem
from PyQt5.QtCore import Qt, QObject, QEvent
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

    def __init__(self, data_models, video, parent=None):
        super(MainApp, self).__init__(parent)
        self.video = video

        #Draw User Interface
        pyqtgraph.setConfigOption('background', 'w') #White background
        self.resize(1280, 640)
        self.setupUi(data_models, video)

        #Make additional connections
        video.frame.connect(self.video_view.video_plot.update)


    def setupUi(self, data_models, video_model):
        # 1. Create Widget
        self.centralwidget = QtGui.QWidget(self)

        #2. Create a couple of elements
        self.video_view = VideoView(self.video)#VideoPlot(self.video)
        self.video_view.update()

        self.sld = QSlider(Qt.Horizontal, self)
        self.sld.setRange(0, self.video.get_amount_of_frames()-1)
        self.sld.setTickPosition(QSlider.TicksAbove)

        self.listWidget = DataListView(data_models, video_model)

        #3.Create Layout
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        #4. Add elements to layout
        self.verticalLayout.addWidget(self.video_view)#ADD VIDEO HERE
        self.verticalLayout.addWidget(self.sld)

        #TODO
        self.verticalLayout.addWidget(self.listWidget)

        #5. Connect navigation elements to respective slots
        self.sld.valueChanged.connect(self.video.set_framenumber)

        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle(QtGui.QApplication.translate("EEG Viewer", "EEG Viewer", None))

        #QtCore.QMetaObject.connectSlotsByName(self)

class DataListView(QWidget):
    def __init__(self, datamodels = [], videomodel = None, parent = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        self.videomodel = videomodel
        self.datamodels = []#Use self.add_data_display() tQtGui.QListWidget(self.centralwidget)o append
        self.dataviews = []
        pyqtgraph.setConfigOption('background', 'w') #White background
        self.setup_ui(datamodels)
        self.addDataDisplays.clicked.connect(self.add_data_display)


    def setup_ui(self, datamodels):
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.red)
        self.setPalette(p)

        self.datamodels = []#Use self.add_data_display() to append
        self.dataviews = []

        self.centralwidget = QtGui.QWidget(self)
        #self.centralwidget.setMinimumSize(600, 400)

        self.scrollarea = QScrollArea(self)
        self.scrollarea.setWidgetResizable(True)

        #Create layout
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        #Create couple of elements
        self.addDataDisplays = QtGui.QPushButton(self) #Draw (+) button to add data displays
        self.addDataDisplays.setText("+")
        #self.verticalLayout.addWidget(self.addDataDisplays)

        for model in datamodels:
            self.add_data_display(model)
            self.datamodels.append(model)

        #add elements to layout
        self.scrollarea.setGeometry(self.geometry())
        self.scrollarea.setWidget(self.centralwidget)

    def delete(self, datadisplay):
        self.verticalLayout.removeWidget(self.addDataDisplays)

        idx = self.dataviews.index(datadisplay)

        readd_models = self.datamodels.copy()
        del readd_models[idx]

        self.datamodels = []#Use self.add_data_display() to append
        self.dataviews = []

        self.centralwidget = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        for model in readd_models:
            self.add_data_display(model)
            #self.datamodels.append(model)

        self.scrollarea.setWidget(self.centralwidget)

        #redraw Add button at bottom
        self.verticalLayout.addWidget(self.addDataDisplays)

    def add_data_display(self, model = None):
        self.verticalLayout.removeWidget(self.addDataDisplays)

        #Create new MODEL and append it to self.models
        if type(model) != type(DataModel()):
            model = DataModel()

        self.datamodels.append(model)#


        #Create VIEW and add it (widget) to layout
        optiondisplay = DataView(model, video_model = self.videomodel, container = self)#such that child can tell parent it's dead
        self.dataviews.append(optiondisplay)
        self.verticalLayout.addWidget(optiondisplay)

        self.verticalLayout.addWidget(self.addDataDisplays)

        #Subscribe
        self.videomodel.eeg_pos.connect(optiondisplay.data_plot.update)
        model.channeldata.connect(optiondisplay.data_plot.print_data)


class VideoView(QWidget):
    def __init__(self, video_model = None, parent=None):
        #1. Create the widget i.e. self by calling superclass
        super(QtGui.QWidget,self).__init__(parent)
        self.video_model = video_model

        #2. Create a couple of elements
        self.video_plot = VideoPlot(self.video_model, self)
        self.options_group = self.createOptionsGroup()
        self.video_surrounding = QFrame()

        # 2a: Create Window that will open upon button press
        self.dialog = MotionWindowSelector(video=video_model, parent = self)

        #3. Create and set layout
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.setLayout(self.horizontalLayout)####IMPORTANT
        self.setMinimumSize(120, 120)

        #self.video_surrounding_layout = QtGui.QHBoxLayout()
        #self.video_surrounding.setLayout(self.video_surrounding_layout)

        #4. Add elements to widget
        #self.video_surrounding_layout.addWidget(self.video_plot)
        #self.horizontalLayout.addWidget(self.video_surrounding)
        self.horizontalLayout.addWidget(self.video_plot)
        self.horizontalLayout.addWidget(self.options_group)

    #@pyqtSlot()
    def update(self, msg = ""):
        self.video_plot.update()
        self.l1.setText("Channel:")

    def createOptionsGroup(self):
        #1. Create a widget (here: QGroupBox)
        self.groupBox = QGroupBox()
        self.groupBox.setAlignment(4)

        #2. Create a couple of elements
        self.load_button = QtGui.QPushButton()
        self.load_button.setText("Load...")
        self.close_button = QtGui.QPushButton()
        self.open_dialog = QtGui.QPushButton()
        self.open_dialog.setText("Specify Motion ROI")
        self.frame_forward = QtGui.QPushButton()
        self.frame_back = QtGui.QPushButton()
        self.play = QtGui.QPushButton()
        self.reverse_play = QtGui.QPushButton()
        self.stop_vid = QtGui.QPushButton()

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/frame_back.png"))
        self.frame_back.setIcon(icon)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/play.png"))
        self.play.setIcon(icon)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/stop.png"))
        self.stop_vid.setIcon(icon)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/frame_forward.png"))
        self.frame_forward.setIcon(icon)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/reverse_play.png"))
        self.reverse_play.setIcon(icon)

        self.close_button.setText("Close")
        self.l1 = QLabel("Video")
        self.spin_box = QSpinBox()

        #3. Add them to a QVBoxLayout (Vertical)
        vbox = QVBoxLayout()
        vbox.addWidget(self.l1)
        vbox.addWidget(self.spin_box)
        vbox.addWidget(self.load_button)
        vbox.addWidget(self.close_button)
        vbox.addWidget(self.open_dialog)

        vbox.addWidget(self.stop_vid)#
        vbox.addWidget(self.play)#
        vbox.addWidget(self.reverse_play)#
        vbox.addWidget(self.frame_forward)#
        vbox.addWidget(self.frame_back)#
        vbox.addStretch(1)#Add empty QSpacerItem that pushes the buttons upwards

        #4. Add layout to widget
        self.groupBox.setLayout(vbox)

        #5. connect
        self.open_dialog.clicked.connect(self.choose_ROI)
        self.frame_forward.clicked.connect(self.video_model.frame_forward)
        self.frame_back.clicked.connect(self.video_model.frame_back)
        self.play.clicked.connect(self.video_model.start_play)
        self.stop_vid.clicked.connect(self.video_model.stop_play)

        return self.groupBox

    def choose_ROI(self):
        self.dialog.show()

class DataView(QWidget):

    def __init__(self, model, video_model = None, container = None, parent=None):#Parent is container
        super(QtGui.QWidget,self).__init__(parent)
        self.model = model
        self.video_model = video_model
        self.container = container
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.setLayout(self.horizontalLayout)####IMPORTANT

        self.setMinimumSize(120, 120)

        self.data_plot = InteractiveDataPlot(self.model, self.video_model, self)
        self.horizontalLayout.addWidget(self.data_plot)
        self.horizontalLayout.addWidget(self.createOptionsGroup())

    def update(self, msg = ""):
        self.data_plot.update(msg)
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

        #USE EEG DISPLAY CONTROLLER TO HAVE THE MDataVODEL LOAD ITS DATA
        loader = DataController(self.model)
        self.load_button.clicked.connect(loader)

        #LET THE MODEL COMMUNICATE IT'S DEAD
        self.close_button.clicked.connect(self.delete)

        #Use spin box to switch through channels
        self.spin_box.valueChanged.connect(self.model.set_channel)

        vbox.addStretch(1)
        self.groupBox.setLayout(vbox)

        return self.groupBox

    def delete(self):
        self.container.delete(self)

class VideoPlot(QFrame):

    def __init__(self, video, parent=None, centered = True):
        super(VideoPlot, self).__init__(parent)

        print("video_plot")

        self.video = video
        self.figure = plt.figure()
        #self.setStyleSheet("background-color: rgb(255,0,0); margin:1px; border:1px solid rgb(0, 255, 0); ")
        self.setStyleSheet("background-color: rgb(0,0,0); margin:-10px; border:-10px solid rgb(0, 255, 0); ")

        # Create couple of elements
        self.setMinimumSize(320, 180)
        self.label = QLabel(self)

        #self.horizontalSpacer = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        #Create Layout and add self
        layout = QtGui.QHBoxLayout()
        if(centered):
            layout.addWidget(QFrame())

        layout.addWidget(self.label)

        if(centered):
            layout.addWidget(QFrame())
        self.setLayout(layout)
        self.update()
        #def paintEvent(self, event):#Rescale picture in case of a paint event to fit dimesions


    def resizeEvent(self, event):
        size = self.label.size()
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
        self.label.setPixmap(scaledPix)

    def update(self, frame = None):
        if type(frame) == type(None):
            frame = self.video.get_frame()
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.pixmap = QtGui.QPixmap(image)
        size = self.label.size()
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)

        self.label.setPixmap(scaledPix)

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
        #ax.set_title(self.model.get_title())
        self.draw()

class InteractiveDataPlot(PlotWidget):
    def __init__(self, model, video_model = None, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)

        assert type(model) != type(True)

        self.main_plot = None
        self.indicator = None
        self.video_model = video_model
        self.model = model
        self.print_data()
        self.plot()

    def print_data(self):
        self.plot_item = self.getPlotItem()

        C=pyqtgraph.hsvColor(1)
        pen=pyqtgraph.mkPen(color=C,width=1)
        data = self.model.get_data()

        if(type(data)==type(None)):#In case we draw without having loaded
            data = np.zeros(10000)

        X=np.arange(len(data))
        self.indicator_min = int(np.nanmin(data))
        self.indicator_max = int(np.nanmax(data))
        self.main_plot = self.plot_item.plot(X,data,pen=pen,clear=True)

        pos = int(self.video_model.get_pos())

        self.indicator = self.plot_item.plot([pos,pos],[self.indicator_min,self.indicator_max],pen=pyqtgraph.mkPen(color=pyqtgraph.hsvColor(2),width=1))


    def update(self, pos = 0, msg = ""):
        if(msg == "eeg"):#EEG datamodel changed
            self.print_data()
        C=pyqtgraph.hsvColor(1)
        pen=pyqtgraph.mkPen(color=C,width=1)
        data = np.zeros(10)

        #if(not type(self.indicator)==type(None)):
        #    self.plot_item.removeItem(self.indicator)

        pos = int(self.video_model.get_pos())

        self.indicator.setData([pos,pos],[self.indicator_min,self.indicator_max]) #= self.plot_item.plot([pos,pos],[self.indicator_min,self.indicator_max],pen=pyqtgraph.mkPen(color=pyqtgraph.hsvColor(2),width=1))

        #PlotItem.plot(X,data,pen=pen,clear=True)

class MotionWindowSelector(QtGui.QMainWindow):
    def __init__(self, video, parent=None):
        super(MotionWindowSelector, self).__init__(parent)
        self.video = video

        # 1. Create Widget
        self.centralwidget = QtGui.QWidget(self)
        self.resize(800, 400)

        #2. Create a couple of elements
        self.box = SelectBoxOverlay()
        self.video_plot = VideoPlot(self.video, centered=False)
        self.video_plot.installEventFilter(self.box)

        #3.Create Layout
        self.verticalLayout = QtGui.QHBoxLayout(self.centralwidget)

        self.verticalLayout.addWidget(self.video_plot)#ADD VIDEO HERE
        self.verticalLayout.addWidget(self.createOptionsGroup())

        self.setLayout(self.verticalLayout)#First add to layout THEN setLayout THEN setCentralWidget that was used to create layout
        self.setCentralWidget(self.centralwidget)#Essential

    def createOptionsGroup(self):
        #1. Create a widget (here: QGroupBox)
        self.groupBox = QGroupBox()
        self.groupBox.setAlignment(4)

        #2. Create a couple of elements
        self.load_button = QtGui.QPushButton()
        self.load_button.setText("Load...")
        self.close_button = QtGui.QPushButton()
        self.open_dialog = QtGui.QPushButton()
        self.open_dialog.setText("Specify Motion ROI")

        self.close_button.setText("Close")
        self.l1 = QLabel("Video")
        self.spin_box = QSpinBox()

        #3. Add them to a QVBoxLayout (Vertical)
        vbox = QVBoxLayout()
        vbox.addWidget(self.l1)
        vbox.addWidget(self.spin_box)
        vbox.addWidget(self.load_button)
        vbox.addWidget(self.close_button)
        vbox.addWidget(self.open_dialog)
        vbox.addStretch(1)#Add empty QSpacerItem that pushes the buttons upwards

        #4. Add layout to widget
        self.groupBox.setLayout(vbox)

        return self.groupBox

class SelectBoxOverlay(QObject):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        self.overlay = None# assume overlay does not exist
        self.box_coordinates = [0,0,0,0]

    def eventFilter(self, w, event):
        if w.isWidgetType(): #Go through event types if a widget is passed

            #If overlay doesn't exist create it
            if not self.overlay:
                self.overlay = SelectBoxOverlay.Overlay(w.parentWidget())

            #Redirect event types:
            if event.type() == QEvent.MouseButtonPress:
                self.overlay.mousePressEvent(event)

            if event.type() == QEvent.MouseMove:
                self.overlay.mouseMoveEvent(event)

            if event.type() == QEvent.MouseButtonRelease:
                self.overlay.mouseReleaseEvent(event)

            elif event.type() == QEvent.Resize:#Upon resize
                if self.overlay: #If overlay exists (Python evaluates if None as False)
                    self.overlay.setGeometry(w.geometry())#set its geometry to widgets geometry which also causes paintEvent call

            #Set coordinates
            self.box_coordinates = self.overlay.get_box_coordinates()
        return False

    def get_box_coordinates(self):
        return self.box_coordinates

    def toggle_box(self):
        if self.overlay:
            self.overlay.show_box()

    class Overlay(QWidget):
        def __init__(self, parent = None):
            QWidget.__init__(self, parent)
            self.setAttribute(Qt.WA_NoSystemBackground)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.begin = QtCore.QPoint(0,0)
            self.end = QtCore.QPoint(0,0)
            self.permanent_show = True

        def get_box_coordinates(self):
            x = self.begin.x()
            y = self.begin.y()
            x1 = self.end.x()
            y1 = self.end.y()

            return [min(x,x1),min(y,y1),max(x,x),max(y,y1)]

        def show_box(self):
            self.permanent_show = not self.permanent_show

        def paintEvent(self, event):
            qp = QtGui.QPainter(self)
            br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 40))
            qp.setBrush(br)
            qp.drawRect(QtCore.QRect(self.begin, self.end))

        def mousePressEvent(self, event):
            self.begin = event.pos()
            self.end = event.pos()
            self.update()

        def mouseMoveEvent(self, event):
            self.end = event.pos()
            self.update()

        def mouseReleaseEvent(self, event):
            self.begin = event.pos()
            self.end = event.pos()
            if not self.permanent_show:
                self.update()
