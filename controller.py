from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QSpinBox, QVBoxLayout, QMessageBox)
from model import *

class DataController(QDialog):
        NumGridRows = 3
        NumButtons = 4

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
