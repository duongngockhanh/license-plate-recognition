import typing
import cv2
import numpy as np
import sys
import os
from datetime import datetime
from PIL import ImageQt, Image
import time
sys.path.append("../")

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import uic
from PyQt5.QtCore import Qt, QObject, QTimer, QThread, pyqtSignal, pyqtSlot ######## Khanh 0: Add the library

from lpr.lprecg import LPRecognizer
from queue import Queue 

UPLOAD_DIR = "./my_bike"

def uploadFile(image, file_name):
    if not os.path.exists(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)

    timeTerm: str = datetime.now().strftime('%Y%m%d%H%M%S')
    imageName: str = f'{timeTerm}-{os.path.basename(file_name)}'
    imagePath: str = os.path.join(UPLOAD_DIR, imageName)
    cv2.imwrite(imagePath, image)

    return imagePath

class VideoThread(QThread):
    video_processed = pyqtSignal(np.ndarray)
    infer_signal = pyqtSignal(np.ndarray)

    def __init__(self, *args, video_path, height_video, width_video, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_path = video_path
        self.height_video = height_video
        self.width_video = width_video
    def run(self):
        video_capture = cv2.VideoCapture(self.video_path)
        frame_count = 0
        frame_to_display = 30
        while video_capture.isOpened() :
            ret, frame = video_capture.read()
            if not ret:
                break
            if frame_count % frame_to_display == 0:
                self.infer_signal.emit(frame)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_image = cv2.resize(rgb_image, (self.width_video, self.height_video))
            self.video_processed.emit(rgb_image)

            frame_count += 1
            self.spin(0.03)

        video_capture.release()
        black_frame = np.zeros((self.height_video, self.width_video, 3), dtype=np.uint8)
        self.video_processed.emit(black_frame)

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QApplication.processEvents()

class InferThread(QThread):
    infer_processed = pyqtSignal(list, list, list)
    

    def __init__(self, *args, lprecognizer, **kwargs):
        super().__init__(*args, **kwargs)
        self.lprecognizer = lprecognizer
        # self.rgb_image = None
        self.my_queue = Queue(maxsize=30)
    
    @pyqtSlot(np.ndarray)
    def receive_infer_signal(self, rgb_image):
        # self.rgb_image = rgb_image
        self.my_queue.put(rgb_image)
        # print(self.my_queue.qsize())

    def run(self):
        while True:
            if self.my_queue.empty():
                # print(self.my_queue.qsize())
                continue
            else:
                infered_img = self.my_queue.get()
                start_time = time.time()
                list_txt, scores, list_iplates = self.lprecognizer.infer(infered_img)
                print(time.time() - start_time)
                self.infer_processed.emit(list_txt, scores, list_iplates)
                self.my_queue.task_done()

    # def spin(self, seconds):
    #     """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

    #     time_end = time.time() + seconds
    #     while time.time() < time_end:
    #         QApplication.processEvents()

def convert2pixmap(img):
    h, w, ch = img.shape
    image = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
    image = image.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    return QPixmap.fromImage(image)

class IN(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("in.ui", self)
        self.lprecognizer = LPRecognizer()

        self.btnChooseFile.clicked.connect(self.vehicleIN)
        
        self.video_thread = VideoThread(video_path="videos/a4_car.mp4", height_video=self.lblImgCar.size().height(), width_video=self.lblImgCar.size().width(), parent=self)
        self.infer_thread = InferThread(lprecognizer=self.lprecognizer, parent=self)

        self.video_thread.video_processed.connect(self.update_video_lblImgCar)
        self.video_thread.infer_signal.connect(self.infer_thread.receive_infer_signal)
        self.infer_thread.infer_processed.connect(self.update_infer_lblImgCar)

    def vehicleIN(self):
        self.video_thread.start()
        self.infer_thread.start()

    @pyqtSlot(np.ndarray)
    def update_video_lblImgCar(self, rgb_image):
        pixmap = convert2pixmap(rgb_image)
        self.lblImgCar.setPixmap(pixmap)

    @pyqtSlot(list, list, list)
    def update_infer_lblImgCar(self, list_txt, scores, list_iplates):
        if scores:
            #inference info
            text = list_txt[scores.index(max(scores))]
            plate = list_iplates[list_txt.index(text)]
            
            #time info
            timeIN = datetime.now()
            strTimeIN = timeIN.strftime('%Hh%Mp')
            strDayIN = timeIN.strftime('%d/%m/%Y')
            
            #image
            self.lblPlateCar.setScaledContents(True)
            self.lblPlateCar.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
            
            #information
            self.lblCarDayIn.setText(strDayIN)
            self.lblCarTimeIn.setText(strTimeIN)
            self.lblCarPlate.setText("\n" + text)

    
    '''
    def vehicleIN(self):
        start_time = time.time()
        #read image 
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image File", r"../image_test", "Image files (*.jpg *.jpeg *.png)")


        #licence plate recognizer
        if fileName:
            image = cv2.imread(fileName)
            list_txt, scores, list_iplates = self.lprecognizer.infer(image)
            if scores:
                text = list_txt[scores.index(max(scores))]
                plate = list_iplates[list_txt.index(text)]
                print("text: ", type(text))
                print("plate: ", type(plate))
                print("scores: ", type(scores))

                #upload image
                _fileName = fileName.split(".")[0] + "_plate." + fileName.split(".")[1]
                filePath = uploadFile(image, fileName)
                _filePath = uploadFile(plate, _fileName)

                #set lane vehicle
                nameVehicle = os.path.dirname(fileName).split("/")[-1]

                timeIN = datetime.now()
                # strTimeIN = timeIN.strftime('%Hh%Mp - %d/%m/%Y')
                strTimeIN = timeIN.strftime('%Hh%Mp')
                strDayIN = timeIN.strftime('%d/%m/%Y')
                idCard = os.path.basename(fileName.split(".")[0])


                if nameVehicle == "car":
                    #car image
                    self.lblImgCar.setScaledContents(True)
                    self.lblImgCar.setPixmap(QPixmap(fileName))
                    #plate image
                    self.lblPlateCar.setScaledContents(True)
                    self.lblPlateCar.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
                    # self.lblPlateCar.setPixmap(QPixmap(_filePath))
                    #information
                    self.lblCarDayIn.setText(strDayIN)
                    self.lblCarTimeIn.setText(strTimeIN)
                    self.lblCarPlate.setText("\n" + text)
                    self.lblCarID.setText(idCard)
                else:
                    #motobike image
                    self.lblImgMotobike.setScaledContents(True)
                    self.lblImgMotobike.setPixmap(QPixmap(fileName))
                    #plate image
                    self.lblPlateMotobike.setScaledContents(True)
                    # self.lblPlateMotobike.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
                    self.lblPlateMotobike.setPixmap(QPixmap(_filePath))
                    #information
                    self.lblMotobikeDayIn.setText(strDayIN)
                    self.lblMotobikeTimeIn.setText(strTimeIN)
                    self.lblMotobikePlate.setText("\n" + text)
                    self.lblMotobikeID.setText(idCard)

                document = card_collection.find_one({"Mã thẻ": idCard})
                if document is None:
                    # messageCheckRegis()
                    if nameVehicle == "car":
                        self.lblCarMessage.setText("THẺ KHÔNG TỒN TẠI")
                        self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                    else:
                        self.lblMotobikeMessage.setText("THẺ KHÔNG TỒN TẠI")
                        self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                elif document["Loại thẻ"] == "Thẻ tháng":
                    if document["Biển số"] == "":
                        if nameVehicle == "car":
                            self.lblCarMessage.setText("THẺ CHƯA ĐƯỢC ĐĂNG KÝ")
                            self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                        else:
                            self.lblMotobikeMessage.setText("THẺ CHƯA ĐƯỢC ĐĂNG KÝ")
                            self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                    else:
                        valuesList = list(manager_collection.find_one({"Mã thẻ": idCard}).values())
                        if nameVehicle == "car":
                            if not checkDate(valuesList[6], valuesList[7], timeIN):
                                # messageCheckDate()
                                self.lblCarMessage.setText("THẺ HẾT HẠN")
                                self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                            elif valuesList[4] == text:
                                if in_collection.find_one({"Mã thẻ": idCard}) is not None:
                                    self.lblCarMessage.setText("THẺ ĐANG ĐƯỢC SỬ DỤNG")
                                    self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                                else:
                                    status = "In"
                                    add2In(filePath, idCard, text, valuesList[11], "Ô tô", timeIN, status)
                                    self.lblCarMessage.setText("XIN MỜI VÀO")
                                    self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: green}')
                            else:
                                # messageCheckIn()
                                self.lblCarMessage.setText("BIỂN SỐ KHÔNG HỢP LỆ")
                                add2In(filePath, idCard, text, valuesList[11], "Ô tô", timeIN, status)
                                self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                        else:
                            if not checkDate(valuesList[6], valuesList[7], timeIN):
                                # messageCheckDate()
                                self.lblMotobikeMessage.setText("THẺ HẾT HẠN")
                                self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                            elif valuesList[4] == text:
                                if in_collection.find_one({"Mã thẻ": idCard}) is not None:
                                    self.lblMotobikeMessage.setText("THẺ ĐANG ĐƯỢC SỬ DỤNG")
                                    self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                                else:
                                    status = "In"
                                    add2In(filePath, idCard, text, valuesList[11], "Xe máy", timeIN, status)
                                    self.lblMotobikeMessage.setText("XIN MỜI VÀO")
                                    self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: green}')
                            else:
                                # messageCheckIn()
                                self.lblMotobikeMessage.setText("BIỂN SỐ KHÔNG HỢP LỆ")
                                add2In(filePath, idCard, text, valuesList[11], "Xe máy", timeIN, status)
                                self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                else:
                    if document["Biển số"] != "":
                        if nameVehicle == "car":
                            self.lblCarMessage.setText("THẺ ĐANG ĐƯỢC SỬ DỤNG")
                            self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                        else:
                            self.lblMotobikeMessage.setText("THẺ ĐANG ĐƯỢC SỬ DỤNG")
                            self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                    else:
                        if nameVehicle == "car":
                            status = "In"
                            add2In(filePath, idCard, text, "Vé lượt", "Ô tô", timeIN, status)
                            self.lblCarMessage.setText("XIN MỜI VÀO")
                            self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: orange}')
                        else:
                            status = "In"
                            add2In(filePath, idCard, text, "Vé lượt", "Xe máy", timeIN, status)
                            self.lblMotobikeMessage.setText("XIN MỜI VÀO")
                            self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: orange}')
                        card_collection.find_one_and_update({"Mã thẻ": idCard}, {"$set": {"Biển số": text, "Trạng thái": "Đã sử dụng"}})

        print(time.time() - start_time)

    '''