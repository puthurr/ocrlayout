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
## Prepare your OCR engine(s) call(s)
Depending on your preferred OCR service Azure, Google or AWS, follow the corresponding instructions.
### Azure 
Set the below 2 environment variables in your OS env. 
```
COMPUTERVISION_SUBSCRIPTION_KEY
COMPUTERVISION_LOCATION
```
The ComputerVision location refers to the region you have registered your Azure Computer Vision service. You only need the region there. 
```python
COMPUTERVISION_SUBSCRIPTION_KEY="..."
COMPUTERVISION_LOCATION="westeurope"
```
### Google 
Google documentation to authenticate the [Google Client](https://cloud.google.com/vision/docs/ocr#set-up-your-gcp-project-and-authentication)
### AWS 
AWS documentation to get started with [Amazon Textract](https://docs.aws.amazon.com/textract/latest/dg/getting-started.html)
## Calling the BBoxHelper main method
if you are not familiar with Azure CV, Google & AWS Text detection first hands I would encourage you to jump the [Sample script](#bboxhelper-run-the-sample-script-in-github) section as it would help getting hands on experience. 
#### Azure
>Azure response is a JSON string object hence we can send it as-is to processing after decoding. 
```python
ocrresponse=image_analysis.response.content.decode("utf-8")
...
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse)
print(bboxresponse.text)
```
#### Google
```python
response = google_client.document_text_detection(image=image)
# Convert the response object to JSON
json_string=json_format.MessageToJson(response)
...
# Create BBOX OCR Response from Google's JSON output
bboxresponse=BBoxHelper().processGoogleOCRResponse(json_string)
print(bboxresponse.text)
```
>Passing the full_text_annotation object itself will not work anymore (ocrlayout>=0.8), only a JSON string or dict object are supported hence the JSON MessageToJson invocation.

#### AWS 
>AWS response is Dictionary-based object hence we can send it as-is to processing. 
```python
# Amazon Textract client
textract = boto3.client('textract')
# Call Amazon Textract
ocrresponse = textract.detect_document_text(Document={'Bytes': bytes_test })
# Getting the width and height of the image
imagefn=os.path.join(IMAGES_FOLDER, filename)
image = Image.open(imagefn)
width, height = image.size
# Create BBOX OCR Response from AWS string response
bboxresponse=BBoxHelper().processAWSOCRResponse(ocrresponse,width,height,verbose=verbose)
```
#### Notes
The BBoxHelper().processXXXOCRResponse() method will accept a JSON string, JSON/Dictionary object or existing BBOXOCRResponse object. 

All processXXXOCRResponse methods will check on the input object type to convert it to a BBOXOCRResponse object.

```python
# Load the input into a BBOXOCRResponse object for processing
if isinstance(input,str):
    response=BBOXOCRResponse.from_xxx(json.loads(input))
if isinstance(input,dict):
    response=BBOXOCRResponse.from_xxx(input)
elif isinstance(input,BBOXOCRResponse):
    response=input
```
Once the input is converted to an non-optimized BBOXOCRResponse object it goes into the processing phase. 
```python
if response:
    return self.__processOCRResponse(response,sortingAlgo,boxSeparator)
```

**Important** Passing an existing BBOXOCRResponse object to any BBoxHelper.processXXXOCRResponse() method will modify the object.

If you need to keep the "original" BBOXOCRResponse make sure to do a copy.deepcopy() beforehands.
```python
bboxresponse=BBoxHelper().processAzureOCRResponse(copy.deepcopy(ocrresponse))
```
This could be usefull for evaluating OCR Engine(s) quality response (see the sample script) and ocrlayout optimization (before/after).

## BBoxHelper - Response object
- status : reflect the original status of your ocr request response. 
- original_text : the original text provide by the default OCR engine when relevant. 
- **text** : representing the sorted text of all processed pages. 
- pages : List of all pages. The OCR Engines we support allows you to send full PDF or TIFF multiple pages. 

```python
print(bboxresponse.text)
```
## BBoxHelper - Run the sample script in github
We provided a single sample script to showcase how BBoxHelper runs against Azure and Google OCR engines output. 
### Under the project python directory in a terminal
Execute the sample script **[bboxtester.py](https://github.com/puthurr/ocrlayout/blob/master/python/bboxtester.py)** for testing with Microsoft Azure CV or Google CV. 
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

### DISCLAIMER
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.