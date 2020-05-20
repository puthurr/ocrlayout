# Google OCR 

We support Google Cloud Text Detection object aka DOCUMENT_TEXT_DETECTION. 

>DOCUMENT_TEXT_DETECTION also extracts text from an image, but the response is optimized for dense text and documents. The JSON includes pages,blocks,paragraphs,words, symbols and break information, including confidence scores and bounding boxes. 
 
## Google Documentation
1. [Google Vision API](https://cloud.google.com/vision/docs)
2. [Simple Text Detection](https://cloud.google.com/vision/docs/ocr#vision_text_detection-python)
3. [Document Text Detection - handwriting](https://cloud.google.com/vision/docs/handwriting)
4. [Document Text Detection - pdf/tiff](https://cloud.google.com/vision/docs/pdf)

## Google Python Example
The below example is provide by Google where you see the actual data model of its response
```python
def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock confidence: {}\n'.format(block.confidence))

            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(
                    paragraph.confidence))

                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    print('Word text: {} (confidence: {})'.format(
                        word_text, word.confidence))

                    for symbol in word.symbols:
                        print('\tSymbol: {} (confidence: {})'.format(
                            symbol.text, symbol.confidence))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
```

## BBoxHelper Google Integration 
### In our sample script 
We follow the above example. We capture the response object. 
```python
response = client.document_text_detection(image=image)
```
We then pass the full_text_annotation **object** to the BBoxHelper processing method **processGoogleOCRResponse()**
```python
# Create BBOX OCR Response from Google's response object
bboxresponse=BBoxHelper().processGoogleOCRResponse(response.full_text_annotation,boxSeparator=["","\r\n"])
```
### Behind the scene...
To avoid adding OCR engines direct dependencies in the code, for Google OCR, we only support passing the full_text_annotation object in **processGoogleOCRResponse()**

We do similar iterations to build a line concept from Google annotation object.
**bboxhelper.py**
```python
class BBOXPageLayout():
    #...
    @classmethod
    def from_google(cls, page):
        lines=[]
        line_counter=0
        line_text =""
        line_boxes=[]
        # Create the concept of lines for Google ocr response. 
        for idb, block in enumerate(page.blocks):
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    # Test if the enxt word is within range of the previous one. 
                    # Google OCR doesn't split nicely text set in columns.
                    if len(line_boxes)>0:
                        xdiff=(word.bounding_box.vertices[0].x - line_boxes[-1][1].x)
                        if xdiff > bboxconfig.config["pixel"].GoogleLineBreakThresholdInPixel:
                            bboxlogger.debug("Google|Line Break {0}| {1} {2}".format(str(xdiff),str(line_counter),line_text))
                            # Line break
                            line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes)
                            lines.append(line)
                            line_text=""
                            line_counter+=1
                            line_boxes.clear()

                    line_boxes.append(word.bounding_box.vertices)
                    for symbol in word.symbols:
                        line_text+=symbol.text
                        if symbol.property.detected_break:
                            if symbol.property.detected_break.type in [1,2]:
                                line_text+=" "
                            elif symbol.property.detected_break.type in [3,5]:
                                bboxlogger.debug("Google|Detected Break {0}| {1} {2}".format(str(symbol.property.detected_break.type),str(line_counter),line_text))
                                # Line Break
                                line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes)
                                lines.append(line)
                                line_text=""
                                line_counter+=1
                                line_boxes.clear()

        return cls(Id=1,Width=page.width,Height=page.height,Lines=lines)

class BBOXOCRResponse():
    #...
    @classmethod
    def from_google(cls, document):
        pages = list(map(BBOXPageLayout.from_google,document.pages))
        return cls(status="success",original_text=document.text,recognitionResults=pages)

class BBoxHelper():
    def processGoogleOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None):
        """ processGoogleOCRResponse method
            Process an OCR Response input from Google and returns a new BBox format OCR response.
        """
        #Create an BBOXOCRResponse object from Google input
        response=BBOXOCRResponse.from_google(input)

        return self.__processOCRResponse(response,sortingAlgo,boxSeparator)

```

### If you are dealing with a Google JSON response string 

Our Google sample script shows how to read JSON string from a file and rebuild the Google response object 
```python
# Use local OCR cached response when available
with open(os.path.join(RESULTS_FOLDER, imgname+".google.vision.json"), 'r') as cachefile:
    json_string = cachefile.read().replace('\n', '')
response = json_format.Parse(json_string, vision.types.AnnotateImageResponse())
```
then call the processGoogleOCRResponse() as usual. 