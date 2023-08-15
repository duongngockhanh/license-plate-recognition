from PyQt5.QtWidgets import QApplication

from main import MAIN
from window_in_custom import IN
from window_out import OUT


class UI():
    def __init__(self):
        self.main = MAIN()
        self.main.show()

        self.main.btnIN.clicked.connect(lambda: self.changeUI("window_in"))
        self.main.btnOUT.clicked.connect(lambda: self.changeUI("window_out"))

        self.window_in = IN()
        self.window_in.btnBackIN.clicked.connect(lambda: self.changeUI("main"))

        self.window_out = OUT()
        self.window_out.btnBackOUT.clicked.connect(lambda: self.changeUI("main"))

    def changeUI(self, i):
        if i == "window_in":
            self.main.hide()
            self.window_in.show()
        elif i == "window_out":
            self.main.hide()
            self.window_out.show()
        elif i == "main":
            self.window_in.hide()
            self.window_out.hide()
            self.main.show()


if __name__ == "__main__":
    app = QApplication([])
    ui = UI()
    app.exec_()