from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic


class MAIN(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)