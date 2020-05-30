import io
import os
import os.path
import json
from PIL import Image,ImageDraw, ImageFont
from enum import Enum
import logging
from pathlib import Path

try:
    from inspect import getfullargspec as get_arg_spec
except ImportError:
    from inspect import getargspec as get_arg_spec
import os
import sys
import types

# Azure CV Support
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
# Google CV Support - Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types as google_types
from google.protobuf import json_format

# OCRLAYOUT Import
try:
    from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper
    print("PyPI Package imported")
except ImportError:
    print("Local Package imported")
    from ocrlayout_pkg.ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper

IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")

#
# Google Specific
#
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
        for bound in page.lines:
            draw.polygon([
                bound.boundingbox[0].X+padding, bound.boundingbox[0].Y+padding,
                bound.boundingbox[1].X+padding, bound.boundingbox[1].Y+padding,
                bound.boundingbox[2].X+padding, bound.boundingbox[2].Y+padding,
                bound.boundingbox[3].X+padding, bound.boundingbox[3].Y+padding], 
                outline=color)
            if bound.rank>0.0:
                font = ImageFont.load_default()
                draw.text((bound.xmedian, bound.ymedian),str(round(bound.rank,4)),fill ="red",font=font)
    return image

def iterate_all_images(ocrengines=[],filter=None,callOCR=True,verbose=False):
    """OCR Text detection for all images 
    Iterate through all images located in the IMAGES_FOLDER and call all OCR Engines
    """
    for filename in os.listdir(IMAGES_FOLDER):
        if filter:
            if filter not in filename:
                continue
        if '.DS_Store' in filename:
            continue
        for engine in ocrengines:
            engine(os.path.join(IMAGES_FOLDER, filename),callOCR,verbose)

def google_document_text_detection_image(filename=None,callOCR=True,verbose=False):
    """Google document text detection. 
    This will recognize text of the given image using the Google Vision API.
    """
    print("GOOGLE - Image Name {}".format(filename))
    p = Path(filename)
    (imgname,imgext) = os.path.splitext(p.name)

    # Check if we have a cached ocr response already for this provider
    invokeOCR=callOCR
    if not callOCR:
        if not os.path.exists(os.path.join(RESULTS_FOLDER, imgname+".google.vision.json")):
            invokeOCR=True

    if invokeOCR:

        # Instantiates a Google Vision client
        google_client = vision.ImageAnnotatorClient()

        with io.open(filename, "rb") as image_file:
            content = image_file.read()

        image = google_types.Image(content=content)

        response = google_client.document_text_detection(image=image)

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
    bboxresponse=BBoxHelper(verbose=verbose).processGoogleOCRResponse(response.full_text_annotation)
    print("BBOX Helper Response {}".format(bboxresponse.__dict__))

    converted=BBOXOCRResponse.from_google(response.full_text_annotation)
    with open(os.path.join(RESULTS_FOLDER, imgname+".google.converted.json"), 'w') as outfile:
        outfile.write(json.dumps(converted.__dict__, default = lambda o: o.__dict__, indent=4))

    with open(os.path.join(RESULTS_FOLDER, imgname+".google.bbox.json"), 'w') as outfile:
        outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
    with open(os.path.join(RESULTS_FOLDER, imgname+".google.bbox.txt"), 'w') as outfile:
        outfile.write(bboxresponse.text)

    document = response.full_text_annotation

    try:
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
        draw_gboxes(image, bounds[FeatureType.WORD.value], 'yellow')
        draw_gboxes(image, bounds[FeatureType.PARA.value], 'red',padding=1)
        draw_gboxes(image, bounds[FeatureType.BLOCK.value], 'blue',padding=2)       
        image.save(os.path.join(RESULTS_FOLDER, imgname+".google"+imgext))
        
        # Write the BBOX resulted image 
        draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
        save_boxed_image(bboximg,os.path.join(RESULTS_FOLDER, imgname+".google.bbox"+imgext))
    except:
        pass

def azure_read_in_stream(filename=None,callOCR=True,verbose=False):
    """RecognizeTextUsingBatchReadAPI.
    This will recognize text of the given image using the Batch Read API.
    """
    import time
    #
    # Azure Specific
    #
    SUBSCRIPTION_KEY_ENV_NAME = os.environ.get("COMPUTERVISION_SUBSCRIPTION_KEY", None)
    COMPUTERVISION_LOCATION = os.environ.get("COMPUTERVISION_LOCATION", "westeurope")

    azure_client = ComputerVisionClient(
        endpoint="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/",
        credentials=CognitiveServicesCredentials(SUBSCRIPTION_KEY_ENV_NAME)
    )
    print("AZURE Image Name {}".format(filename))
    p = Path(filename)
    (imgname,imgext) = os.path.splitext(p.name)

    # Check if we have a cached ocr response already for this provider
    invokeOCR=callOCR
    if not callOCR:
        if not os.path.exists(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json")):
            invokeOCR=True

    if invokeOCR:
        # Azure Computer Vision Call
        with open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_stream:
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

        with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json"), 'w') as outfile:
            outfile.write(image_analysis.response.content.decode("utf-8"))

        with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.txt"), 'w') as outfile:
            for rec in image_analysis.output.analyze_result.read_results:
                for line in rec.lines:
                    outfile.write(line.text)
                    outfile.write('\n')
        ocrresponse=image_analysis.response.content.decode("utf-8")
    else:
        # Use local OCR cached response when available
        with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json"), 'r') as cachefile:
            ocrresponse = cachefile.read().replace('\n', '')

    # Create BBOX OCR Response from Azure CV string response
    bboxresponse=BBoxHelper(verbose=verbose).processAzureOCRResponse(ocrresponse)
    print("BBOX Helper Response {}".format(bboxresponse.__dict__))

    # Write the improved ocr response
    with open(os.path.join(RESULTS_FOLDER, imgname+".azure.bbox.json"), 'w') as outfile:
        outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
    # Write the improved ocr text
    with open(os.path.join(RESULTS_FOLDER, imgname+".azure.bbox.txt"), 'w') as outfile:
        outfile.write(bboxresponse.text)

    try:
        # Create the Before and After images
        imagefn=os.path.join(IMAGES_FOLDER, filename)
        image = Image.open(imagefn)
        bboximg = image.copy()
        # Write the Azure OCR resulted boxes image
        orig_ocrresponse=BBOXOCRResponse.from_azure(json.loads(ocrresponse))
        draw_bboxes(image, orig_ocrresponse, 'red')
        save_boxed_image(image,os.path.join(RESULTS_FOLDER, imgname+".azure"+imgext))
        # Write the BBOX resulted boxes image
        draw_bboxes(bboximg, bboxresponse, 'black',padding=1)
        save_boxed_image(bboximg,os.path.join(RESULTS_FOLDER, imgname+".azure.bbox"+imgext))
    except:
        pass

if __name__ == "__main__":
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    import os
    import argparse
    parser = argparse.ArgumentParser(description='Call OCR outputs for a given image or images dir')
    parser.add_argument('--image',type=str,required=False,help='Process a single image',default=None)
    parser.add_argument('--imagesdir',type=str,required=False,help='Process all images contained in the given directory',default=IMAGES_FOLDER)
    parser.add_argument('--filter',type=str,required=False,help='Filter the images to process based on their filename',default="")
    parser.add_argument('--outputdir',type=str,required=False,help='Define where all outputs will be stored',default=RESULTS_FOLDER)
    parser.add_argument('--callocr', dest='callocr', action='store_true',help='flag to invoke online OCR Service')
    parser.set_defaults(callocr=False)
    parser.add_argument('-v','--verbose', dest='verbose', action='store_true',help='DEBUG logging level')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()

    # Output dir
    if args.outputdir:
        RESULTS_FOLDER=args.outputdir

    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    # Check for available OCR engine functions
    ocrengines=[]
    for func in list(globals().values()):
        if not isinstance(func, types.FunctionType):
            continue
        arguments = get_arg_spec(func).args
        if 'filename' in arguments:
            ocrengines.append(func)

    if len(ocrengines)==0:
        print("No OCR Engine found. exiting.")
        exit

    # Process a single image
    if args.image:
        if not os.path.exists(args.image):
            print("Image path doesn't exist.")
            exit
        else:
            for engine in ocrengines:
                engine(filename=args.image,callOCR=args.callocr,verbose=args.verbose)
    else:
        if args.imagesdir:
            if not os.path.exists(args.imagesdir):
                print("Images folder doesn't exist.")
                exit
            else: 
                IMAGES_FOLDER=args.imagesdir
        # Process all images contained the IMAGES_FOLDER
        # iterate_all_images(ocrengines=ocrengines,filter=args.filter,callOCR=args.callocr,verbose=args.verbose)
        iterate_all_images(ocrengines=ocrengines,filter=args.filter,callOCR=args.callocr,verbose=args.verbose)
