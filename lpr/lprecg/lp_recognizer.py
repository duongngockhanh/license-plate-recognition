from lpr.lprecg import *
import cv2
import numpy as np

class LPRecognizer(object):
    def __init__(self) -> None:
        self.lpDetector = LPDetector()
        self.textRecognizer = TextRecognizer()
    
    def __four_points_transform(self, image):
        H, W, _= image.shape
        rect = np.asarray([[0, 0], [W ,0], [W, H], [0, H]], dtype= "float32")
        width = 195
        height = 50
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]], dtype= "float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warp = cv2.warpPerspective(image, M, (width, height))

        return warp

    def __norm_plate(self, iplate, classID=None):
        if iplate is None:
            return []
        h, w, _ = iplate.shape
        if w / h > 2.5:
        # if classID == 1:
            iplate_transform = self.__four_points_transform(iplate)

            return iplate_transform
        else:
            iplate_1 = iplate[0:int(h / 2), 0:w]
            iplate_2 = iplate[int(h / 2):h, 0:w]
            _iplate_1 = cv2.resize(iplate_1, (165, 50))
            _iplate_2 = cv2.resize(iplate_2, (165, 50))
            iplate_concat = cv2.hconcat([_iplate_1, _iplate_2])
            iplate_blur = cv2.GaussianBlur(iplate_concat, (7, 7), 0)

            return iplate_blur

    def __rule(self, text):
        text_new = ''
        text = ''.join(char for char in text if char.isalnum() or char.isalpha())
        text = text.upper()
        arr = list(text)
        if len(arr) == 9 and arr[3].isalpha() and not arr[2].isalpha():
            arr = arr[1:] 
        if len(arr) > 6:
            if arr[2] in '8':
                arr = arr[:2] + ['B'] + arr[2+1:]
            if arr[0] in 'B':
                arr = ['8'] + arr[1:]
            if arr[1] in 'B':
                arr = arr[:1] + ['8'] + arr[1+1:]
            # 7 Z
            if arr[0] in 'Z':
                arr = ['7'] + arr[1:]
            if arr[1] in 'Z':
                arr = arr[:1] + ['7'] + arr[1+1:]
            # 0 D
            if arr[2] in '0':
                arr = arr[:2] + ['D'] + arr[2+1:]
            # A 4
            if arr[2] in '4':
                arr = arr[:2] + ['A'] + arr[2+1:]
            # 7 V
            if arr[0] in 'V':
                arr = ['7'] + arr[1:]
            if arr[1] in 'V':
                arr = arr[:1] + ['7'] + arr[1+1:]
            # O D
            if arr[3] in 'O':
                arr = arr[:3] + ['D'] + arr[3+1:]
            text_new = ''.join(str(elem) for elem in arr)
        
        return text_new

    def infer(self, image):
        global text_pred
        global text
        list_txt = []
        list_iplates = []
        scores = []
        list_plates = self.lpDetector.detect(image)
        if list_plates is None:
            return None
        for plate in list_plates:
            x0 = int(plate[0])
            y0 = int(plate[1])
            x1 = int(plate[2])
            y1 = int(plate[3])
            lp_score = plate[4]
            if x0 > 5:
                iplate = image[abs(y0):abs(y1+3), abs(x0-5):abs(x1+5)]
            iplate = image[abs(y0):abs(y1), abs(x0):abs(x1)]

            res = []
            text_pred = ''

            if iplate is None:
                continue
            h, w, _ = iplate.shape
            if w / h > 2.5:
                text = self.textRecognizer.recognizer(iplate)
                res.append(text[0][0])
            else:
                iplate_1 = iplate[0:int(h / 2), 0:w]
                iplate_2 = iplate[int(h / 2):h, 0:w]
                text_1 = self.textRecognizer.recognizer(iplate_1)
                text_2 = self.textRecognizer.recognizer(iplate_2)
                text = str(text_1[0][0] + text_2[0][0])
                res.append(text)
            
            # norm_plate = self.__norm_plate(iplate)

            # if norm_plate is None:
            #     continue
            # text = self.textRecognizer.recognizer(norm_plate)
            # res.append(text[0][0])
            _text = list(map(lambda text: str(text), res))
            _text_pred = ''.join(_text)
            text_pred = ''.join(char for char in _text_pred if char.isalnum() or char.isalpha()).upper()
            txt = self.__rule(text_pred)
            list_txt.append(txt)
            scores.append(lp_score)
            list_iplates.append(iplate)

        return list_txt, scores, list_iplates

