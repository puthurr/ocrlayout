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
bboxresponse=BBoxHelper().processGoogleOCRResponse(response.full_text_annotation)
```
### Behind the scene...
To avoid adding OCR engines direct dependencies in the code, for Google OCR, we only support passing the full_text_annotation object in **processGoogleOCRResponse()** whether the object is passed as JSON string, a JSON object (dict).
We do similar iterations to build a line concept from Google annotation object.
**bboxhelper.py**
```python
class BBOXPageLayout():
...
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
                    # Line Break Logic 
                    for symbol in word.symbols:
                        # Line Break Logic based on symbol 
        ...

class BBOXOCRResponse():
...
    @classmethod
    def from_google(cls, data):
        if "fullTextAnnotation" in data:
            pages = list(map(BBOXPageLayout.from_google,data["fullTextAnnotation"]["pages"]))
            return cls(status="success",original_text=data["fullTextAnnotation"]["text"],recognitionResults=pages)
...

class BBoxHelper():
...
    def processGoogleOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,verbose=None):
        """ processGoogleOCRResponse method
            Process an OCR Response input from Google and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)
            
        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_google(json.loads(input))
        if isinstance(input,dict):
            response=BBOXOCRResponse.from_google(input)
        elif isinstance(input,BBOXOCRResponse):
            response=input

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator)
...
```
### Reading the Google JSON response from a file and process it 
Our Google sample script shows how to read JSON string from a file and rebuild the Google response object 
```python
# Use local OCR cached response when available
with open(os.path.join(self.RESULTS_FOLDER, imgname+".google.vision.json"), 'r') as cachefile:
    json_string = cachefile.read().replace('\n', '')

# Create BBOX OCR Response from Google's JSON output
bboxresponse=self.bboxhelper.processGoogleOCRResponse(json_string,verbose=verbose)
```
