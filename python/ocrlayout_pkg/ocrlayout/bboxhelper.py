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
    def __init__(self, X: float = 0.0, Y: float = 0.0):
        self.X = X
        self.Y = Y
    # Reverse a BBOX Point X,Y coordinates
    def inv(self):
        return BBOXPoint(self.Y,self.X)   
    def __repr__(self):
        return "[{0},{1}]".format(str(self.X),str(self.Y))
    @classmethod
    def from_azure(cls, data):
        return cls(**data)

class BBOXNormalizedLine():
    def __init__(self, Idx, BoundingBox: List[BBOXPoint], Text:str = None, merged:bool=False, avg_height=0.0, std_height=0.0):
        self.start_idx=Idx
        self.end_idx=Idx
        self.boundingbox = BoundingBox
        self.text = ''
        self.merged = merged
        self.calculateMedians()
        self.__appendText(Text)
        self.avg_height = avg_height
        self.std_height = std_height
        self.rank=0.0
        self.listids=[]

    def calculateMedians(self):
        self.xmedian=(min(self.boundingbox[0].X,self.boundingbox[3].X) + max(self.boundingbox[1].X,self.boundingbox[2].X))/2
        self.ymedian=(min(self.boundingbox[0].Y,self.boundingbox[3].Y) + max(self.boundingbox[1].Y,self.boundingbox[2].Y))/2

    def getClusterId(self):
        return self.listids[0]

    def getBoxesAsArray(self,scale=1):
        result=[]
        for box in self.boundingbox:
            result.append([box.X*scale,box.Y*scale])
        return result

    def getBoxesAsRectangle(self,scale=1):
        return (self.boundingbox[0].X*scale,self.boundingbox[0].Y*scale,(self.boundingbox[2].X-self.boundingbox[0].X)*scale,(self.boundingbox[2].Y-self.boundingbox[0].Y)*scale)

    def __appendText(self, Text):
        self.text += Text
        if Text.endswith('.'):
            self.end_sentence=True
        else:
            self.end_sentence=False

    def appendLine(self,line):
        line.merged = True
        self.__appendText(" " + line.text)
        self.boundingbox[0] = BBoxUtils.minXminY(0,self,line)
        self.boundingbox[1] = BBoxUtils.maxXminY(1,self,line)
        self.boundingbox[2] = BBoxUtils.maxXmaxY(2,self,line)
        self.boundingbox[3] = BBoxUtils.minXmaxY(3,self,line)
        self.calculateMedians()
        self.end_idx=line.end_idx
        
    @classmethod
    def from_azure(cls, index, data, ppi):
        points = list()
        array=data["boundingBox"]
        if ( len(array) > 4 ):
            x = array[0]
            y = array[1]          
            points.append(BBOXPoint(x*ppi,y*ppi))
            x = array[2]
            y = array[3]
            points.append(BBOXPoint(x*ppi, y*ppi))
            x = array[4]
            y = array[5]
            points.append(BBOXPoint(x*ppi, y*ppi))
            x = array[6]
            y = array[7]
            points.append(BBOXPoint(x*ppi, y*ppi))

            # Make sure the X of the line is consistent to the first word of the same. 
            if len(data['words'])>0:
                points[0].X = data['words'][0]["boundingBox"][0]+1
                points[3].X = data['words'][0]["boundingBox"][6]+1
        else:
            points = list(map(BBOXPoint.from_azure, [ppi*x for x in array]))
            if len(data['words'])>0:
                points[0].X = data['words'][0]["boundingBox"][0].X+1
                points[3].X = data['words'][0]["boundingBox"][3].X+1
          
        wordheights=[]
        # # Check Line in anomaly
        for wordbox in data['words']:
            wordheights.append(wordbox['boundingBox'][5]-wordbox['boundingBox'][1])

        # calculate the average
        npheights = np.array(wordheights)
        avg_height = np.average(npheights)
        std_height = np.std(npheights, dtype=np.float64)
        return cls(Idx=index,BoundingBox=points,Text=data['text'],std_height=std_height,avg_height=avg_height)

    @classmethod
    def from_google(cls, line_counter, line_text, line_boxes):
        points = list()
        for bb in range(4):
            points.append(BBOXPoint(0,0))
        # 
        points[0].X = line_boxes[0][0].x 
        points[0].Y = line_boxes[0][0].y 
        points[3].X = line_boxes[0][3].x 
        points[3].Y = line_boxes[0][3].y

        points[1].X = line_boxes[-1][1].x 
        points[1].Y = line_boxes[-1][1].y 
        points[2].X = line_boxes[-1][2].x 
        points[2].Y = line_boxes[-1][2].y 

        return BBOXNormalizedLine(Idx=line_counter,BoundingBox=points,Text=line_text)

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
    def from_azure(cls, data):
        # TODO #1
        if data["unit"]=="inch":
            # Azure OCR response doesn't provide the ppi per page
            # so we need to determine it for normalizing the processing of lines
            # ppi=BBoxUtils.determine_ppi(data["width"],data["height"])
            
            # decimal precision on Azure is set to 4, so we can set a 10000 to normalize the box and 
            # not convert to pixel
            ppi=10000
        else:
            ppi=1

        lines=[BBOXNormalizedLine.from_azure(i,line, 1) for i,line in enumerate(data["lines"])] 
        # >=0.6.0
        if "angle" in data:
            angle = data["angle"]
        # <= 0.5.0
        elif "clockwiseorientation" in data:
            angle = data["clockwiseorientation"]
          
        return cls(Id=data["page"],clockwiseorientation=angle,Width=data["width"],Height=data["height"],Unit=data["unit"],Lines=lines,ppi=ppi)

    @classmethod
    def from_google(cls, page):
        lines=[]
        line_counter=0
        line_text =""
        line_boxes=[]
        bboxlogger.debug("Google|Page shape (Height,Width) ({0},{1})".format(page.height,page.width))
        # Create the concept of lines for Google ocr response. 
        for idb, block in enumerate(page.blocks):
            for paragraph in block.paragraphs:
                pagearray = np.zeros((page.height,page.width))
                # parray=page[paragraph.bounding_box.vertices[0].y:paragraph.bounding_box.vertices[2].y,paragraph.bounding_box.vertices[0].x:paragraph.bounding_box.vertices[2].x]
                bboxlogger.debug("Google|Paragraph {0} of {1} words".format(str(idb),str(len(paragraph.words))))
                for widx, word in enumerate(paragraph.words):
                    # Put the word presence in the paragraph matrix 
                    low_y=word.bounding_box.vertices[0].y-1
                    high_y=word.bounding_box.vertices[2].y
                    low_x=word.bounding_box.vertices[0].x-1
                    high_x=word.bounding_box.vertices[2].x
                    # the Min,Max allows us to handle vertical words. 
                    pagearray[min(low_y,high_y):max(low_y,high_y),min(low_x,high_x):max(low_x,high_x)]=widx+1

                columns=BBoxSort.findClusters(pagearray,axis=0,gapthreshhold=bboxconfig.config["pixel"].GoogleLineBreakThresholdInPixel)

                # Assign the first cluster as current
                currentTextColumn = columns[0]

                for widx, word in enumerate(paragraph.words):
                    if len(columns)==1:
                        foundTextColumn = columns[0]
                    else:                       
                        # Find the word cluster
                        for cidx,column in enumerate(columns):
                            if word.bounding_box.vertices[0].x >= column[0] and word.bounding_box.vertices[0].x <= column[1]:
                                foundTextColumn = column
                                bboxlogger.debug("Google|Word Idx:{0} X:{1} in Cluster {2}".format(widx,word.bounding_box.vertices[0].x,column))

                    # Line break on text columns change.
                    if len(line_boxes)>0:
                        if foundTextColumn != currentTextColumn:
                            # xdiff=(word.bounding_box.vertices[0].x - line_boxes[-1][1].x)
                            # if xdiff > bboxconfig.config["pixel"].GoogleLineBreakThresholdInPixel:
                                bboxlogger.debug("Google|Detected Cluster Break current {0} found {1} | {2} {3}".format(currentTextColumn,foundTextColumn,str(line_counter),line_text))
                                # Line break
                                line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes)
                                lines.append(line)
                                line_text=""
                                line_counter+=1
                                line_boxes.clear()
                    currentTextColumn=foundTextColumn

                    line_boxes.append(word.bounding_box.vertices)
                    for symbol in word.symbols:
                        line_text+=symbol.text
                        if symbol.property.detected_break:
                            if symbol.property.detected_break.type in [1,2]:
                                line_text+=" "
                            elif symbol.property.detected_break.type in [3,5]:
                                bboxlogger.debug("Google|Detected Line Break {0}| {1} {2}".format(str(symbol.property.detected_break.type),str(line_counter),line_text))
                                # Line Break
                                line=BBOXNormalizedLine.from_google(line_counter,line_text,line_boxes)
                                lines.append(line)
                                line_text=""
                                line_counter+=1
                                line_boxes.clear()

        return cls(Id=1,Width=page.width,Height=page.height,Lines=lines)

class BBOXOCRResponse():
    def __init__(self,status:str = None,Text:str=None,original_text:str=None,recognitionResults:List[BBOXPageLayout]=None):
        self.status =status
        self.original_text=original_text
        self.text=Text
        self.pages=recognitionResults

    @classmethod
    def from_azure(cls, data):
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
        return cls(status=data["status"],recognitionResults=pages)
    @classmethod
    def from_google(cls, document):
        pages = list(map(BBOXPageLayout.from_google,document.pages))
        return cls(status="success",original_text=document.text,recognitionResults=pages)

class BBoxHelper():

    # Support to use a custom configuration file.
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

    def processGoogleOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None):
        """ processGoogleOCRResponse method
            Process an OCR Response input from Google and returns a new BBox format OCR response.
        """
        #Create an BBOXOCRResponse object from Google input
        response=BBOXOCRResponse.from_google(input)

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
                # Default page separator
                newtext += '\r\n'

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
                lowb=regiony-(regiony*0.1)
                highb=(regiony + (Ythresholdratio * bboxconfig.get_ImageTextBoxingYThreshold(unit,ppi)))
                bboxlogger.debug("{7}|Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.boundingbox),str(line.text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent < highb)),str(regiony),alignment))

                if (regiony == 0.0):
                    prevline = line
                elif (ycurrent >= lowb and ycurrent < highb):
                    prevline.appendLine(line)
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
                        if not sortedBlocks[i+1].text[0].isupper():
                            if block.text.strip().endswith("."):
                                newtext+='\r\n'
                            else:
                                newtext+=' '
                        # elif (not sortedBlocks[i+1].text[0].isupper()):
                        #     newtext+=' '
                        else:
                            newtext+='\r\n'
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
