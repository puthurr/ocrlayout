# Ocrlayout Library

Provides the ability to get more meaninful output from common OCR responses by manipulating Bounding Boxes.

Current OCR engines responses are focus on text recall. Ocrlayout tries to go a step further by re-ordering the lines of text so it'd approach a human-reading behavior. 

## Problem Statement
When processing images containing lots of textual information, it becomes relevant to assemble the generated text into meaninful blocks of text. 
While OCR engines responses are fine for recall, they aren't necessary generating meaningfull output text for further Text processing. 

## More meaningfull output for what? 
- **Text Analytics** you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
- **Accessibility** : Any infographic becomes alive, overcoming the alt text feature.
- **Read Aloud feature** : it becomes easier to build solutions to read aloud an image, increasing verbal narrative of visual information. 
- **Machine Translation** : get more accurate MT output as you can retain more context. 
- **Sentences/Paragraph Classification**: from scanned-base images i.e. contracts, having a more meaninful textual output allows you to classify it at a granular level in terms of risk, personal clause or conditions. 

## OCR Engines Support
We supports Azure/Google respective Computer Vision API.

>Our goal here is not to conduct a comparison between Azure & Google Computer Vision API but to provide a consistent way to output OCR text for further processing regardless of the underlying OCR Engine. 

* [Azure Computer Vision Read API](https://docs.microsoft.com/en-us/azure/cognitive-services/   computer-vision/concept-recognizing-text#read-api)

* [Azure Computer Vision OCR API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#ocr-api)

* [Google Vision API Detect Text](https://cloud.google.com/vision/docs/ocr#vision_text_detection-python)

### Azure Computer Vision SDK Python Sample
https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision

### Google Vision Python Sample
https://cloud.google.com/vision/docs/ocr
https://cloud.google.com/vision/docs/ocr#vision_text_detection-python
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/document_text/doctext.py

## BBoxHelper - Get Started
More information to get started can be found documentation of this repository: [documentation](https://puthurr.github.io/getting-started/).

## PyPi Install (https://pypi.org/project/ocrlayout/)
```python
pip install ocrlayout
```
### Known Limitations 
More information on known [limitations](https://puthurr.github.io/known-limitations/).

## Upcoming improvements
* hOCR Suppport https://en.wikipedia.org/wiki/HOCR [tools](https://github.com/tmbdev/hocr-tools)
* asyncio support for pages processing

## Contributing
This project welcomes contributions and suggestions.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/). 

## Disclaimer
**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**
