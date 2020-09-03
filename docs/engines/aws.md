# AWS Textexract - Detecting Text (OCR)

BBOXHelper supports AWS Textract detect_document_text for single-page documents. 

>Amazon Textract operations process document images that are stored on a local file system, or document images stored in an Amazon S3 bucket. You specify where the input document is located by using the Document input parameter. The document image can be in either PNG or JPEG format.

## AWS Textextract Documentation

1. [AWS Textextract - Detecting Text](https://docs.aws.amazon.com/textract/latest/dg/how-it-works-detecting.html)
2. [AWS Textextract - Detecting Text Example](https://docs.aws.amazon.com/textract/latest/dg/detecting-document-text.html)
3. [Document entity](https://docs.aws.amazon.com/textract/latest/dg/API_Document.html)

## AWS Python Example
```python
#Detects text in a document stored in an S3 bucket. Display polygon box around text and angled text 
import boto3
import io
from io import BytesIO
import sys

import psutil
import time

import math
from PIL import Image, ImageDraw, ImageFont


# Displays information about a block returned by text detection and text analysis
def DisplayBlockInformation(block):
    print('Id: {}'.format(block['Id']))
    if 'Text' in block:
        print('    Detected: ' + block['Text'])
    print('    Type: ' + block['BlockType'])
   
    if 'Confidence' in block:
        print('    Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

    if block['BlockType'] == 'CELL':
        print("    Cell information")
        print("        Column:" + str(block['ColumnIndex']))
        print("        Row:" + str(block['RowIndex']))
        print("        Column Span:" + str(block['ColumnSpan']))
        print("        RowSpan:" + str(block['ColumnSpan']))    
    
    if 'Relationships' in block:
        print('    Relationships: {}'.format(block['Relationships']))
    print('    Geometry: ')
    print('        Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
    print('        Polygon: {}'.format(block['Geometry']['Polygon']))
    
    if block['BlockType'] == "KEY_VALUE_SET":
        print ('    Entity Type: ' + block['EntityTypes'][0])
    if 'Page' in block:
        print('Page: ' + block['Page'])
    print()

def process_text_detection(bucket, document):

    
    #Get the document from S3
    s3_connection = boto3.resource('s3')
                          
    s3_object = s3_connection.Object(bucket,document)
    s3_response = s3_object.get()

    stream = io.BytesIO(s3_response['Body'].read())
    image=Image.open(stream)

   
    # Detect text in the document
    
    client = boto3.client('textract')
    #process using image bytes                      
    #image_binary = stream.getvalue()
    #response = client.detect_document_text(Document={'Bytes': image_binary})

    #process using S3 object
    response = client.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': document}})

    #Get the text blocks
    blocks=response['Blocks']
    width, height =image.size  
    draw = ImageDraw.Draw(image)  
    print ('Detected Document Text')
   
    # Create image showing bounding box/polygon the detected lines/text
    for block in blocks:
            print('Type: ' + block['BlockType'])
            if block['BlockType'] != 'PAGE':
                print('Detected: ' + block['Text'])
                print('Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

            print('Id: {}'.format(block['Id']))
            if 'Relationships' in block:
                print('Relationships: {}'.format(block['Relationships']))
            print('Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
            print('Polygon: {}'.format(block['Geometry']['Polygon']))
            print()
            draw=ImageDraw.Draw(image)
            # Draw WORD - Green -  start of word, red - end of word
            if block['BlockType'] == "WORD":
                draw.line([(width * block['Geometry']['Polygon'][0]['X'],
                height * block['Geometry']['Polygon'][0]['Y']),
                (width * block['Geometry']['Polygon'][3]['X'],
                height * block['Geometry']['Polygon'][3]['Y'])],fill='green',
                width=2)
            
                draw.line([(width * block['Geometry']['Polygon'][1]['X'],
                height * block['Geometry']['Polygon'][1]['Y']),
                (width * block['Geometry']['Polygon'][2]['X'],
                height * block['Geometry']['Polygon'][2]['Y'])],
                fill='red',
                width=2)    

                 
            # Draw box around entire LINE  
            if block['BlockType'] == "LINE":
                points=[]

                for polygon in block['Geometry']['Polygon']:
                    points.append((width * polygon['X'], height * polygon['Y']))

                draw.polygon((points), outline='black')    
  
                # Uncomment to draw bounding box
                #box=block['Geometry']['BoundingBox']                    
                #left = width * box['Left']
                #top = height * box['Top']           
                #draw.rectangle([left,top, left + (width * box['Width']), top +(height * box['Height'])],outline='black') 


    # Display the image
    image.show()
    # display image for 10 seconds

    
    return len(blocks)

def main():

    bucket = ''
    document = ''
    block_count=process_text_detection(bucket,document)
    print("Blocks detected: " + str(block_count))
    
if __name__ == "__main__":
    main()
```
## AWS BBoxHelper Integration
Import the below ocrlayout classes
```python
# AWS 
import boto3 
from PIL import Image
from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper
```
Create the Textextract client 
```python
# Amazon Textract client
textract = boto3.client('textract')
```
Capture the detect_document_text method passing the document as byte-array object. Refer to the [Document documentation](https://docs.aws.amazon.com/textract/latest/dg/API_Document.html) on how to build a Document object.
```python
# Call Amazon Textract
ocrresponse = textract.detect_document_text(Document={'Bytes': bytes_test })
```
Pass it to the BBoxHelper processing method **processAWSOCRResponse()**. 
>AWS Textextract doesn't provide the Width and Height as part of their detect_document_text response object. We do need those for correctly processing the bboxes hence we provide those with the processing method as parameters.
```python
# Retrieving the image width and height
imagefn=os.path.join(IMAGES_FOLDER, filename)
image = Image.open(imagefn)
width, height = image.size
# Create BBOX OCR Response from AWS string response
bboxresponse=BBoxHelper.processAWSOCRResponse(ocrresponse,width,height)
```
Print the resulting text
```python
print(bboxresponse.text)
```

### Behind the scene...
The method **processAWSOCRResponse()** supports passing a string, JSON object or an existing BBOXOCRResponse.
####Snippet of the **bboxhelper.py** to process an AWS OCR response
```python
class BBOXPageLayout():
...
    @classmethod
    def from_aws(cls, page, width, height):
        lines=list()
        ...
...
class BBOXOCRResponse():
...
    @classmethod
    def from_aws_detect_document_text(cls, data, width, height):
        pages=list()
        pages.append(BBOXPageLayout.from_aws(data["Blocks"],width,height))
        if "status" in data:
            status = data["status"]
        else:
            status = "awssuccess"

        return cls(status=status,recognitionResults=pages)
...
class BBoxHelper():
...
    def processAWSOCRResponse(self,input,width,height,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,verbose=None):
        """ processAWSOCRResponse method
            Process an OCR Response input from AWS and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)

        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_aws_detect_document_text(json.loads(input),width,height)
        if isinstance(input,dict):
            response=BBOXOCRResponse.from_aws_detect_document_text(input,width,height)
        elif isinstance(input,BBOXOCRResponse):
            response=input

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator)
...
```

### Reading the response from a file and send it to BBOX processing
```python
# Use local OCR cached response when available
with open(os.path.join(self.RESULTS_FOLDER, imgname+".aws.textextract.json"), 'r') as cachefile:
    ocrresponse = cachefile.read().replace('\n', '')

# Retrieving the image width and height
imagefn=os.path.join(IMAGES_FOLDER, imgname)
image = Image.open(imagefn)
width, height = image.size

# Create BBOX OCR Response from AWS string response
bboxresponse=BBoxHelper.processAWSOCRResponse(ocrresponse,width,height)

# Print the output text
print(bboxresponse.text)
```