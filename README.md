# OcrLayout Project

Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of blocks, paragraphs, lines or words eventually merging them when relevant. 

## BBoxHelper concept

While OCR processing images containing lots of textual information, it might be relevant to assemble the generated text into meaninful sentences or paragraphs.

### Why more meanifull text matters? 

With a closer-human-readable text, you may 
- leverage any Text Analytics for Key Phrases, Entities Extraction with more confidence of its outcome.
- Any infographic becomes alive, overcoming the alt text feature for better Accessibility. 
- engage for Translation 
- convert Text to Speech : create audio files of specific blocks of text or the full scanned image. 
- enable the Browser read-aloud feature for your end-users

### Ocr Output Support

Today bboxhelper supports the original output of 

* Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api

* Google Vision API Detect Text
https://cloud.google.com/vision/docs
https://cloud.google.com/vision/docs/ocr#vision_text_detection-python

## BBoxHelper - Get Started

More information to get started can be found documentation of this repository: [documentation](https://puthurr.github.io/getting-started/).

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


### Known Limitations 

More information on known [limitations](https://puthurr.github.io/known-limitations/).


## Upcoming improvements

* Output in hOCR https://en.wikipedia.org/wiki/HOCR


## Contributing

This project welcomes contributions and suggestions.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**
