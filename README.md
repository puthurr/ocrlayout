# OcrLayout Project

Provides the ability to get more meaninful text out of OCR outputs. It manipulates the Bounding Boxes of lines or words. 

## boboxhelper 

While OCR processing images containing lots of textual information, it might be relevant to assemble the generated text into meaninful sentences or paragraphs.

### More meanifull output for what? 

With a closer-human-readable text, you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
Browser read-aloud. Any infographic becomes alive, overcoming the alt text feature for Accessibility.
Translation 

### Ocr Output Support

Today bboxhelper only supports Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api

Google Vision API support is coming...

### Limitations 

There is no size limitation 

## Upcoming improvements 

* Scale the testing data 
* Support for paragraph/lines markup like <p>...</p> (configurable)
* Support for Google Vision API output 
* Output in hOCR https://en.wikipedia.org/wiki/HOCR . Only outputing the lines level
