import io
import json
import logging
import os
import os.path
import sys
import types
import time
import requests

from enum import Enum
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

class OCREngine():
    def __init__(self, name, bboxhelper, inputdir, outputdir):
        self.name=name
        self.bboxhelper=bboxhelper
        self.IMAGES_FOLDER=inputdir
        self.RESULTS_FOLDER=outputdir
    # @abstractmethod
    def draw_boxes(self, image, polygon, color, padding=0):
        pass
    # @abstractmethod
    def detect_text(self, filename=None,callOCR=True,verbose=False):
        pass

class OCRUtils(): 
    @classmethod
    def save_boxed_image(cls,image,fileout):
        if fileout:
            image.save(fileout)
        else:
            image.show()
    # Draw BBOX boxes
    @classmethod
    def draw_bboxes(cls,image, ocrresponse, color, padding=0):
        """Draw a border around the image using the hints in the vector list."""
        draw = ImageDraw.Draw(image)
        for page in ocrresponse.pages:
            for line in page.lines:
                draw.polygon([
                    line.boundingbox[0].X+padding, line.boundingbox[0].Y+padding,
                    line.boundingbox[1].X+padding, line.boundingbox[1].Y+padding,
                    line.boundingbox[2].X+padding, line.boundingbox[2].Y+padding,
                    line.boundingbox[3].X+padding, line.boundingbox[3].Y+padding], 
                    outline=color)
                # if line.rank>0.0:
                #     font = ImageFont.load_default()
                #     draw.text((line.xmedian, line.ymedian),str(round(line.rank,4)),fill ="red",font=font)
                if line.sorting:
                    font = ImageFont.load_default()
                    draw.text((line.xmedian-15, line.ymedian-15),str(line.sorting),fill ="red",font=font)
                if line.id:
                    draw.text((line.xmedian, line.ymedian),str(line.id),fill ="green",font=font)
        return image
    # Draw CV2 Boxes 
    @classmethod
    def draw_cv2_boxes(cls,image,outputdir):
        p = Path(image)
        (imgname,imgext) = os.path.splitext(p.name)

        # Load image, grayscale, Gaussian blur, Otsu's threshold
        image = cv2.imread(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7,7), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Create rectangular structuring element and dilate
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        dilate = cv2.dilate(thresh, kernel, iterations=4)

        # Find contours and draw rectangle
        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 2)

        cv2.imwrite(os.path.join(outputdir,(imgname+'.cv2'+imgext)),image)
