import json
import os.path

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw

from bboxhelper import BBoxHelper,BBOXOCRResponse

SUBSCRIPTION_KEY_ENV_NAME = "COMPUTERVISION_SUBSCRIPTION_KEY"
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
    for page in ocrresponse.recognitionResults:
        for bound in page.Lines:
            draw.polygon([
                bound.BoundingBox[0].X+padding, bound.BoundingBox[0].Y+padding,
                bound.BoundingBox[1].X+padding, bound.BoundingBox[1].Y+padding,
                bound.BoundingBox[2].X+padding, bound.BoundingBox[2].Y+padding,
                bound.BoundingBox[3].X+padding, bound.BoundingBox[3].Y+padding], 
                outline=color)
    return image

def batch_read_file_in_stream(subscription_key):
    """RecognizeTextUsingBatchReadAPI.
    This will recognize text of the given image using the Batch Read API.
    """
    import time
    client = ComputerVisionClient(
        endpoint="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/",
        credentials=CognitiveServicesCredentials(subscription_key)
    )
    print("*** batch_read_file_in_stream ****")
    for filename in os.listdir(IMAGES_FOLDER):
        print("Image Name {}".format(filename))
        with open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_stream:
            job = client.batch_read_file_in_stream(
                image=image_stream,
                mode="Printed",
                raw=True
            )
        operation_id = job.headers['Operation-Location'].split('/')[-1]

        image_analysis = client.get_read_operation_result(operation_id,raw=True)
        while image_analysis.output.status in ['NotStarted', 'Running']:
            time.sleep(1)
            image_analysis = client.get_read_operation_result(operation_id=operation_id,raw=True)
        print("\tJob completion is: {}".format(image_analysis.output.status))
        print("\tRecognized {} page(s)".format(len(image_analysis.output.recognition_results)))

        with open(os.path.join(RESULTS_FOLDER, filename+".azcv.batch_read.json"), 'w') as outfile:
            outfile.write(image_analysis.response.content.decode("utf-8"))

        with open(os.path.join(RESULTS_FOLDER, filename+".azcv.batch_read.text.json"), 'w') as outfile:
            for rec in image_analysis.output.recognition_results:
                for line in rec.lines:
                    outfile.write(line.text)
                    outfile.write('\n')

        bboxresponse=BBoxHelper().processOCRResponse(image_analysis.response.content.decode("utf-8"),YXSortedOutput=False)
        print("BBOX Helper Response {}".format(bboxresponse.__dict__))

        # Write the improved ocr response
        with open(os.path.join(RESULTS_FOLDER, filename+".azcv.bbox.json"), 'w') as outfile:
            outfile.write(json.dumps(bboxresponse.__dict__, default = lambda o: o.__dict__, indent=4))
        # Write the improved ocr text
        with open(os.path.join(RESULTS_FOLDER, filename+".azcv.bbox.text.json"), 'w') as outfile:
            outfile.write(bboxresponse.Text)

        # Create the Before and After images
        imagefn=os.path.join(IMAGES_FOLDER, filename)
        image = Image.open(imagefn)
        response=BBOXOCRResponse.from_json(json.loads(image_analysis.response.content.decode("utf-8")))
        draw_boxes(image, response, 'red')
        draw_boxes(image, bboxresponse, 'black',padding=1)
        save_boxed_image(image,os.path.join(RESULTS_FOLDER, "azure."+filename))


if __name__ == "__main__":
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tools import execute_samples
    execute_samples(globals(), SUBSCRIPTION_KEY_ENV_NAME)
