import cv2
import sys
import os
from datetime import datetime
from PIL import ImageQt, Image
sys.path.append("../")

from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

from lpr.lprecg import LPRecognizer

from pymongo import MongoClient
cluster = "mongodb+srv://tuyennt:0711@lpr.3u3tc8j.mongodb.net/test"
client = MongoClient(cluster)
db = client.lpr
in_collection = db.in_collection
manager_collection = db.manager_collection
card_collection = db.card

UPLOAD_DIR = "../upload"


def uploadFile(image, file_name):
    if not os.path.exists(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)

    timeTerm: str = datetime.now().strftime('%Y%m%d%H%M%S')
    imageName: str = f'{timeTerm}-{os.path.basename(file_name)}'
    imagePath: str = os.path.join(UPLOAD_DIR, imageName)
    cv2.imwrite(imagePath, image)

    return imagePath

def add2In(filePath, idCard, textLPR, cardType, vehicle, timeIN, status):
    dbIn = {"Image Path": filePath, "Mã thẻ": idCard, "Biển số": textLPR, "Loại vé": cardType, "Loại xe": vehicle, "Thời gian vào": timeIN, "Status": status}
    in_collection.insert_one(dbIn)

def checkDate(strDateRegis, strDateExpired, timeIN):
    objDateRegis = datetime.strptime(strDateRegis, "%d %m %Y")
    objDateExpired = datetime.strptime(strDateExpired, "%d %m %Y")
    if timeIN >= objDateRegis and timeIN <= objDateExpired:
        return True
    else:
        return False


class IN(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("in.ui", self)

        self.lprecognizer = LPRecognizer()

        self.btnChooseFile.clicked.connect(self.vehicleIN)

    def vehicleIN(self):
        #read image 
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image File", r"/mnt/c/Users/tuyen/Desktop/Project/Do_an/LPR_App/image_test", "Image files (*.jpg *.jpeg *.png)")

        #licence plate recognizer
        if fileName:
            image = cv2.imread(fileName)
            list_txt, scores, plate = self.lprecognizer.infer(image)
            if scores:
                text = list_txt[scores.index(max(scores))]
            else:
                text = ''

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
                # self.lblPlateCar.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
                self.lblPlateCar.setPixmap(QPixmap(_filePath))
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
