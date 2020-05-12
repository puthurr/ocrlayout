# OcrLayout Project

Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of blocks, paragraphs , lines or words. 

## BBoxHelper concept

While OCR processing images containing lots of textual information, it might be relevant to assemble the generated text into meaninful sentences or paragraphs.

### Why more meanifull text matters? 

With a closer-human-readable text, you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome.
Any infographic becomes alive, overcoming the alt text feature for better Accessibility. 
Translation 
Convert Text to Speech : create audio files of specific blocks of text or the full scanned image. 
Browser read-aloud. 

### Ocr Output Support

Today bboxhelper supports the original output of 

* Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api

* Google Vision API Detect Text
https://cloud.google.com/vision/docs
https://cloud.google.com/vision/docs/ocr#vision_text_detection-python

## BBoxHelper Setup

BBoxHelper has been developed for Python 3.7+. 

Depending on your preferred OCR service Microsoft Azure or Google, 

### Microsoft Azure 
Set the below environment variables in your env. The ComputerVision location refers to the region you have registered your Azure Computer Vision service. You only need th region there. 
```
SUBSCRIPTION_KEY_ENV_NAME = os.environ.get("COMPUTERVISION_SUBSCRIPTION_KEY", None)
COMPUTERVISION_LOCATION = os.environ.get("COMPUTERVISION_LOCATION", "westeurope")
```

### Google 
Set the below environment variables. The ComputerVision location refers to the region you have registered your Azure Computer Vision service. You only need th region there. 

Refere to Google documentation to authenticate the Google Client : https://cloud.google.com/vision/docs/ocr#set-up-your-gcp-project-and-authentication

### Run the Sample script(s) 

Each supported OCR platform has a corresponding testing script 

Under the project python directory, 
- execute the *bboxtester.azure.py* for testing with Microsoft Azure Computer Vision OCR. 
- execute the *bboxtester.google.py* for testing with Google Computer Vision OCR. 

Each sample script will
- process all images located under the images script (one level of the python dir), 
- call the corresponding OCR service, 
- persist the raw ocr response on disk in the tests-results or the directory of your choice
- persist the original image with the bouding boxes of the raw OCR response
- call on the BBOx Helper
- persist the original image with the bouding boxes of the BBoxHelper OCR response

#### Changing the input and output directories
```
IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")
```


### References
#### Azure Computer Vision SDK for Python 
https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision

#### Google Vision

https://cloud.google.com/vision/docs/ocr
https://cloud.google.com/vision/docs/drag-and-drop
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/document_text/doctext.py
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/e126767a678ea132b2eb18e0ee9062f10c4d7be5/vision/cloud-client/crop_hints/crop_hints.py

#### hOCR 

https://en.wikipedia.org/wiki/HOCR
https://github.com/tmbdev/hocr-tools

### Annotated Images

```
def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
    return image
```

### Limitations 

The bboxhelper doesn't output Words levels as its goal is to build sentences and paragraphs. 

## Upcoming improvements

* Output in hOCR https://en.wikipedia.org/wiki/HOCR

