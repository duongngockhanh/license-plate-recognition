import cv2
import sys
import os
from datetime import datetime, date, time
from PIL import ImageQt, Image
sys.path.append("../")

from lpr.lprecg import LPRecognizer

from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

from pymongo import MongoClient
cluster = "mongodb+srv://tuyennt:0711@lpr.3u3tc8j.mongodb.net/test"
client = MongoClient(cluster)
db = client.lpr
in_collection = db.in_collection
manager_collection = db.manager_collection
out_collection = db.out_collection
price_collection = db.price
card_collection = db.card

priceCar = price_collection.find_one({"Loại phương tiện": "Ô tô", "Trạng thái": "Sử dụng"})
priceMotobike = price_collection.find_one({"Loại phương tiện": "Xe máy", "Trạng thái": "Sử dụng"})

def add2Out(idCard, textLPR, cardType, vehicle, timeIN, timeOUT, price, status):
    dbOut = {"Mã thẻ": idCard, "Biển số": textLPR, "Loại vé": cardType, "Loại xe": vehicle, "Thời gian vào": timeIN, "Thời gian ra": timeOUT, "Giá vé": price, "Status": status}
    out_collection.insert_one(dbOut)

# def calculateDateTime(timeIN, timeOUT):
#     dayIN = date(timeIN.year, timeIN.month, timeIN.day)
#     dayOUT = date(timeOUT.year, timeOUT.month, timeOUT.day)

#     return (dayOUT - dayIN).days

def checkBetweenTime(beginTime, endTime, checkTime):
    if beginTime < endTime:
        return checkTime >= beginTime and checkTime <= endTime
    else:
        return checkTime >= beginTime or checkTime <= endTime

def calculateMoney(price, timeIN, timeOUT):
    if timeOUT.day - timeIN.day > 0:
        priceDay = (int(price["Giá ngày"]) + int(price["Giá đêm"]) + int(price["Giá phụ thu"])) * (timeOUT.day - timeIN.day - 1)

        #calculate extra price
        if int(price["Bắt đầu phụ thu"]) == int(price["Kết thúc phụ thu"]):
            priceExtraIN = 0
            priceExtraOUT = 0
        elif int(price["Bắt đầu phụ thu"]) > int(price["Kết thúc phụ thu"]):
            priceExtraIN = int(price["Giá phụ thu"])
            if checkBetweenTime(time(int(price["Bắt đầu phụ thu"])), time(23), time(timeOUT.hour)):
                priceExtraOUT = int(price["Giá phụ thu"])
            else:
                priceExtraOUT = 0
        else:
            if checkBetweenTime(time(0), time(int(price["Kết thúc phụ thu"])), time(timeIN.hour)):
                priceExtraIN = int(price["Giá phụ thu"])
            else:
                priceExtraIN = 0
            if checkBetweenTime(time(int(price["Bắt đầu phụ thu"])), time(0), time(timeOUT.hour)):
                priceExtraOUT = int(price["Giá phụ thu"])
            else:
                priceExtraOUT = 0

        #calculate price day IN
        if checkBetweenTime(time(int(price["Bắt đầu đêm"])), time(int(price["Kết thúc đêm"])), time(timeIN.hour)):
            if checkBetweenTime(time(int(price["Bắt đầu đêm"])), time(23), time(timeIN.hour)):
                priceDayIN = int(price["Giá đêm"])
            else:
                priceDayIN = int(price["Giá đêm"]) + int(price["Giá ngày"])
        else:
            priceDayIN = int(price["Giá đêm"]) + int(price["Giá ngày"])

        #calculate price day OUT
        if checkBetweenTime(time(int(price["Bắt đầu đêm"])), time(int(price["Kết thúc đêm"])), time(timeOUT.hour)):
            if checkBetweenTime(time(0), time(int(price["Kết thúc đêm"])), time(timeOUT.hour)):
                priceDayOUT = 0
            else:
                priceDayOUT = int(price["Giá đêm"]) + int(price["Giá ngày"])
        else:
            priceDayOUT = int(price["Giá ngày"])
        
        priceSum = priceDay + priceExtraIN + priceExtraOUT + priceDayIN + priceDayOUT
    
    else:
        #calculate extra price
        if int(price["Bắt đầu phụ thu"]) == int(price["Kết thúc phụ thu"]):   
            priceExtraIN = 0
            priceExtraOUT = 0
        elif int(price["Bắt đầu phụ thu"]) > int(price["Kết thúc phụ thu"]):   
            if checkBetweenTime(time(0), time(int(price["Kết thúc phụ thu"])), time(timeIN.hour)):
                priceExtraIN = int(price["Giá phụ thu"])
            else:
                priceExtraIN = 0
            if checkBetweenTime(time(int(price["Bắt đầu phụ thu"])), time(23), time(timeOUT.hour)):
                priceExtraOUT = int(price["Giá phụ thu"])
            else:
                priceExtraOUT = 0
        else:
            if timeOUT.hour < int(price["Bắt đầu phụ thu"]) or timeIN.hour > int(price["Kết thúc phụ thu"]):
                priceExtraIN = 0
                priceExtraOUT = 0
            else:
                priceExtraIN = int(price("Giá phụ thu"))
                priceExtraOUT = 0
        
        #calculate price
        if checkBetweenTime(time(0), time(int(price["Kết thúc đêm"])), time(timeIN.hour)) and checkBetweenTime(time(0), time(int(price["Kết thúc đêm"])), time(timeOUT.hour)):
            priceDay = int(price["Giá đêm"])
        elif checkBetweenTime(time(0), time(int(price["Kết thúc đêm"])), time(timeIN.hour)) and checkBetweenTime(time(int(price["Kết thúc đêm"])), time(int(price["Bắt đầu đêm"])), time(timeOUT.hour)):
            priceDay = int(price["Giá đêm"]) + int(price["Giá ngày"])
        elif checkBetweenTime(time(0), time(int(price["Kết thúc đêm"])), time(timeIN.hour)) and checkBetweenTime(time(int(price["Bắt đầu đêm"])), time(0), time(timeOUT.hour)):
            priceDay = int(price["Giá đêm"]) * 2 + int(price["Giá ngày"])
        elif checkBetweenTime(time(int(price["Kết thúc đêm"])), time(int(price["Bắt đầu đêm"])), time(timeIN.hour)) and checkBetweenTime(time(int(price["Kết thúc đêm"])), time(int(price["Bắt đầu đêm"])), time(timeOUT.hour)):
            priceDay = int(price["Giá ngày"])
        elif checkBetweenTime(time(int(price["Kết thúc đêm"])), time(int(price["Bắt đầu đêm"])), time(timeIN.hour)) and checkBetweenTime(time(int(price["Bắt đầu đêm"])), time(0), time(timeOUT.hour)):
            priceDay = int(price["Giá đêm"]) + int(price["Giá ngày"])
        else:
            priceDay = int(price["Giá đêm"])
        
        priceSum = priceDay + priceExtraIN + priceExtraOUT

    return priceSum


class OUT(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("out.ui", self)

        self.lprecognizer = LPRecognizer()

        self.btnChooseFile.clicked.connect(self.vehicleOUT)
    
    def vehicleOUT(self):
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

            #set lane vehicle
            timeOUT = datetime.now()
            strTimeOUT = timeOUT.strftime('%Hh%Mp')
            strDayOUT = timeOUT.strftime('%d/%m/%Y')

            idCard = os.path.basename(fileName.split(".")[0])
            nameVehicle = os.path.dirname(fileName).split("/")[-1]
            if nameVehicle == "car":
                #car image out
                self.lblImgOutCar.setScaledContents(True)
                self.lblImgOutCar.setPixmap(QPixmap(fileName))
                #plate image out
                self.lblPlateOutCar.setScaledContents(True)
                self.lblPlateOutCar.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
                #information
                self.lblCarDayOut.setText(strDayOUT)
                self.lblCarTimeOut.setText(strTimeOUT)
                self.lblCarPlateOut.setText(text)
            else:
                #motobike image out
                self.lblImgOutMotobike.setScaledContents(True)
                self.lblImgOutMotobike.setPixmap(QPixmap(fileName))
                #plate image out
                self.lblPlateOutMotobike.setScaledContents(True)
                self.lblPlateOutMotobike.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(Image.fromarray(plate, mode="RGB"))))
                #information
                self.lblMotobikeDayOut.setText(strDayOUT)
                self.lblMotobikeTimeOut.setText(strTimeOUT)
                self.lblMotobikePlateOut.setText(text)
            document = in_collection.find_one({"Mã thẻ": idCard})
            if document is None:
                if nameVehicle == "car":
                    # messageCheckCard()
                    self.lblCarDayIn.clear()
                    self.lblCarTimeIn.clear()
                    self.lblCarPlateIn.clear()
                    self.lblCarPrice.clear()
                    self.lblImgInCar.clear()
                    self.lblCarMessage.setText("THẺ KHÔNG HỢP LỆ")
                    self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                else:
                    # messageCheckCard()
                    self.lblMotobikeDayIn.clear()
                    self.lblMotobikeTimeIn.clear()
                    self.lblMotobikePlateIn.clear()
                    self.lblMotobikePrice.clear()
                    self.lblImgInMotobike.clear()
                    self.lblMotobikeMessage.setText("THẺ KHÔNG HỢP LỆ")
                    self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')
            else:
                valuesList = list(document.values())
                timeIN = valuesList[6]
                strDayIN = timeIN.strftime('%d/%m/%Y')
                strTimeIN = timeIN.strftime('%Hh%Mp')
                if nameVehicle == "car":
                    self.lblImgInCar.setScaledContents(True)
                    self.lblImgInCar.setPixmap(QPixmap(valuesList[1]))
                    self.lblCarPlateIn.setText(valuesList[3])
                    self.lblCarPlateOut.setText(text)
                    self.lblCarTimeIn.setText(strTimeIN)
                    self.lblCarDayIn.setText(strDayIN)
                    if valuesList[4] == "Vé tháng":
                        self.lblCarPrice.setText("0 VND")
                        priceSum = 0
                    else:
                        # day = calculateDateTime(timeIN, timeOUT)
                        priceCar = price_collection.find_one({"Loại phương tiện": "Ô tô", "Trạng thái": "Sử dụng"})
                        if priceCar:
                            priceSum = calculateMoney(priceCar, timeIN, timeOUT)
                            self.lblCarPrice.setText(str(priceSum) + " VND")
                        card_collection.find_one_and_update({"Mã thẻ": idCard}, {"$set": {"Biển số": "", "Trạng thái": "Chưa sử dụng"}})
                    # self.lblPlateInCar.setPixmap(QPixmap(valuesList[2].split(".")[0] + "_plate." + valuesList[2].split(".")[1]))
                    if valuesList[3] == text:
                        status = "Out"
                        add2Out(idCard, text, valuesList[4], valuesList[5], timeIN, timeOUT, priceSum, status)
                        in_collection.delete_one({"Biển số": text})
                        self.lblCarMessage.setText("HẸN GẶP LẠI")
                        self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: green}')
                    else:
                        # messageCheckOut()
                        self.lblCarDayIn.clear()
                        self.lblCarTimeIn.clear()
                        self.lblCarPlateIn.clear()
                        self.lblCarPrice.clear()
                        self.lblImgInCar.clear()
                        self.lblCarMessage.setText("BIỂN SỐ KHÔNG HỢP LỆ")
                        self.lblCarMessage.setStyleSheet('QLabel {color: white; background-color: red}')
                else:
                    self.lblImgInMotobike.setScaledContents(True)
                    self.lblImgInMotobike.setPixmap(QPixmap(valuesList[1]))
                    self.lblMotobikePlateIn.setText(valuesList[3])
                    self.lblMotobikePlateOut.setText(text)
                    self.lblMotobikeTimeIn.setText(strTimeIN)
                    self.lblMotobikeDayIn.setText(strDayIN)
                    if valuesList[4] == "Vé tháng":
                        self.lblMotobikePrice.setText("0 VND")
                        priceSum = 0
                    else:
                        # day = calculateDateTime(timeIN, timeOUT)
                        priceMotobike = price_collection.find_one({"Loại phương tiện": "Xe máy", "Trạng thái": "Sử dụng"})
                        if priceMotobike:
                            priceSum = calculateMoney(priceMotobike, timeIN, timeOUT)
                            self.lblMotobikePrice.setText(str(priceSum) + " VND")
                        card_collection.find_one_and_update({"Mã thẻ": idCard}, {"$set": {"Biển số": "", "Trạng thái": "Chưa sử dụng"}})
                    # self.lblPlateInMotobike.setPixmap(QPixmap(valuesList[2].split(".")[0] + "_plate." + valuesList[2].split(".")[1]))
                    if valuesList[3] == text:
                        status = "Out"
                        add2Out(idCard, text, valuesList[4], valuesList[5], timeIN, timeOUT, priceSum, status)
                        in_collection.delete_one({"Biển số": text})
                        self.lblMotobikeMessage.setText("HẸN GẶP LẠI")
                        self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: green}')
                    else:
                        # messageCheckOut()
                        self.lblMotobikeDayIn.clear()
                        self.lblMotobikeTimeIn.clear()
                        self.lblMotobikePlateIn.clear()
                        self.lblMotobikePrice.clear()
                        self.lblImgInMotobike.clear()
                        self.lblMotobikeMessage.setText("BIỂN SỐ KHÔNG HỢP LỆ")
                        self.lblMotobikeMessage.setStyleSheet('QLabel {color: white; background-color: red}')

