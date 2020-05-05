import io
import os
import os.path
import json
from PIL import Image,ImageDraw
from enum import Enum

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types

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

def draw_boxes(image, bounds, color, padding=0):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x+padding, bound.vertices[0].y+padding,
            bound.vertices[1].x+padding, bound.vertices[1].y+padding,
            bound.vertices[2].x+padding, bound.vertices[2].y+padding,
            bound.vertices[3].x+padding, bound.vertices[3].y+padding], None, color)
    return image


def google_document_text_detection():
    """Google document text detection. 
    This will recognize text of the given image using the Google Vision API.
    """
    import time

    for filename in os.listdir(IMAGES_FOLDER):
        print("Image Name {}".format(filename))

        # Instantiates a Google Vision client
        client = vision.ImageAnnotatorClient()

        with io.open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_file:
            content = image_file.read()

        image = types.Image(content=content)

        response = client.document_text_detection(image=image)
        document = response.full_text_annotation

        # print("\tRecognized {} page(s)".format(len(image_analysis.output.recognition_results)))

        # with open(os.path.join(RESULTS_FOLDER, filename+".azcv.batch_read.json"), 'w') as outfile:
        #     outfile.write(image_analysis.response.content.decode("utf-8"))

        with open(os.path.join(RESULTS_FOLDER, filename+".gocv.vision.text.json"), 'w') as outfile:
            outfile.write(document.text)

        # Create BBOX OCR Response from Google's response object
        ocrresponse=BBOXOCRResponse.from_google(document)
        bboxresponse=BBoxHelper().processOCRResponse(ocrresponse,YXSortedOutput=False)

        with open(os.path.join(RESULTS_FOLDER, filename+".gocv.bbox.json"), 'w') as outfile:
            outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
        with open(os.path.join(RESULTS_FOLDER, filename+".gocv.bbox.text.json"), 'w') as outfile:
            outfile.write(bboxresponse.Text)

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

        # draw_boxes(image, bounds[FeatureType.SYMBOL.value], 'black')
        draw_boxes(image, bounds[FeatureType.WORD.value], 'yellow')
        draw_boxes(image, bounds[FeatureType.PARA.value], 'red',padding=1)
        draw_boxes(image, bounds[FeatureType.BLOCK.value], 'blue',padding=2)
        
        image.save(os.path.join(RESULTS_FOLDER, "google."+filename))


if __name__ == "__main__":
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    google_document_text_detection()
