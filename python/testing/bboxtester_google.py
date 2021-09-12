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

# Google CV Support - Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types as google_types
from google.protobuf import json_format

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# OCRLAYOUT Import
try:
    from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint
    print("PyPI Package imported")
except ImportError:
    print("Local Package imported")
    from ocrlayout_pkg.ocrlayout.bboxmodel import BBOXOCRResponse,BBOXPoint
    from ocrlayout_pkg.ocrlayout.bboxhelper import BBoxHelper

#
# Google Specific
#
class FeatureType(Enum):
    PAGE = 0
    BLOCK = 1
    PARA = 2
    WORD = 3
    SYMBOL = 4

# Import
from .bboxtester_utils import OCREngine, OCRUtils

class GoogleOCREngine(OCREngine):
    # Draw Google boxes
    def draw_boxes(self, image, bounds, color, padding=0):
        """Draw a border around the image using the hints in the vector list."""
        draw = ImageDraw.Draw(image)
        for bound in bounds:
            draw.polygon([
                bound.vertices[0].x+padding, bound.vertices[0].y+padding,
                bound.vertices[1].x+padding, bound.vertices[1].y+padding,
                bound.vertices[2].x+padding, bound.vertices[2].y+padding,
                bound.vertices[3].x+padding, bound.vertices[3].y+padding], None, color)
        return image

    def detect_text(self, filename=None,callOCR=True,verbose=False):
        """Google document text detection. 
        This will recognize text of the given image using the Google Vision API.
        """
        print("GOOGLE - Image Name {}".format(filename))
        p = Path(filename)
        (imgname,imgext) = os.path.splitext(p.name)

        # Check if we have a cached ocr response already for this provider
        invokeOCR=callOCR
        if not callOCR:
            if not os.path.exists(os.path.join(self.RESULTS_FOLDER, imgname+".google.vision.json")):
                invokeOCR=True

        if invokeOCR:

            # Instantiates a Google Vision client
            google_client = vision.ImageAnnotatorClient()

            with io.open(filename, "rb") as image_file:
                content = image_file.read()

            image = google_types.Image(content=content)

            response = google_client.document_text_detection(image=image)
            json_string=json_format.MessageToJson(response)

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.vision.json"), 'w') as outfile:
                outfile.write(json_string)

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.vision.txt"), 'w') as outfile:
                outfile.write(response.full_text_annotation.text)
        else:
            # Use local OCR cached response when available
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.vision.json"), 'r') as cachefile:
                json_string = cachefile.read().replace('\n', '')

        # Create BBOX OCR Response from Google's JSON output
        bboxresponse=self.bboxhelper.processGoogleOCRResponse(json_string,verbose=verbose)

        if bboxresponse:
            print("BBOX Helper Response {}".format(bboxresponse.__dict__))

            converted=BBOXOCRResponse.from_google(json.loads(json_string))
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.converted.json"), 'w') as outfile:
                outfile.write(json.dumps(converted.__dict__, default = lambda o: o.__dict__, indent=4))

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.bbox.json"), 'w') as outfile:
                outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.bbox.txt"), 'w') as outfile:
                outfile.write(bboxresponse.text)

            document = response.full_text_annotation

            try:
                if imgext not in '.pdf':
                    bounds=[[],[],[],[],[],[]]
                    for page in document.pages:
                        for block in page.blocks:
                            for paragraph in block.paragraphs:
                                for word in paragraph.words:
                                    for symbol in word.symbols:
                                        bounds[FeatureType.SYMBOL.value].append(symbol.bounding_box)
                                    bounds[FeatureType.WORD.value].append(word.bounding_box)
                                bounds[FeatureType.PARA.value].append(paragraph.bounding_box)
                            bounds[FeatureType.BLOCK.value].append(block.bounding_box)

                    image = Image.open(filename)
                    bboximg = image.copy()

                    # draw_boxes(image, bounds[FeatureType.SYMBOL.value], 'black')
                    self.draw_boxes(image, bounds[FeatureType.WORD.value], 'yellow')
                    self.draw_boxes(image, bounds[FeatureType.PARA.value], 'red',padding=1)
                    self.draw_boxes(image, bounds[FeatureType.BLOCK.value], 'blue',padding=2)       
                    image.save(os.path.join(self.RESULTS_FOLDER, imgname+".google"+imgext))
                    
                    # Write the BBOX resulted image 
                    OCRUtils.draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
                    OCRUtils.save_boxed_image(bboximg,os.path.join(self.RESULTS_FOLDER, imgname+".google.bbox"+imgext))
            except Exception as ex:
                print(ex)
                pass
        else:
            print("BBOX Helper Invalid Response. Input was {}".format(json_string))


