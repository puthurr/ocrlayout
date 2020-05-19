# Azure OCR

BBOHelper supports natively Azure Cognitive Services Computer Vision OCR Read API

By native support, I mean our data model follow closely the OCR data model. 

>The Read API detects text content in an image using our latest recognition models and converts the identified text into a machine-readable character stream. It's optimized for text-heavy images (such as documents that have been digitally scanned) and for images with a lot of visual noise. It will determine which recognition model to use for each line of text, supporting images with both printed and handwritten text. The Read API executes asynchronously because larger documents can take several minutes to return a result.

>The Read operation maintains the original line groupings of recognized words in its output. Each line comes with bounding box coordinates, and each word within the line also has its own coordinates. If a word was recognized with low confidence, that information is conveyed as well. 

## Azure Computer Vision Cognitive Services Computer Vision Documentation
1. [Computer Vision API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api)
2. [Image Requirements](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#image-requirements)
3. [Computer Vision API Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/76a0d91c32a79561a7d5666e421908e7c4cffc6a/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision)
4. [Azure SDK for Python](https://azure.github.io/azure-sdk-for-python/)

## Azure Python Example
You can refer to this [example](https://github.com/Azure-Samples/cognitive-services-python-sdk-samples/blob/master/samples/vision/computer_vision_samples.py)

## BBoxHelper Azure CV Integration 
### In our sample script 
We follow the above example. We capture the response object as string.
```python
ocrresponse=image_analysis.response.content.decode("utf-8")
```
We then pass it to the BBoxHelper processing method **processAzureOCRResponse()**
```python
# Create BBOX OCR Response from Azure CV string response
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse,boxSeparator=["","\r\n"])
```
### Behind the scene...
Our BBoxHelper is fully compatible with Azure response model with pages/lines thus the parsing is pretty straighforward. 
The method **processAzureOCRResponse()** supports passing a string, JSON object or an existing BBOXOCRResponse. 
**bboxhelper.py**
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

### If you are dealing with a Azure CV JSON response string 

Our Azure sample script shows how to read JSON string from a file. 
```python
# Use local OCR cached response when available
with open(os.path.join(RESULTS_FOLDER, imgname+".azure.batch_read.json"), 'r') as cachefile:
    ocrresponse = cachefile.read().replace('\n', '')
```
then call the processAzureOCRResponse() as usual. 
