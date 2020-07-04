# Azure Optical Character Recognition (OCR)

BBOXHelper supports Azure Cognitive Services Computer Vision OCR & Read API responses for text detection.

BBOXResponse class follows closely the Read API response data model.

>The Read API detects text content in an image using our latest recognition models and converts the identified text into a machine-readable character stream. It's optimized for text-heavy images (such as documents that have been digitally scanned) and for images with a lot of visual noise. It will determine which recognition model to use for each line of text, supporting images with both printed and handwritten text. The Read API executes asynchronously because larger documents can take several minutes to return a result.

>The Read operation maintains the original line groupings of recognized words in its output. Each line comes with bounding box coordinates, and each word within the line also has its own coordinates. If a word was recognized with low confidence, that information is conveyed as well. 

About the OCR API 
>The OCR API uses an older recognition model, supports only images, and executes synchronously, returning immediately with the detected text. It supports more languages than Read API.

Make sure you understand the requirements/limitations of both APIs for your project. 
## Azure Computer Vision Cognitive Services Computer Vision Documentation
1. [Computer Vision Read API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api)
2. [Computer Vision Read API Image Requirements](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#input-requirements)
2. [Computer Vision OCR API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#ocr-api)
3. [Text Recognition Language Support](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/language-support#text-recognition)
3. [Computer Vision API Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision)
4. [Azure SDK for Python](https://azure.github.io/azure-sdk-for-python/)

## Azure Computer Vision Python Examples
You can refer to this [examples](https://github.com/Azure-Samples/cognitive-services-python-sdk-samples/tree/master/samples/vision) to learn about the Python sdk.

**Note**: some examples are not current. Check the [Azure computer Vision Python SDK](https://pypi.org/project/azure-cognitiveservices-vision-computervision/0.6.0/)

## Azure BBoxHelper Integration
Import the below ocrlayout classes
```python
from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper
```
>Example of using the Azure CV python sdk and READ API. 
```python
azure_client = ComputerVisionClient(
    endpoint="https://" + COMPUTERVISION_LOCATION + ".api.cognitive.microsoft.com/",
    credentials=CognitiveServicesCredentials(SUBSCRIPTION_KEY_ENV_NAME)
)
...
with open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_stream:
    job = azure_client.read_in_stream(
        image=image_stream,
        raw=True
    )
operation_id = job.headers['Operation-Location'].split('/')[-1]

image_analysis = azure_client.get_read_result(operation_id,raw=True)
while str.lower(image_analysis.output.status) in ['notstarted', 'running']:
    time.sleep(1)
    image_analysis = azure_client.get_read_result(operation_id=operation_id,raw=True)
print("\tJob completion is: {}".format(image_analysis.output.status))    
```
Capture the READ API response object as string.
```python
ocrresponse=image_analysis.response.content.decode("utf-8")
```
Pass it to the BBoxHelper processing method **processAzureOCRResponse()**
```python
# Create BBOX OCR Response from Azure CV string response
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse)
```
Print the resulting text
```python
print(bboxresponse.text)
```

### Behind the scene...
Our BBoxHelper is fully compatible with Azure response model with pages/lines thus the parsing is pretty straighforward. 
The method **processAzureOCRResponse()** supports passing a string, JSON object or an existing BBOXOCRResponse.
####Snippet of the **bboxhelper.py** to process an Azure OCR response
```python
class BBOXPageLayout():
    #...
    @classmethod
    def from_azure(cls, data):
        lines=[BBOXNormalizedLine.from_azure(i,line) for i,line in enumerate(data["lines"])] 
        return cls(Id=data["page"],ClockwiseOrientation=data["clockwiseOrientation"],Width=data["width"],Height=data["height"],Unit=data["unit"],Lines=lines)

class BBOXOCRResponse():
    #...
    @classmethod
    def from_azure(cls, data):
        pages = list(map(BBOXPageLayout.from_azure, data["recognitionResults"]))
        return cls(status=data["status"],recognitionResults=pages)

class BBoxHelper():

    def processAzureOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None):
        """ processAzureOCRResponse method
            Process an OCR Response input from Azure and returns a new BBox format OCR response.
        """
        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_azure(json.loads(input))
        if isinstance(input,dict):
            response=BBOXOCRResponse.from_azure(input)
        elif isinstance(input,BBOXOCRResponse):
            response=input

        return self.__processOCRResponse(response,sortingAlgo,boxSeparator)        
```

### Reading the response from a file 
```python
# Use local OCR cached response when available
with open(os.path.join(RESULTS_FOLDER, imgname+".azure.read.json"), 'r') as cachefile:
    ocrresponse = cachefile.read().replace('\n', '')
# Create BBOX OCR Response from Azure CV string response
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse)
print(bboxresponse.text)
```