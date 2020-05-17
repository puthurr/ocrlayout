import json
import os.path
import copy
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw, ImageFont
from bboxutils import BBoxSort
from bboxhelper import BBoxHelper,BBOXOCRResponse
import cv2

SUBSCRIPTION_KEY_ENV_NAME = os.environ.get("COMPUTERVISION_SUBSCRIPTION_KEY", None)
COMPUTERVISION_LOCATION = os.environ.get("COMPUTERVISION_LOCATION", "westeurope")

IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")

def save_boxed_image(image,fileout):
    if fileout:
        image.save(fileout)
    else:
        image.show()

def draw_boxes(image, ocrresponse:BBOXOCRResponse, color, padding=0):
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

def batch_read_file_in_stream(filter=None,callOCR=True):
    """RecognizeTextUsingBatchReadAPI.
    This will recognize text of the given image using the Batch Read API.
    """
    import time
    client = ComputerVisionClient(
        endpoint="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/",
        credentials=CognitiveServicesCredentials(SUBSCRIPTION_KEY_ENV_NAME)
    )
    print("*** batch_read_file_in_stream ****")
    for filename in os.listdir(IMAGES_FOLDER):
        if filter:
            if filter not in filename:
                continue 
        print("Image Name {}".format(filename))
        (imgname,imgext) = os.path.splitext(filename)

        if callOCR:
            # Azure Computer Vision Call
            with open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_stream:
                job = client.batch_read_file_in_stream(
                    image=image_stream,
                    raw=True
                )
            operation_id = job.headers['Operation-Location'].split('/')[-1]

            image_analysis = client.get_read_operation_result(operation_id,raw=True)
            while image_analysis.output.status in ['NotStarted', 'Running']:
                time.sleep(1)
                image_analysis = client.get_read_operation_result(operation_id=operation_id,raw=True)
            print("\tJob completion is: {}".format(image_analysis.output.status))
            print("\tRecognized {} page(s)".format(len(image_analysis.output.recognition_results)))

            with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json"), 'w') as outfile:
                outfile.write(image_analysis.response.content.decode("utf-8"))

            with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.text.json"), 'w') as outfile:
                for rec in image_analysis.output.recognition_results:
                    for line in rec.lines:
                        outfile.write(line.text)
                        outfile.write('\n')

            ocrresponse=image_analysis.response.content.decode("utf-8")
            bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse,boxSeparator=["","\r\n"])
        else: 
            # Use local OCR cached response when available
            with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json"), 'r') as cachefile:
                ocrresponse = cachefile.read().replace('\n', '')
            bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse,boxSeparator=["","\r\n"])

        print("BBOX Helper Response {}".format(bboxresponse.__dict__))

        # Write the improved ocr response
        with open(os.path.join(RESULTS_FOLDER, imgname+".azure.bbox.json"), 'w') as outfile:
            outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
        # Write the improved ocr text
        with open(os.path.join(RESULTS_FOLDER, imgname+".azure.bbox.text.json"), 'w') as outfile:
            outfile.write(bboxresponse.Text)

        # Create the Before and After images
        imagefn=os.path.join(IMAGES_FOLDER, filename)
        image = Image.open(imagefn)
        bboximg = image.copy()

        # Write the Azure OCR resulted boxes image
        orig_ocrresponse=BBOXOCRResponse.from_azure(json.loads(ocrresponse))
        draw_boxes(image, orig_ocrresponse, 'red')
        save_boxed_image(image,os.path.join(RESULTS_FOLDER, imgname+".azure"+imgext))
        # Write the BBOX resulted boxes image
        draw_boxes(bboximg, bboxresponse, 'black',padding=1)
        save_boxed_image(bboximg,os.path.join(RESULTS_FOLDER, imgname+".azure.bbox"+imgext))

if __name__ == "__main__":
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    import os
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)
    # batch_read_file_in_stream("scan",callOCR=False)
    batch_read_file_in_stream("scan6",callOCR=False)
