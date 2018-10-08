from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QWidget
from model import *

class EEGController(QWidget):
        def __call__(self):
            self.open()

        def __init__(self, model):
            super().__init__()
            self.model = model

        def open(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                self.model.set_filepath(fileName)
                self.model.load_eeg_file()
