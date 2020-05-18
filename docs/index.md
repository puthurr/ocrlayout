# OcrLayout Project

Provides the ability to get more meaninful text out of common OCR outputs. It manipulates the Bounding Boxes of lines or words. 

## Bounding Box Helper 

While OCR processing images containing lots of textual information, it becomes relevant to assemble the generated text into meaninful lines of text combining  paragraphs or sentences.

Another way to see would be to cluster the lines of text based on their positions/corrdinates in the original content. 

### More meanifull output for what? 

With a closer-human-readable text...
- Text Analytics you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
- Accessibility : Any infographic becomes alive, overcoming the alt text feature.
- Modern browser Read Aloud feature : it becomes easier to build solutions to read aloud an image, increasing verbal narrative of visual information. 
- Machine Translation : get more accurate MT output as you can retain context. 
- Sentences/Paragraph Classification : from scanned-base images i.e. contracts, having a more meaninful textual output allows you to classify it at a granular level in terms of risk, personal clause or conditions. 

BBoxHelper has support for Azure/Google Computer Vision API.

Our goal here is not to conduct a comparison between Azure & Google Computer Vision API but to provide a consistent way to output OCR text for further processing  

### OCR Support

Today bboxhelper supports the original output of 

* [Azure Batch Read API response](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api)

* [Google Vision API Detect Text](https://cloud.google.com/vision/docs/ocr#vision_text_detection-python)


## Examples

Check out our **Examples** section to get a better feeling on how Bounding Box Helper could support better your OCR-related projects. 

