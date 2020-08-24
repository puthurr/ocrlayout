# Import required modules.
import io
import json
import logging
import logging.config
import math
import os
import random
import re
import time
import uuid
from datetime import datetime
from os import path
from typing import List

import numpy as np

from .bboxutils import BBOXAnnotate, BBoxSort, BBoxUtils

# Constants
LeftAlignment="LeftAlignment"
RightAlignment="RightAlignment"
CenteredAlignment="CenteredAlignment"

Alignments = [LeftAlignment,RightAlignment,CenteredAlignment]

global bboxconfig
global bboxlogger 

from .bboxconfig import BBOXConfig
bboxconfig = BBOXConfig.get_config()

from . import bboxlog
bboxlogger = bboxlog.get_logger()

# Load Default HTML Annotations
json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/annotations.json")
with open(json_file_path) as json_file:
    bboxannotate=BBOXAnnotate.from_json(json.loads(json_file.read()))

#
# Bounding Boxes OCR Classes
#
class BBOXPoint():
    def __init__(self, X: float = 0.0, Y: float = 0.0, ppi=1):
        self.X = X*ppi
        self.Y = Y*ppi
    # Reverse a BBOX Point X,Y coordinates
    def inv(self):
        return BBOXPoint(self.Y,self.X)   
    def __repr__(self):
        return "[{0},{1}]".format(str(self.X),str(self.Y))

    @classmethod
    def from_azure(cls, data):
        return cls(**data)

    @classmethod
    def from_azure_ocr(cls, array, ppi):
        array=array.split(',')
        array = [ float(x) for x in array]
        # This a rectangle coordinates not a bounding boxes per se
        points=list()
        points.append(BBOXPoint(array[0],array[1],ppi))
        points.append(BBOXPoint(array[0]+array[2],array[1],ppi))
        points.append(BBOXPoint(array[0]+array[2],array[1]+array[3],ppi))
        points.append(BBOXPoint(array[0],array[1]+array[3],ppi))
        return points

    @classmethod
    def from_azure_read_2(cls, array, ppi):
        points = list()
        x = array[0]
        y = array[1]          
        points.append(BBOXPoint(x,y,ppi))
        x = array[2]
        y = array[3]
        points.append(BBOXPoint(x,y,ppi))
        x = array[4]
        y = array[5]
        points.append(BBOXPoint(x,y,ppi))
        x = array[6]
        y = array[7]
        points.append(BBOXPoint(x,y,ppi))
        return points

    @classmethod
    def from_aws(cls, data):
        return cls(**data)

class BBOXNormalizedLine():
    def __init__(self, Idx, BoundingBox: List[BBOXPoint], Text:str = None, merged:bool=False, avg_height=0.0, std_height=0.0, words_count=0):
        self.start_idx=Idx+1
        self.end_idx=Idx+1
        self.boundingbox = BoundingBox
        self.text = None
        self.words_count=words_count
        self.merged = merged
        self.calculateMedians()
        self.__appendText(Text)
        self.avg_height = avg_height
        self.std_height = std_height
        self.rank=0.0

    def calculateMedians(self):
        self.xmedian=(min(self.boundingbox[0].X,self.boundingbox[3].X) + max(self.boundingbox[1].X,self.boundingbox[2].X))/2
        self.ymedian=(min(self.boundingbox[0].Y,self.boundingbox[3].Y) + max(self.boundingbox[1].Y,self.boundingbox[2].Y))/2

    def getLineWidthHeight(self):
        return ((self.boundingbox[3].X-self.boundingbox[0].X), (self.boundingbox[3].Y-self.boundingbox[0].Y))
    def getRootX(self):
        return self.boundingbox[0].X
    def getRootY(self):
        return self.boundingbox[0].Y
    def getClusterId(self):
        return self.listids[0]

    def getBoxesAsArray(self,scale=1):
        result=[]
        for box in self.boundingbox:
            result.append([box.X*scale,box.Y*scale])
        return result

    def getWidthRange(self,scale=1):
        return (int(self.boundingbox[0].X*scale),int(self.boundingbox[1].X*scale))

    def getHeightRange(self,scale=1):
        return (int(self.boundingbox[0].Y*scale),int(self.boundingbox[3].Y*scale))

    def getBoxesAsRectangle(self,scale=1):
        return (int(self.boundingbox[0].X*scale),int(self.boundingbox[0].Y*scale),int(self.boundingbox[2].X-self.boundingbox[0].X)*scale,int(self.boundingbox[2].Y-self.boundingbox[0].Y)*scale)

    def __appendText(self,Text,lineMergeChar=''):
        # TODO #2
        if self.text:
            # Word ceasure with a single dash
            if self.text.endswith('-'):
                self.text = self.text[:-1]+Text.strip()
            else:
                self.text += (lineMergeChar + Text.strip())
                pass
        else:
            self.text=Text.strip()

        # Flag for sentence for future use (NLP support)
        if Text.endswith('.'):
            self.end_sentence=True
        else:
            self.end_sentence=False

    def mergeLine(self,line,lineMergeChar):
        line.merged = True
        self.__appendText(line.text,lineMergeChar)
        self.boundingbox[0] = BBoxUtils.minXminY(0,self,line)
        self.boundingbox[1] = BBoxUtils.maxXminY(1,self,line)
        self.boundingbox[2] = BBoxUtils.maxXmaxY(2,self,line)
        self.boundingbox[3] = BBoxUtils.minXmaxY(3,self,line)
        self.calculateMedians()
        self.end_idx=line.end_idx
        self.words_count+=line.words_count
        
    @classmethod
    def from_azure(cls, index, data, ppi):
        points = list()
        words=list()
        line_text=''
        array=data["boundingBox"]
        # OCR Support       
        if isinstance(array,str):
            points = BBOXPoint.from_azure_ocr(array,ppi)           
            for wordbox in data['words']:
                words.append(BBOXPoint.from_azure_ocr(wordbox["boundingBox"],ppi))
                line_text+=wordbox['text']
                line_text+=' '
        elif ( len(array) > 4 ):
            points = BBOXPoint.from_azure_read_2(array,ppi)
            for wordbox in data['words']:
                words.append(BBOXPoint.from_azure_read_2(wordbox["boundingBox"],ppi))
        else:
            points = list(map(BBOXPoint.from_azure, [ppi*x for x in array]))
            for wordbox in data['words']:
                words.append(list(map(BBOXPoint.from_azure, [ppi*x for x in wordbox["boundingBox"]])))

        if "text" in data:
            line_text=data["text"]

        # Ensure the first word bbox is consistend with the line bbox
        if len(words)>0:
            points[0].X = max(words[0][0].X,points[0].X)
            points[3].X = max(words[0][3].X,points[3].X)

        # Check Line cohenrence on Height
        wordheights=[]
        for wordbox in words:
            wordheights.append(wordbox[3].Y-wordbox[0].Y)

        # calculate the average
        npheights = np.array(wordheights)
        avg_height = np.average(npheights)
        std_height = np.std(npheights, dtype=np.float64)
        return cls(Idx=index,BoundingBox=points,Text=line_text,std_height=std_height,avg_height=avg_height,words_count=len(words))

    @classmethod
    def from_google(cls, line_counter, line_text, line_boxes, words_count):
        points = list()
        for bb in range(4):
            points.append(BBOXPoint(0,0))
        # 
        points[0].X = line_boxes[0][0]["x"] 
        points[0].Y = line_boxes[0][0]["y"] 
        points[3].X = line_boxes[0][3]["x"] 
        points[3].Y = line_boxes[0][3]["y"]

        points[1].X = line_boxes[-1][1]["x"] 
        points[1].Y = line_boxes[-1][1]["y"] 
        points[2].X = line_boxes[-1][2]["x"] 
        points[2].Y = line_boxes[-1][2]["y"] 

        return BBOXNormalizedLine(Idx=line_counter,BoundingBox=points,Text=line_text,words_count=words_count)

    @classmethod
    def from_aws(cls, index, data):
        points = list()
        line_text=''
        array=data["Geometry"]["Polygon"]
        points = list(map(BBOXPoint.from_aws, [x for x in array]))

        if "Text" in data:
            line_text=data["Text"]

        return cls(Idx=index,BoundingBox=points,Text=line_text,std_height=0,avg_height=0,words_count=0)

class BBOXPageLayout():
    def __init__(self, Id:int = 0,clockwiseorientation:float = 0.0,Width:float = 0.0,Height:float = 0.0,Unit:str = "pixel",Language:str="en",Text:str=None,Lines:List[BBOXNormalizedLine]=None,ppi=1):
        self.id=Id
        self.clockwiseorientation=clockwiseorientation
        self.width=Width
        self.height=Height
        self.unit=Unit
        self.language=Language
        self.text=Text
        self.lines=Lines
        self.ppi=ppi

    @classmethod
    def from_azure(cls, page):
        lines=list()
        # TODO #1
        if "unit" in page:
            page_unit=page["unit"]
            if page_unit=="inch":
                # Azure OCR response doesn't provide the ppi per page
                # so we need to determine it for normalizing the processing of lines
                # ppi=BBoxUtils.determine_ppi(data["width"],data["height"])
                
                # decimal precision on Azure is set to 4, so we can set a 10000 to normalize the box and 
                # not convert to pixel
                ppi=10000
            else:
                ppi=1
        else:
            page_unit="pixel"
            ppi=1

        # Page Width / Heigth
        if "width" in page:
            page_width=page["width"]
            page_height=page["height"]
        else:
            page_width=0
            page_height=0

        # Support for Azure OCR response (single page)
        if "regions" in page:
            merged_lines=list()
            for region in page["regions"]:
                for line in region["lines"]:
                    merged_lines.append(line)
            lines=[BBOXNormalizedLine.from_azure(i,line, 1) for i,line in enumerate(merged_lines)]
            # Azure OCR doesn't provide width/height data
            npx = np.array([x.getRootX() for x in lines])
            page_width = np.max(npx)-np.min(npx)
            npy = np.array([y.getRootY() for y in lines])
            page_height = np.max(npy)-np.min(npy)
        else:
            lines=[BBOXNormalizedLine.from_azure(i,line, 1) for i,line in enumerate(page["lines"])]

        bboxlogger.debug("Azure|Page shape (Height,Width) ({0},{1})".format(page_width,page_height))

        angle=0.0
        # >=0.6.0
        if "angle" in page:
            angle = page["angle"]
        # <= 0.5.0
        elif "clockwiseorientation" in page:
            angle = page["clockwiseorientation"]
        # OCR Support
        elif "textAngle" in page:
            angle = page["textAngle"]

        # Page Id
        if "page" in page:
            page_id=page["page"]
        else:
            page_id="0"

        return cls(Id=page_id,clockwiseorientation=angle,Width=page_width,Height=page_height,Unit=page_unit,Lines=lines,ppi=ppi)

    @classmethod
    def from_google(cls, page):
        # Initialization
        lines=[]
        line_counter=0
        line_text =""
        line_boxes=[]
        line_words_count=0
        page_width=page["width"]
        page_height=page["height"]
        bboxlogger.debug("Google|Page shape (Height,Width) ({0},{1})".format(page_height,page_width))
        # Create the concept of lines for Google ocr response. 
        for idb, block in enumerate(page["blocks"]):
            for paragraph in block["paragraphs"]:
                pagearray = np.zeros((page_height,page_width))
                # parray=page[paragraph.bounding_box.vertices[0].y:paragraph.bounding_box.vertices[2].y,paragraph.bounding_box.vertices[0].x:paragraph.bounding_box.vertices[2].x]
                bboxlogger.debug("Google|Paragraph {0} of {1} words".format(str(idb),str(len(paragraph["words"]))))
                for widx, word in enumerate(paragraph["words"]):
                    # Put the word presence in the paragraph matrix 
                    low_y=word["boundingBox"]["vertices"][0]["y"]-1
                    high_y=word["boundingBox"]["vertices"][2]["y"]
                    low_x=word["boundingBox"]["vertices"][0]["x"]-1
                    high_x=word["boundingBox"]["vertices"][2]["x"]
                    # the Min,Max allows us to handle vertical words. 
                    pagearray[min(low_y,high_y):max(low_y,high_y),min(low_x,high_x):max(low_x,high_x)]=widx+1

                columns=BBoxSort.findClusters(pagearray,axis=0,gapthreshhold=bboxconfig.config["pixel"].GoogleLineBreakThresholdInPixel)

                # Assign the first cluster as current
                currentTextColumn = columns[0]

                for widx, word in enumerate(paragraph["words"]):
                    if len(columns)==1:
                        foundTextColumn = columns[0]
                    else:                       
                        # Find the word cluster
                        for cidx,column in enumerate(columns):
                            if word["boundingBox"]["vertices"][0]["x"] >= column[0] and word["boundingBox"]["vertices"][0]["x"] <= column[1]:
                                foundTextColumn = column
                                bboxlogger.debug("Google|Word Idx:{0} X:{1} in Cluster {2}".format(widx,word["boundingBox"]["vertices"][0]["x"],column))

                    # Line break on text columns change.
                    if len(line_boxes)>0:
                        if foundTextColumn != currentTextColumn:
                            # xdiff=(word.bounding_box.vertices[0].x - line_boxes[-1][1].x)
                            # if xdiff > bboxconfig.config["pixel"].GoogleLineBreakThresholdInPixel:
                                bboxlogger.debug("Google|Detected Cluster Break current {0} found {1} | {2} {3}".format(currentTextColumn,foundTextColumn,str(line_counter),line_text))
                                # Line break
                                line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes,words_count=line_words_count)
                                lines.append(line)
                                line_text=""
                                line_counter+=1
                                line_boxes.clear()
                                line_words_count=0

                    currentTextColumn=foundTextColumn
                    line_boxes.append(word["boundingBox"]["vertices"])                   
                    line_words_count+=1
                    for symbol in word["symbols"]:
                        line_text+=symbol["text"]
                        if "property" in symbol:
                            if "detectedBreak" in symbol["property"]:
                                bboxlogger.debug("Google|Detected Break {0}".format(str(symbol["property"]["detectedBreak"]["type"])))                            
                                if symbol["property"]["detectedBreak"]["type"] in ['SPACE','SURE_SPACE',1,2]:
                                    line_text+=" "
                                elif symbol["property"]["detectedBreak"]["type"] in ['EOL_SURE_SPACE','LINE_BREAK',3,5]:
                                    bboxlogger.debug("Google|Detected Line Break {0}| {1} {2}".format(str(symbol["property"]["detectedBreak"]["type"]),str(line_counter),line_text))
                                    # Line Break
                                    line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes,words_count=line_words_count)
                                    lines.append(line)
                                    line_text=""
                                    line_counter+=1
                                    line_boxes.clear()
                                    line_words_count=0                                

        return cls(Id=1,Width=page_width,Height=page_height,Lines=lines)

    @classmethod
    def from_aws(cls, page, width, height):
        lines=list()

        # TODO #1
        if "unit" in page:
            page_unit=page["unit"]
            if page_unit=="inch":
                # Azure OCR response doesn't provide the ppi per page
                # so we need to determine it for normalizing the processing of lines
                # ppi=BBoxUtils.determine_ppi(data["width"],data["height"])
                
                # decimal precision on Azure is set to 4, so we can set a 10000 to normalize the box and 
                # not convert to pixel
                ppi=10000
            else:
                ppi=1
        else:
            page_unit="pixel"
            ppi=1

        # Page Width / Heigth
        if "width" in page:
            page_width=page["width"]
            page_height=page["height"]
        else:
            page_width=width
            page_height=height

        # Denormalize the Geometry/Polygon
        for block in page:
            for coordinate in block["Geometry"]["Polygon"]:
                coordinate["X"]=coordinate["X"]*width
                coordinate["Y"]=coordinate["Y"]*height

        lines=[BBOXNormalizedLine.from_aws(i,line) for i,line in enumerate(page) if (line["BlockType"] == "LINE")]

        bboxlogger.debug("AWS|Page shape (Height,Width) ({0},{1})".format(page_width,page_height))

        # AWS doesn't provide an angle or text orientation
        angle=0.0

        # Page Id
        if "page" in page:
            page_id=page["page"]
        else:
            page_id="1"

        return cls(Id=page_id,clockwiseorientation=angle,Width=page_width,Height=page_height,Unit=page_unit,Lines=lines,ppi=ppi)


class BBOXOCRResponse():
    def __init__(self,status:str = None,Text:str=None,original_text:str=None,recognitionResults:List[BBOXPageLayout]=None):
        self.status =status
        self.original_text=original_text
        self.text=Text
        self.pages=recognitionResults

    @classmethod
    def from_azure(cls, data):
        pages=list()
        # Convert to JSON dict if a JSON string is passed.
        if isinstance(data,str):
            data=json.loads(data)
        # Breaking change from Azure Computer Vision in 0.6.0. Response Model has changed. 
        # https://github.com/Azure/azure-sdk-for-python/commit/99668db644fe606c24cc7cb553135b6614c10ffd#diff-6f3fc7f0ca3bec21308cea3f35f37afc
        # <= 0.5.0
        if "recognitionResults" in data:
            pages = list(map(BBOXPageLayout.from_azure, data["recognitionResults"]))
        # >=0.6.0
        elif "analyzeResult" in data:
            if "readResults" in data["analyzeResult"]:
                pages = list(map(BBOXPageLayout.from_azure, data["analyzeResult"]["readResults"]))
        # Support for the OCR API (old CV modles from Azure) - single page 
        elif "regions" in data:
            pages.append(BBOXPageLayout.from_azure(data))

        if "status" in data:
            status = data["status"]
        else:
            status = "ocrsuccess"

        return cls(status=status,recognitionResults=pages)
    
    @classmethod
    def from_google(cls, data):
        if "fullTextAnnotation" in data:
            pages = list(map(BBOXPageLayout.from_google,data["fullTextAnnotation"]["pages"]))
            return cls(status="success",original_text=data["fullTextAnnotation"]["text"],recognitionResults=pages)

    @classmethod
    def from_aws_detect_document_text(cls, data, width, height):
        pages=list()
        pages.append(BBOXPageLayout.from_aws(data["Blocks"],width,height))
        if "status" in data:
            status = data["status"]
        else:
            status = "awssuccess"

        return cls(status=status,recognitionResults=pages)

class BBoxHelper():

    # Support to use a custom configuration, annotation and logging file.
    def __init__(self, customcfgfilepath=None, customlogfilepath=None, annotate=False, annotationconfig=None,verbose=None):
        global bboxlogger,bboxconfig,bboxannotate
        if customcfgfilepath:
            with open(customcfgfilepath) as json_file:
                bboxconfig=BBOXConfig.from_json(json.loads(json_file.read()))
        if customlogfilepath:
            logging.config.fileConfig(customlogfilepath)
            bboxlogger = logging.getLogger('bboxhelper')
        else:
            if verbose:
                bboxlogger.setLevel(logging.DEBUG)
        self.annotate=annotate
        if annotationconfig:
            bboxannotate=BBOXAnnotate.from_json(json.loads(annotationconfig))

    def processAzureOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,verbose=None):
        """ processAzureOCRResponse method
            Process an OCR Response input from Azure and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)

        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_azure(json.loads(input))
        if isinstance(input,dict):
            response=BBOXOCRResponse.from_azure(input)
        elif isinstance(input,BBOXOCRResponse):
            response=input

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator)

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


    def __processOCRResponse(self, response, sortingAlgo=BBoxSort.contoursSort, boxSeparator:str = None):
        """processOCRResponse method
        Process an OCR Response input (Azure,Google) and returns a new BBox format OCR response.

        Iterate through each page of the response and process it. Before processing we tackle the boxes 
        orientation. 
        """
        newtext = ""

        # Rotate the BBox of each page based on its corresponding orientation
        for page in response.pages:
            bboxlogger.debug("{0}|Processing Page {0} with {1} lines.".format(str(page.id),len(page.lines)))
            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[0]
            rotation = round(page.clockwiseorientation,0)
            bboxlogger.debug("{0}|Orientation {1}".format(str(page.id),str(rotation)))
            page_width=page.width
            page_height=page.height
            # Bounding Boxes Orientation
            # if ( rotation != 0):
            #     # TODO Do the Math for clockwise orientation
            #     for line in page.lines:
            #         bboxlogger.debug("Before rotation {}".format(line.boundingbox))
            #         test = BBoxUtils.rotateLineBoundingBox(line.boundingbox, -1*page.clockwiseorientation)
            #         bboxlogger.debug("After rotation 1 {}".format(test))
            #         test = BBoxUtils.rotateLineBoundingBox(line.boundingbox, page.clockwiseorientation)
            #         bboxlogger.debug("After rotation 2 {}".format(test))

            rotation_threshold=1

            applied_rotation=0 
            # if (rotation >= 360-1 or rotation == 0):
            if rotation in range(360-rotation_threshold,360+rotation_threshold) or rotation in range(-rotation_threshold,rotation_threshold):
                bboxlogger.debug("no rotation adjustment required")
            # elif (rotation >= 270-1) or rotation in range(-180,-90):
            elif rotation in range(270-rotation_threshold,270+rotation_threshold) or rotation in range(-90-rotation_threshold,-90+rotation_threshold):
                applied_rotation=90
                # //Rotate 90 clockwise
                for line in page.lines:
                    line.boundingbox = BBoxUtils.rotateBoundingBox(page.width, page.height, line.boundingbox, applied_rotation)
                    line.calculateMedians()
                # Switch W/H accordingly
                page.width = page_height
                page.height = page_width
            # elif (rotation >= 180-1):
            elif rotation in range (180-rotation_threshold,180+rotation_threshold) or rotation in range(-180-rotation_threshold,-180+rotation_threshold):
                applied_rotation=180
                # // Rotate 180
                for line in page.lines:
                    line.boundingbox = BBoxUtils.rotateBoundingBox(page.width, page.height, line.boundingbox, applied_rotation)
                    line.calculateMedians()
            # elif (rotation >= 90-1):
            elif rotation in range(90-rotation_threshold,90+rotation_threshold) or rotation in range(-270-rotation_threshold,-270+rotation_threshold):
                applied_rotation=-90
                # //Rotate 90 counterclockwise
                for line in page.lines:
                    line.boundingbox = BBoxUtils.rotateBoundingBox(page.width, page.height, line.boundingbox, applied_rotation)
                    line.calculateMedians()
                # Switch W/H accordingly
                page.width = page_height
                page.height = page_width
            else:
                bboxlogger.warning("TODO rotation adjustment required ? ")

            # Invoke the page processing
            page = self.processOCRPageLayout(page, sortingAlgo, boxSeparator)
            newtext += page.text

            bboxlogger.debug("{0}|Processed Page {0} with {1} bbox lines.".format(str(page.id),len(page.lines)))

            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[1]
            else:
                # TODO #3
                # Default page separator
                newtext += os.linesep

            # Revert the rotation of the bounding boxes back to its original orientation
            if applied_rotation!=0:
                for line in page.lines:
                    line.boundingbox = BBoxUtils.rotateBoundingBox(page.width, page.height, line.boundingbox, int(-applied_rotation))
                    # recalculate medians for drawing the boxes correctly
                    line.calculateMedians()
                # Restore W/H 
                page.width = page_width
                page.height = page_height

        response.text = str(newtext)

        return response

    def __processLineBoundingBoxes(self, lines, alignment, unit, ppi): 
        boxref = 0
        Xthresholdratio = bboxconfig.get_Thresholds(unit,ppi)[alignment].Xthresholdratio
        Ythresholdratio = bboxconfig.get_Thresholds(unit,ppi)[alignment].Ythresholdratio
        if ( alignment == LeftAlignment):
            boxref = 0
            # //Adjustment for bullet list text. 
            for line in lines:
                if (line.text.startswith(". ")):
                    line.boundingbox[boxref].X = line.boundingbox[boxref].X + bboxconfig.get_ImageTextBoxingBulletListAdjustment(unit,ppi)
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: (o.boundingbox[boxref].X,o.boundingbox[boxref].Y))
        elif (alignment == RightAlignment):
            boxref = 1
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: o.boundingbox[boxref].X,reverse=True)
        elif (alignment == CenteredAlignment):
            boxref = 1
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: (o.xmedian,o.boundingbox[boxref].Y))
        else:
            bboxlogger.error("__processLineBoundingBoxes : Unknown text alignment")

        bboxlogger.debug("bounding boxes count {}".format(len(XSortedList)))

        regions = list(list())
        regions.append(list())
        regionx = 0.0
        regionidx = 0

        # //First Pass on the X Axis 
        for line in XSortedList:
            xcurrent = line.boundingbox[boxref].X

            if (alignment == CenteredAlignment):
                xcurrent = line.xmedian

            lowb=(regionx - (Xthresholdratio * bboxconfig.get_ImageTextBoxingXThreshold(unit,ppi)))
            highb=(regionx + (Xthresholdratio * bboxconfig.get_ImageTextBoxingXThreshold(unit,ppi)))
            if lowb>0.0:
                bboxlogger.debug("{6}|Region Id:{0} X:{1} LowX {2}<{3}<{4} HighX | Same Region? {5} ".format(str(regionidx),str(regionx),str(lowb),str(xcurrent),str(highb),str((xcurrent >= lowb and xcurrent <= highb)),alignment))

            if (regionx == 0.0):
                regions[regionidx].append(line)
                regionx = xcurrent
            # //can be improved by testing the upper X boundaries eventually
            elif (xcurrent >= lowb and xcurrent <= highb):
                regions[regionidx].append(line)
                if ( not alignment == CenteredAlignment ):
                    regionx = (xcurrent + regionx) / 2
            else:
                # // Add new region 
                regions.append(list())
                regionidx+=1
                regions[regionidx].append(line)
                regionx = xcurrent

        bboxlogger.debug("{1}|Found {0} regions".format(len(regions),alignment))

        # //Second Pass on the Y Axis 
        for lines in regions:
            lines.sort(key=lambda o : o.boundingbox[boxref].Y)
            # YSortedList = sorted(lines,key=lambda o : o.boundingbox[boxref].Y)
            # // the entries are now sorted ascending their Y axis
            regiony = 0.0
            bboxlogger.debug("{1}|Region with {0} lines.".format(str(len(lines)),alignment))

            for line in lines:
                # //Top Left Y
                ycurrent = line.boundingbox[boxref].Y
                # lowb=(regiony - (Ythresholdratio * bboxconfig.config[unit].ImageTextBoxingYThreshold))
                lowb=regiony-(regiony*0.05)
                highb=(regiony + (Ythresholdratio * bboxconfig.get_ImageTextBoxingYThreshold(unit,ppi)))
                bboxlogger.debug("{7}|Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.boundingbox),str(line.text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent <= highb)),str(regiony),alignment))

                if (regiony == 0.0):
                    prevline = line
                elif (ycurrent >= lowb and ycurrent < highb):
                    prevline.mergeLine(line,bboxconfig.lineMergeChar)
                else:
                    prevline = line

                # //Take the bottom left Y axis as new reference
                # regiony = line.boundingbox[3].Y
                regiony = line.boundingbox[2].Y
        return XSortedList

    def processOCRPageLayout(self, input_json, sortingAlgo=None, boxSeparator:str = None):
        """ processOCRPageLayout method
            Process a single page from an OCR input, returns the same page with enhanced boxing data & text.
        """
        if isinstance(input_json,str):
            page=BBOXPageLayout.from_azure(json.loads(input_json))
        elif isinstance(input_json,BBOXPageLayout):
            page=input_json

        inlines=[o for o in page.lines if o.merged == False]
        bboxlogger.debug("{1}|Input # lines {0}".format(len(inlines),str(page.id)))

        # Go through potential Text Alignment : Left, Right and Centered.
        for alignment in Alignments:
            bboxlogger.debug("{1}|Processing {0}".format(alignment,str(page.id)))
            page.lines = self.__processLineBoundingBoxes(page.lines,alignment,page.unit,page.ppi)

        # Another pass on LeftAlignment
        bboxlogger.debug("{1}-2|Processing {0}".format(alignment,str(page.id)))
        page.lines = self.__processLineBoundingBoxes(page.lines,LeftAlignment,page.unit,page.ppi)

        outlines=[o for o in page.lines if o.merged == False]
        bboxlogger.debug("{1}|Output {0} lines before sorting...".format(len(outlines),str(page.id)))
        #
        # Page lines Sorting
        # 
        if sortingAlgo is None:
            # Old Default Sorting Strategy 
            # Based on the W/H ratio we set the sorting strategy
            if page.Width/page.Height > 1.0:
                YXSortedOutput=False
            else: 
                YXSortedOutput=True

            if (YXSortedOutput):
                bboxlogger.debug("{0}|Sorting by YX".format(str(page.id)))
                sortedBlocks = sorted(outlines,key= lambda o: (o.boundingbox[0].Y, o.xmedian))
            else:
                bboxlogger.debug("{0}|Default sorting strategy".format(str(page.id)))
                sortedBlocks = sorted(outlines,key= lambda o: (o.boundingbox[0].X, o.ymedian))
        else:
            sortedBlocks = sortingAlgo(page.id,page.width,page.height,blocks=outlines,scale=page.ppi)

        bboxlogger.debug("{1}|Output {0} lines after sorting...".format(len(sortedBlocks),str(page.id)))

        # Output the actual from the sorted blocks
        newtext = ""
        for i,block in enumerate(sortedBlocks):
            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[0]
            else:
                newtext+=boxSeparator[0]

            # Normalized to Rectangles? 
            if bboxconfig.rectangleNormalization:
                BBoxUtils.makeRectangle(block)

            newtext+=block.text

            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[1]
                else:
                    if (i+1<len(sortedBlocks)):
                        # if block.getClusterId() != sortedBlocks[i+1].getClusterId() and (not sortedBlocks[i+1].text[0].isupper()):
                        if not (sortedBlocks[i+1].text[0].isupper() or sortedBlocks[i+1].text[0].isdigit()):
                            if block.text.strip().endswith("."):
                                newtext+=os.linesep
                            else:
                                newtext+=' '
                        # elif (not sortedBlocks[i+1].text[0].isupper()):
                        #     newtext+=' '
                        else:
                            newtext+=os.linesep
                    # Default separator
                    # if block.Text.strip().endswith("."):
                    # newtext+='\r\n'
                    # else:
                    #     newtext+=' '
            else:
                newtext+=boxSeparator[1]

        # // Setting the new Normalized Lines we created.
        page.lines = sortedBlocks
        # // Updating the Text after our processing.
        page.text = newtext

        return page
