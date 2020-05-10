# OcrLayout Project

Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of lines or words. 

## bboxhelper 

While OCR processing images containing lots of textual information, it might be relevant to assemble the generated text into meaninful sentences or paragraphs.

### More meanifull output for what? 

With a closer-human-readable text, you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
Browser read-aloud. Any infographic becomes alive, overcoming the alt text feature for Accessibility.
Translation 

### Ocr Output Support

Today bboxhelper only supports Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api

Google Vision API support is coming...

### Azure Computer Vision SDK for Python 

https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision

### Google Vision

https://cloud.google.com/vision/docs/ocr

https://cloud.google.com/vision/docs

https://cloud.google.com/vision/docs/drag-and-drop


https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/document_text/doctext.py

https://github.com/GoogleCloudPlatform/python-docs-samples/blob/e126767a678ea132b2eb18e0ee9062f10c4d7be5/vision/cloud-client/crop_hints/crop_hints.py

### Annotated Images

'''
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
'''

### hOCR 

https://en.wikipedia.org/wiki/HOCR

https://github.com/tmbdev/hocr-tools

### Limitations 

The bboxhelper doesn't output Words levels as its goal is to build sentences and paragraphs. 

## Upcoming improvements 

* Scale the testing data 
* Support for paragraph/lines markup like '''<p>...</p>''' (configurable)
* Support for Google Vision API output 
* Output in hOCR https://en.wikipedia.org/wiki/HOCR . Only outputing the lines level

