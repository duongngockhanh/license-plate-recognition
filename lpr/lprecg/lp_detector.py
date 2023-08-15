import torch
import numpy as np
import onnxruntime
from lpr.lprecg.func import *

class LPDetector(object):
    def __init__(self, model='../lpr/model/detect.onnx') -> None:
        self.providers = ['CPUExecutionProvider']
        self.session = onnxruntime.InferenceSession(model, providers=self.providers)
    
    def __pre_process(self, image):
        im = letterbox(image,640, stride=32, auto=True)[0]
        im = im.transpose((2, 0, 1))[::-1]
        im = np.ascontiguousarray(im)
        im = torch.from_numpy(im)
        im = im.float()
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim

        return im

    def detect(self, image):
        blob = self.__pre_process(image)
        outputs = self.session.run(None, {self.session.get_inputs()[0].name:np.asarray(blob)})
        output_data = torch.tensor(outputs[0])
        y = non_max_suppression(output_data, 0.25, 0.45)[0]
        y[:, :4] = scale_boxes(blob.shape[2:], y[:, :4], image.shape).round()

        return y[:, :5]