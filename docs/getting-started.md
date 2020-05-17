## BBoxHelper - Getting Started

BBoxHelper has been developed for Python 3.7+. Install the requirements as specified in the requirements.txt. 

Depending on your preferred OCR service Microsoft Azure or Google

### Microsoft Azure 
Set the below 2 environment variables in your OS env. 
```
COMPUTERVISION_SUBSCRIPTION_KEY
COMPUTERVISION_LOCATION
```
The ComputerVision location refers to the region you have registered your Azure Computer Vision service. You only need the region there. 
```
COMPUTERVISION_SUBSCRIPTION_KEY="..."
COMPUTERVISION_LOCATION="westeurope"
```

### Google 
Refer to Google documentation to authenticate the Google Client : https://cloud.google.com/vision/docs/ocr#set-up-your-gcp-project-and-authentication

## BBoxHelper - Run the Sample script(s) 

Each supported OCR platform has a corresponding testing script 

Under the project python directory,
1. execute the **bboxtester.azure.py** for testing with Microsoft Azure Computer Vision OCR. 
2. execute the **bboxtester.google.py** for testing with Google Computer Vision OCR. 

Each sample script will
1. process all images located under the images script (one level of the python dir), 
2. call the corresponding OCR service, 
3. persist the raw ocr response on disk in the tests-results or the directory of your choice
4. persist the original image with the bouding boxes of the raw OCR response
5. call on the BBOx Helper processOCRResponse() method. 
6. persist the original image with the bouding boxes of the BBoxHelper OCR response .

### Changing the input and output directories used in the samples scripts
```
IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")
```
**NOTE** The RESULTS_FOLDER is created upon running the sample script if not already existing. 

### Calling the BBoxHelper main method 

#### For Azure 

If you have the response object from client.get_read_operation_result() 
```
# Azure Computer Vision Call
with open(os.path.join(IMAGES_FOLDER, filename), "rb") as image_stream:
    job = client.batch_read_file_in_stream(
        image=image_stream,
        raw=True
    )
operation_id = job.headers['Operation-Location'].split('/')[-1]

image_analysis = client.get_read_operation_result(operation_id,raw=True)
while image_analysis.output.status in ['NotStarted', 'Running']:
    time.sleep(1)
    image_analysis = client.get_read_operation_result(operation_id=operation_id,raw=True)
...
ocrresponse=image_analysis.response.content.decode("utf-8")
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse,sortingAlgo=BBoxSort.contoursSort)
```
The BBoxHelper().processAzureOCRResponse() method will accept a string, dict (JSON) or BBOXOCRResponse instance. 

Passing a dict object (really if you want to)
```
bboxresponse=BBoxHelper().processAzureOCRResponse(json.loads(ocrresponse),sortingAlgo=BBoxSort.contoursSort)
```
You can create an BBOXOCRResponse object and send it as is as well. This is usefull to draw the bounding boxes Before and After (see the sample script)
```
ocrresponse=BBOXOCRResponse.from_azure(json.loads(ocrresponse))
bboxresponse=BBoxHelper().processAzureOCRResponse(copy.deepcopy(ocrresponse),sortingAlgo=BBoxSort.contoursSort)
```

**Note** : BBoxHelper.processOCRResponse() manipulates the original object, if you need to keep the "original" ocr response make sure to do a copy.deepcopy() beforehands.

#### For Google

```
response = client.document_text_detection(image=image)
document = response.full_text_annotation
...
bboxresponse=BBoxHelper().processGoogleOCRResponse(document)
```

## Suggestions
