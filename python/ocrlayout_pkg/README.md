# OcrLayout Library

Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of lines to rebuild a page layout to approximate human-reading experience.  

## Problem Statement

While OCR processing images containing lots of textual information, it becomes relevant to assemble the generated text into meaninful lines of text combining related paragraphs or sentences. 

Another way to see would be to cluster the lines of text based on their positions/coordinates in the original content. 

## More meaningfull output for what? 
- Text Analytics you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
- Accessibility : Any infographic becomes alive, overcoming the alt text feature.
- Modern browser Read Aloud feature : it becomes easier to build solutions to read aloud an image, increasing verbal narrative of visual information. 
- Machine Translation : get more accurate MT output as you can retain more context. 
- Sentences/Paragraph Classification : from scanned-base images i.e. contracts, having a more meaninful textual output allows you to classify it at a granular level in terms of risk, personal clause or conditions. 

### Ocr Output Support

Today bboxhelper supports the output of 

* Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api

* Azure Computer Vision SDK Python Sample
https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision

and 

* Google Vision API Detect Text
https://cloud.google.com/vision/docs/ocr
https://cloud.google.com/vision/docs/ocr#vision_text_detection-python

* Google Vision Python Sample
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/document_text/doctext.py

## BBoxHelper - Get Started
More information to get started can be found documentation of this repository: [documentation](https://puthurr.github.io/getting-started/).

### Known Limitations 

More information on known [limitations](https://puthurr.github.io/known-limitations/).

## Upcoming improvements

* hOCR Suppport https://en.wikipedia.org/wiki/HOCR [tools](https://github.com/tmbdev/hocr-tools)
* asyncio support for pages processing 

# Release History
## 0.2 (2020-05-22 Afternoon)
- Change to fit the new Azure Computer Vision SDK 0.6.0 [breaking changes](https://pypi.org/project/azure-cognitiveservices-vision-computervision/0.6.0/).
## 0.1 (2020-05-22 Morning)
- Initial release 

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**
