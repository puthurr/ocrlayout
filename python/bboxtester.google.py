import io
import os
import os.path
import json
from PIL import Image,ImageDraw, ImageFont
from enum import Enum

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types
from google.protobuf import json_format

from bboxhelper import BBOXOCRResponse,BBoxHelper

IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")

class FeatureType(Enum):
    PAGE = 0
    BLOCK = 1
    PARA = 2
    WORD = 3
    SYMBOL = 4

def save_boxed_image(image,fileout):
    if fileout:
        image.save(fileout)
    else:
        image.show()

def draw_gboxes(image, bounds, color, padding=0):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x+padding, bound.vertices[0].y+padding,
            bound.vertices[1].x+padding, bound.vertices[1].y+padding,
            bound.vertices[2].x+padding, bound.vertices[2].y+padding,
            bound.vertices[3].x+padding, bound.vertices[3].y+padding], None, color)
    return image

def draw_bboxes(image, ocrresponse:BBOXOCRResponse, color, padding=0):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)
    for page in ocrresponse.pages:
        for bound in page.Lines:
            draw.polygon([
                bound.BoundingBox[0].X+padding, bound.BoundingBox[0].Y+padding,
                bound.BoundingBox[1].X+padding, bound.BoundingBox[1].Y+padding,
                bound.BoundingBox[2].X+padding, bound.BoundingBox[2].Y+padding,
                bound.BoundingBox[3].X+padding, bound.BoundingBox[3].Y+padding], 
                outline=color)
            if bound.blockid>0.0:
                font = ImageFont.load_default()
                draw.text((bound.XMedian, bound.YMedian),str(round(bound.blockid,4)),fill ="red",font=font)
    return image


def google_document_text_detection(filter:None,callOCR=True):
    """Google document text detection. 
    This will recognize text of the given image using the Google Vision API.
    """
    import time

    for filename in os.listdir(IMAGES_FOLDER):

        if filter:
            if filter not in filename:
                continue 

        print("Image Name {}".format(filename))
        (imgname,imgext) = os.path.splitext(filename)

        if callOCR:
            # Instantiates a Google Vision client
            client = vision.ImageAnnotatorClient()

            with io.open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_file:
                content = image_file.read()

            image = types.Image(content=content)

            response = client.document_text_detection(image=image)

            with open(os.path.join(RESULTS_FOLDER, imgname+".google.vision.json"), 'w') as outfile:
                outfile.write(json_format.MessageToJson(response))

            with open(os.path.join(RESULTS_FOLDER, imgname+".google.vision.txt"), 'w') as outfile:
                outfile.write(response.full_text_annotation.text)
        else:
            # Use local OCR cached response when available
            with open(os.path.join(RESULTS_FOLDER, imgname+".google.vision.json"), 'r') as cachefile:
                json_string = cachefile.read().replace('\n', '')
            response = json_format.Parse(json_string, vision.types.AnnotateImageResponse())

        # Create BBOX OCR Response from Google's response object
        bboxresponse=BBoxHelper().processGoogleOCRResponse(response.full_text_annotation,boxSeparator=["","\r\n"])

        converted=BBOXOCRResponse.from_google(response.full_text_annotation)
        with open(os.path.join(RESULTS_FOLDER, imgname+".google.converted.json"), 'w') as outfile:
            outfile.write(json.dumps(converted.__dict__, default = lambda o: o.__dict__, indent=4))

        with open(os.path.join(RESULTS_FOLDER, imgname+".google.bbox.json"), 'w') as outfile:
            outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
        with open(os.path.join(RESULTS_FOLDER, imgname+".google.bbox.txt"), 'w') as outfile:
            outfile.write(bboxresponse.Text)

        document = response.full_text_annotation

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

        image = Image.open(os.path.join(IMAGES_FOLDER, filename))
        bboximg = image.copy()

        # draw_boxes(image, bounds[FeatureType.SYMBOL.value], 'black')
        draw_gboxes(image, bounds[FeatureType.WORD.value], 'yellow')
        draw_gboxes(image, bounds[FeatureType.PARA.value], 'red',padding=1)
        draw_gboxes(image, bounds[FeatureType.BLOCK.value], 'blue',padding=2)       
        image.save(os.path.join(RESULTS_FOLDER, imgname+".google"+imgext))
        
        # Write the BBOX resulted image 
        draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
        save_boxed_image(bboximg,os.path.join(RESULTS_FOLDER, imgname+".google.bbox"+imgext))


if __name__ == "__main__":
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    import os
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)
    google_document_text_detection("scan",callOCR=False)
