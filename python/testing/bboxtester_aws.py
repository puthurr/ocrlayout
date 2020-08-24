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

# AWS 
import boto3 

# OCRLAYOUT Import
try:
    from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint
    print("PyPI Package imported")
except ImportError:
    print("Local Package imported")
    from ocrlayout_pkg.ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint

# Import
from .bboxtester_utils import OCREngine, OCRUtils

class AWSOCREngine(OCREngine):

    # Draw AWS boxes
    def draw_boxes(self, image, polygon, color, padding=0):
        """Draw a border around the image using the hints in the vector list."""
        draw = ImageDraw.Draw(image)

        # width, height = image.size
        width, height = 1,1

        draw.polygon([
            polygon[0]["X"]*width+padding, polygon[0]["Y"]*height+padding,
            polygon[1]["X"]*width+padding, polygon[1]["Y"]*height+padding,
            polygon[2]["X"]*width+padding, polygon[2]["Y"]*height+padding,
            polygon[3]["X"]*width+padding, polygon[3]["Y"]*height+padding], None, color)

        return image

    #
    # AMAZON - AWS 
    #
    def detect_text(self, filename=None,callOCR=True,verbose=False):
    # {
    #     "Document": {
    #         "Bytes": "/9j/4AAQSk....."
    #     }
    # }
        print("AWS TextExtract Image Name {}".format(filename))
        p = Path(filename)
        (imgname,imgext) = os.path.splitext(p.name)

        if imgext in ['.pdf','.tif','.tiff']:
            return 

        # Check if we have a cached ocr response already for this provider
        invokeOCR=callOCR
        if not callOCR:
            if not os.path.exists(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.json")):
                invokeOCR=True

        if invokeOCR :
            with open(os.path.join(self.IMAGES_FOLDER, filename), "rb") as image_stream:
                img_test = image_stream.read()
                bytes_test = bytearray(img_test)

            # Amazon Textract client
            textract = boto3.client('textract')

            # Call Amazon Textract
            ocrresponse = textract.detect_document_text(Document={'Bytes': bytes_test })

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.json"), 'w') as outfile:
                outfile.write(json.dumps(ocrresponse))

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.txt"), 'w') as outfile:
                for item in ocrresponse["Blocks"]:
                    if item["BlockType"] == "LINE":
                        outfile.write(item["Text"])
                        outfile.write('\n')
        else:
            # Use local OCR cached response when available
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.json"), 'r') as cachefile:
                ocrresponse = cachefile.read().replace('\n', '')

        try:
            if imgext not in '.pdf':
                # Create the Before and After images
                imagefn=os.path.join(self.IMAGES_FOLDER, filename)
                image = Image.open(imagefn)

                width, height = image.size

                # Create BBOX OCR Response from AWS string response
                bboxresponse=self.bboxhelper.processAWSOCRResponse(ocrresponse,width,height,verbose=verbose)
                if bboxresponse:
                    print("BBOX Helper Response {}".format(bboxresponse.__dict__))

                    # Write the improved ocr response
                    with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.bbox.json"), 'w') as outfile:
                        outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
                    # Write the improved ocr text
                    with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.bbox.txt"), 'w') as outfile:
                        outfile.write(bboxresponse.text)

                    # Create the Before and After images
                    bboximg = image.copy()
                    
                    blocks=ocrresponse["Blocks"]
                    for block in blocks:
                        if block["BlockType"] == "LINE":
                            image = self.draw_boxes(image,block["Geometry"]["Polygon"],'red')
                        if block["BlockType"] == "WORD":
                            image = self.draw_boxes(image,block["Geometry"]["Polygon"],'yellow',padding=1)

                    OCRUtils.save_boxed_image(image,os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract"+imgext))

                    # Write the BBOX resulted boxes image
                    OCRUtils.draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
                    OCRUtils.save_boxed_image(bboximg,os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.bbox"+imgext))
                else:
                    print("BBOX Helper Invalid Response. Input was {}".format(json_string))             

        except Exception as ex:
            print(ex)
            pass

