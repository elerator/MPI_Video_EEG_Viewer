from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QSpinBox, QVBoxLayout, QMessageBox)
from model import *

class DataController(QDialog):
        NumGridRows = 3
        NumButtons = 4
        title = pyqtSignal(str)

        def __call__(self):
            self.show()

        def __init__(self, model):
            super().__init__()
            self.model = model
            self.setup_ui()
            self.database = self.model.database

            self.datatype = "eeg"
            self.dyad = 1
            self.channel_or_video = 1# Integer for channel or number of video

        def setup_ui(self):
            #super(Dialog, self).__init__()
            self.createFormGroupBox()

            buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttonBox.accepted.connect(self.check_input)
            buttonBox.rejected.connect(self.reject)

            mainLayout = QVBoxLayout()
            mainLayout.addWidget(self.formGroupBox)
            mainLayout.addWidget(buttonBox)
            self.setLayout(mainLayout)

            self.make_connections()

            self.setWindowTitle("Load Data ...")

        def make_connections(self):
            try:
                self.datatype.currentIndexChanged.connect(self.set_datatype)
                self.dyad.valueChanged.connect(self.set_dyad)#
                self.vid_or_channel.valueChanged.connect(self.set_channel_or_vid)
            except Exception as e:
                QMessageBox.about(self, "Invalid value", "The datapoint was not found in the database.\nPlease adjust your selection.\n"+str(e))

        def set_datatype(self, msg):
            if(msg == 0):
                self.datatype = "eeg"
            elif(msg == 1):
                self.datatype = "Motion"
            else:
                raise NotImplementedError("EEG and Motion-Data supported only")

        def set_dyad(self, n):
            try:
                self.database.dictionary[str(n)]
                self.dyad = n
            except KeyError:
                QMessageBox.about(self, "Invalid value", "The datapoint was not found in the database.\nPlease adjust your selection")

            self.title.emit("Dyad: " + str(n))


        def set_channel_or_vid(self, n):
            if(self.datatype == "eeg"):
                if((n < 0) or (n >= 64)):
                    raise ValueError("No such channel")
                else:
                    self.channel_or_video = n

            elif(self.datatype == "Motion"):
                try:
                    self.database.dictionary[self.dyad]["motion"]["videos"][str(n)]
                    self.channel_or_video = n
                except KeyError:
                    QMessageBox.about(self, "Invalid value", "The datapoint was not found in the database.\nPlease adjust your selection")
                    #raise ValueError("No such value")
            else:
                raise NotImplementedError


        def createFormGroupBox(self):
            self.formGroupBox = QGroupBox("Select from database")
            layout = QFormLayout()

            self.dyad = QSpinBox()
            layout.addRow(QLabel("Dyad:"), self.dyad)

            self.datatype = QComboBox()

            self.datatype.addItem("EEG")
            self.datatype.addItem("Motion")

            self.vid_or_channel =  QSpinBox()

            layout.addRow(QLabel("Data Type:"), self.datatype)
            layout.addRow(QLabel("Video/Channel:"), self.vid_or_channel)

            #layout.addRow(QLabel("Name:"), QLineEdit())
            self.formGroupBox.setLayout(layout)

        def check_input(self):
            try:
                if(self.datatype == "eeg"):
                    self.model.set_datatype(self.datatype)
                    self.model.set_dyad(self.dyad)
                    self.model.set_channel(self.channel_or_video)
                elif(self.datatype == "Motion"):
                    self.model.set_filepath(self.database.dictionary[self.dyad]["Motion"][self.channel_or_video]["path"])
                    self.model.set_channel(0)
                else:
                    QMessageBox.about(self, "Incorrect selection", "Choose datatype")

                self.accept()
            except Exception as e:
                QMessageBox.about(self, "Exception", str(e))
                QMessageBox.about(self, "Incorrect selection", "Please choose wisely")

        def open(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                self.model.set_filepath(fileName)
                self.model.load_eeg_file()

class MotionWindowSelector():
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(300, 300))

        self.lines = []

        self.xmin = 0
        self.xmax = 0
        self.ymin = 0
        self.ymax = 0

    def draw_rect(self, p1, p2):
        self.lines = []
        x1 = p1.x()
        x2 = p2.x()
        y1 = p1.y()
        y2 = p2.y()

        self.xmin = min(x1,x2)
        self.xmax = max(x1,x2)
        self.ymin = min(y1,y2)
        self.ymax = max(y1,y2)

        xmin = min(x1,x2)
        xmax = max(x1,x2)
        ymin = min(y1,y2)
        ymax = max(y1,y2)

        self.lines.append(QLine(QPoint(xmin,ymin),QPoint(xmin,ymax)))
        self.lines.append(QLine(QPoint(xmin,ymax),QPoint(xmax,ymax)))
        self.lines.append(QLine(QPoint(xmax,ymax),QPoint(xmax,ymin)))
        self.lines.append(QLine(QPoint(xmax,ymin),QPoint(xmin,ymin)))
        self.update()


    def mousePressEvent(self,event):
        self.startx=event.x()
        self.starty=event.y()

    def mouseReleaseEvent(self,event):
        self.endx=event.x()
        self.endy=event.y()
        self.draw_rect(QPoint(self.startx,self.starty),QPoint(self.endx,self.endy))

    def paintEvent(self,event):
        QMainWindow.paintEvent(self, event)
        painter = QPainter(self)
        pen = QPen(Qt.black, 2, Qt.DashLine)

        painter.setPen(pen)
        for line in self.lines:
            painter.drawLine(line)
