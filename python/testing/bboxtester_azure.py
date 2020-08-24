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

# Azure CV Support
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# OCRLAYOUT Import
try:
    from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint
    print("PyPI Package imported")
except ImportError:
    print("Local Package imported")
    from ocrlayout_pkg.ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint

#
# Azure Specific
#
SUBSCRIPTION_KEY_ENV_NAME = os.environ.get("COMPUTERVISION_SUBSCRIPTION_KEY", None)
COMPUTERVISION_LOCATION = os.environ.get("COMPUTERVISION_LOCATION", "westeurope")

# Import
from .bboxtester_utils import OCREngine, OCRUtils

class AzureEngine(OCREngine):

    def draw_boxes(self, image, polygon, color, padding=0):
        """Draw a border around the image using the hints in the vector list."""
        draw = ImageDraw.Draw(image)

        # Convert the given bounding box to BBOXPoint 
        if isinstance(polygon,str):
            points = BBOXPoint.from_azure_ocr(polygon,1)           
        elif ( len(polygon) > 4 ):
            points = BBOXPoint.from_azure_read_2(polygon,1)
        else:
            points = list(map(BBOXPoint.from_azure, [x for x in polygon]))

        draw.polygon([
            points[0].X+padding, points[0].Y+padding,
            points[1].X+padding, points[1].Y+padding,
            points[2].X+padding, points[2].Y+padding,
            points[3].X+padding, points[3].Y+padding], 
            outline=color)
        return image

class AzureOCREngine(AzureEngine):

    def detect_text(self, filename=None,callOCR=True,verbose=False):
        print("AZURE OCR Image Name {}".format(filename))
        p = Path(filename)
        (imgname,imgext) = os.path.splitext(p.name)

        # Check if we have a cached ocr response already for this provider
        invokeOCR=callOCR
        if not callOCR:
            if not os.path.exists(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.json")):
                invokeOCR=True

        ocrexception=False

        if invokeOCR:
            ocr_url="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/vision/v3.0/ocr"
            # Set Content-Type to octet-stream
            headers = {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY_ENV_NAME, 'Content-Type': 'application/octet-stream'}
            params = {'language': 'unk', 'detectOrientation': 'true'}

            # Azure Computer Vision OCR API Call
            with open(os.path.join(self.IMAGES_FOLDER, filename), "rb") as image_stream:
                response = requests.post(ocr_url, headers=headers, params=params, data = image_stream)
                # response.raise_for_status()
                image_analysis=response.json()

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.json"), 'w') as outfile:
                outfile.write(response.content.decode("utf-8"))

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.txt"), 'w') as outfile:
                if "regions" in image_analysis:
                    # Extract the word bounding boxes and text.
                    line_infos = [region["lines"] for region in image_analysis["regions"]]
                    for line in line_infos:
                        for word_metadata in line:
                            for word_info in word_metadata["words"]:
                                outfile.write(word_info['text'])
                        outfile.write('\n')
                else: 
                    ocrexception = True
            ocrresponse=response.content.decode("utf-8")
        else:
            # Use local OCR cached response when available
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.json"), 'r') as cachefile:
                ocrresponse = cachefile.read().replace('\n', '')

        if not ocrexception:
            # Create BBOX OCR Response from Azure CV string response
            bboxresponse=self.bboxhelper.processAzureOCRResponse(ocrresponse,verbose=verbose)
            print("BBOX Helper Response {}".format(bboxresponse.__dict__))

            # Write the improved ocr response
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.bbox.json"), 'w') as outfile:
                outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
            # Write the improved ocr text
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.bbox.txt"), 'w') as outfile:
                outfile.write(bboxresponse.text)

            try:
                if imgext not in '.pdf':
                    # Create the Before and After images
                    imagefn=os.path.join(self.IMAGES_FOLDER, filename)
                    image = Image.open(imagefn)
                    bboximg = image.copy()

                    # Write the Azure OCR resulted boxes image
                    jsonres = json.loads(ocrresponse)
                    if "recognitionResults" in jsonres:
                        blocks=jsonres["recognitionResults"]
                    elif "analyzeResult" in jsonres:
                        blocks=jsonres["analyzeResult"]["readResults"]
                    elif "regions" in jsonres:
                        blocks=jsonres["regions"]
                    else:
                        blocks={}

                    for block in blocks:
                        for line in block["lines"]:
                            for word in line["words"]:
                                image = self.draw_boxes(image,word["boundingBox"],'yellow')
                            image = self.draw_boxes(image,line["boundingBox"],'red',padding=1)

                    OCRUtils.save_boxed_image(image,os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr"+imgext))

                    # Write the BBOX resulted boxes image
                    OCRUtils.draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
                    OCRUtils.save_boxed_image(bboximg,os.path.join(self.RESULTS_FOLDER, imgname+".azure.ocr.bbox"+imgext))
            except Exception as ex:
                print(ex)
                pass

class AzureReadEngine(AzureEngine):
    
    def detect_text(self, filename=None,callOCR=True,verbose=False):
        """RecognizeTextUsingBatchReadAPI.
        This will recognize text of the given image using the Batch Read API.
        """
        azure_client = ComputerVisionClient(
            endpoint="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/",
            credentials=CognitiveServicesCredentials(SUBSCRIPTION_KEY_ENV_NAME)
        )
        print("AZURE READ Image Name {}".format(filename))
        p = Path(filename)
        (imgname,imgext) = os.path.splitext(p.name)

        # Check if we have a cached ocr response already for this provider
        invokeOCR=callOCR
        if not callOCR:
            if not os.path.exists(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.json")):
                invokeOCR=True

        if invokeOCR:
            # Azure Computer Vision Call
            with open(os.path.join(self.IMAGES_FOLDER, filename), "rb") as image_stream:
                job = azure_client.read_in_stream(
                    image=image_stream,
                    raw=True
                )
            operation_id = job.headers['Operation-Location'].split('/')[-1]

            image_analysis = azure_client.get_read_result(operation_id,raw=True)
            while str.lower(image_analysis.output.status) in ['notstarted', 'running']:
                time.sleep(1)
                image_analysis = azure_client.get_read_result(operation_id=operation_id,raw=True)
            print("\tJob completion is: {}".format(image_analysis.output.status))
            print("\tRecognized {} page(s)".format(len(image_analysis.output.analyze_result.read_results)))

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.json"), 'w') as outfile:
                outfile.write(image_analysis.response.content.decode("utf-8"))

            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.txt"), 'w') as outfile:
                for rec in image_analysis.output.analyze_result.read_results:
                    for line in rec.lines:
                        outfile.write(line.text)
                        outfile.write('\n')

            ocrresponse=image_analysis.response.content.decode("utf-8")
        else:
            # Use local OCR cached response when available
            with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.json"), 'r') as cachefile:
                ocrresponse = cachefile.read().replace('\n', '')

        # Create BBOX OCR Response from Azure CV string response
        bboxresponse=self.bboxhelper.processAzureOCRResponse(ocrresponse,verbose=verbose)
        print("BBOX Helper Response {}".format(bboxresponse.__dict__))

        # Write the improved ocr response
        with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.bbox.json"), 'w') as outfile:
            outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
        # Write the improved ocr text
        with open(os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.bbox.txt"), 'w') as outfile:
            outfile.write(bboxresponse.text)

        try:
            if imgext not in '.pdf':
                # Create the Before and After images
                imagefn=os.path.join(self.IMAGES_FOLDER, filename)
                image = Image.open(imagefn)
                bboximg = image.copy()

                # Write the Azure OCR resulted boxes image
                jsonres = json.loads(ocrresponse)
                if "recognitionResults" in jsonres:
                    blocks=jsonres["recognitionResults"]
                elif "analyzeResult" in jsonres:
                    blocks=jsonres["analyzeResult"]["readResults"]
                elif "regions" in jsonres:
                    blocks=jsonres["regions"]
                else:
                    blocks={}

                for block in blocks:
                    for line in block["lines"]:
                        for word in line["words"]:
                            image = self.draw_boxes(image,word["boundingBox"],'yellow')
                        image = self.draw_boxes(image,line["boundingBox"],'red',padding=1)

                OCRUtils.save_boxed_image(image,os.path.join(self.RESULTS_FOLDER, imgname+".azure.read"+imgext))

                # Write the BBOX resulted boxes image
                OCRUtils.draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
                OCRUtils.save_boxed_image(bboximg,os.path.join(self.RESULTS_FOLDER, imgname+".azure.read.bbox"+imgext))
        except Exception as ex:
            print(ex)
            pass
