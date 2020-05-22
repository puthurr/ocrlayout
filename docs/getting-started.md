The ocrlayout library contains our main class named BBoxHelper.

## Before you start
ocrlayout package has been developed for Python 3.7+. Refer to the package documentation for more details. 

[Package Documentation](https://pypi.org/project/ocrlayout/)
## Ocrlayout package install
```
pip install ocrlayout
```
## Import the BBoxHelper and BBOXOCRResponse classes
```python
from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper
```
## For reference: prep your OCR engine(s)
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
Refer to Google documentation to authenticate the [Google Client](https://cloud.google.com/vision/docs/ocr#set-up-your-gcp-project-and-authentication)

## Calling the BBoxHelper main method 

#### For Azure 

If you have the response object from client.get_read_operation_result() 
```python
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
```python
bboxresponse=BBoxHelper().processAzureOCRResponse(json.loads(ocrresponse),sortingAlgo=BBoxSort.contoursSort)
```
You can create an BBOXOCRResponse object and send it as is as well. This is usefull to draw the bounding boxes Before and After (see the sample script)
```python
ocrresponse=BBOXOCRResponse.from_azure(json.loads(ocrresponse))
bboxresponse=BBoxHelper().processAzureOCRResponse(copy.deepcopy(ocrresponse),sortingAlgo=BBoxSort.contoursSort)
```

**Note** : BBoxHelper.processOCRResponse() manipulates the original object, if you need to keep the "original" ocr response make sure to do a copy.deepcopy() beforehands.

#### For Google
```python
response = client.document_text_detection(image=image)
...
bboxresponse=BBoxHelper().processGoogleOCRResponse(response.full_text_annotation)
```


## BBoxHelper - Run the sample script

Provided a single sample script to showcase how BBoxHelper runs against Azure and Google OCR engines output. 

### Under the project python directory

Execute the **bboxtester.py** for testing with Microsoft Azure CV or Google CV. 

### Sample script invocation
```
python3 bboxtester.py -h
```
The help output
```
Local Package imported
usage: bboxtester.py [-h] [--image IMAGE] [--imagesdir IMAGESDIR]
                     [--filter FILTER] [--outputdir OUTPUTDIR] [--callocr]
                     [-v]

Call OCR outputs for a given image or images dir

optional arguments:
  -h, --help            show this help message and exit
  --image IMAGE         Process a single image
  --imagesdir IMAGESDIR
                        Process all images contained in the given directory
  --filter FILTER       Filter the images to process based on their filename
  --outputdir OUTPUTDIR
                        Define where all outputs will be stored
  --callocr             flag to invoke online OCR Service
  -v, --verbose         DEBUG logging level
```

#### Invoke on a single image 
```
bboxtester.py --image <FULL_IMAGE_PATH>
```
Example
```
bboxtester.py --image /Users/../../../../images/infography1.jpeg
```
#### Invoke for all images from the default IMAGES_FOLDER
```
python3 bboxtester.py
```
Use the --imagesdir flag to set a different directory 
```
python3 bboxtester.py --imagesdir <NEW_IMAGE_DIR>
```
#### Invoke for all images which name contains "scan1"
```
python3 bboxtester.py --filter scan1
```

you get the idea...

**Few notes**

- The sample script can run against the local ocrlayout directory if you haven't installed the ocrlayout package, simply run it from where the sample script is located. 
- The callocr flag means we will invoke the online OCR service to process an image. Not setting that flag means we will rely on the previous call to the OCR Engine which we saved on disk the output (reducing your online service consumption cost for testing) 
- if the flag *callocr* is on but there is no previously cache output on disk from a specific OCR engine, we will revert to invoke the online OCR service. 
- If you only interested in testing a single OCR Engine, simply comment out the function prefix by either google_ or axure_ in bboxtester.py. The code detect automatically which function to run based on its signature.


### Sample script flow 
1. process one or all images located under the images script (one level of the python dir), 
2. call the corresponding OCR service, 
3. persist the raw ocr response on disk in the tests-results or the directory of your choice
4. persist the original image with the bouding boxes of the raw OCR response
5. call on the BBOx Helper processOCRResponse() method. 
6. persist the original image with the bouding boxes of the BBoxHelper OCR response .

### Sample script Output

Each Sample script will output 

- Azure Annotated Image where we draw the lines its OCR 
- Azure OCR JSON 
- Azure OCR Text (textual information)
- Google Annotated Image where we draw the lines its OCR 
- Google OCR Text (textual information)

Those outputs allow you to evaluate the different OCR output visually.

### Changing the default input and output directories used in the sample script
```python
IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results")
```
**NOTE** The RESULTS_FOLDER is created upon running the sample script if not already existing. 
