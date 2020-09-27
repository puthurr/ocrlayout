# OCRLAYOUT Library
Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of lines to rebuild a page layout to approximate human-reading experience.  
## Problem Statement
Current OCR engines responses are focus on text recall. Ocrlayout tries to go a step further by re-ordering the lines of text so it'd approach a human-reading behavior. 

When images contains a lot of textual information, it becomes relevant to assemble the generated meaninful blocks of text enabling better scenarios. 

Another way to see would be to cluster the lines of text based on their positions/coordinates in the original content. 
## More meaningfull output for what? 
- **Text Analytics** you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
- **Accessibility** : Any infographic becomes alive, overcoming the alt text feature.
- **Read Aloud feature** : it becomes easier to build solutions to read aloud an image, increasing verbal narrative of visual information. 
- **Machine Translation** : get more accurate MT output as you can retain more context. 
- **Sentences/Paragraph Classification**: from scanned-base images i.e. contracts, having a more meaninful textual output allows you to classify it at a granular level in terms of risk, personal clause or conditions. 
## OCR Engines Output Support
Today bboxhelper supports the output of 
### AZURE
* Azure Batch Read API response. 
https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api
* Azure Computer Vision SDK Python Sample
https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision
### GOOGLE 
* Google Vision API Detect Text
https://cloud.google.com/vision/docs/ocr
https://cloud.google.com/vision/docs/ocr#vision_text_detection-python
* Google Vision Python Sample
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/document_text/doctext.py
### AWS - Detect Document Text
* AWS Textract
Detects text in the input document. Amazon Textract can detect lines of text and the words that make up a line of text. The input document must be an image in JPEG or PNG format.
https://aws.amazon.com/textract/features/
https://docs.aws.amazon.com/textract/latest/dg/how-it-works-detecting.html
https://docs.aws.amazon.com/textract/latest/dg/API_DetectDocumentText.html

## BBoxHelper - Get Started
More information to get started can be found documentation of this repository: [documentation](https://puthurr.github.io/getting-started/).

## Known Limitations 
More information on known [limitations](https://puthurr.github.io/known-limitations/).

## Recipes 
If you need more hands-on examples on how to use this library check out our [recipes](https://github.com/puthurr/ocrlayout-recipes)

## Upcoming improvements
* hOCR Suppport https://en.wikipedia.org/wiki/HOCR [tools](https://github.com/tmbdev/hocr-tools)
* Google OCR for documents (PDF)
* AWS OCR for documents (PDF)

# Releases History
## 0.9 (Upcoming)
- Code-base to Python 3.8
- Support for concurrent pages processing. 
- Faster Contours Sorting.
## 0.8 (2020-08-24)
- Support for AWS Detect Document Text 
- Google support refactored for consistency 
- Simplify the bboxtester script
## 0.7 (2020-07-29)
- Configurable merge line character (default is a single space)
## 0.6 (2020-07-09)
- Support for Azure OCR API 
## 0.5 (2020-06-07)
- Fix line/word X alignment
- Improved sorting with with clusters within clusters support
- added words_count to each line
- removed dependency on OpenCV and Pillow
## 0.4.2 (2020-06-06)
- Remove file logging as default
## 0.4.1 (2020-06-01)
- Comment the determine_ppi method as unstable
## 0.4 (2020-05-31)
- Bounding boxes rotation improvements
- Fix issues with inch unit support
## 0.3 (2020-05-23)
- Refactoring variables names 
- Improvement on the end of blocks handling for generating the final text attribute
## 0.2 (2020-05-22 Afternoon)
- Change to fit the new Azure Computer Vision SDK 0.6.0 [breaking changes](https://pypi.org/project/azure-cognitiveservices-vision-computervision/0.6.0/).
## 0.1 (2020-05-22 Morning)
- Initial release 
## Disclaimer
**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**
