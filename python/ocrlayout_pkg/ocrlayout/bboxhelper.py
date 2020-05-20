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
import requests

from .bboxutils import BBoxUtils, BBoxSort, BBOXConfig, BBOXAnnotate

# Constants
LeftAlignment="LeftAlignment"
RightAlignment="RightAlignment"
CenteredAlignment="CenteredAlignment"

Alignments = [LeftAlignment,RightAlignment,CenteredAlignment]

# Load deafult Configuration
json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/config.json")
with open(json_file_path) as json_file:
    bboxconfig=BBOXConfig.from_json(json.loads(json_file.read()))

# Load Logging default configuration 
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'config/logging.conf')
logging.config.fileConfig(log_file_path)
bboxlogger = logging.getLogger('bboxhelper')  # get a logger

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
    def __init__(self, Idx, BoundingBox: List[BBOXPoint], Text:str = None, merged:bool=False, avgheight=0.0, stdheight=0.0):
        self.startIdx=Idx
        self.endIdx=Idx
        self.BoundingBox = BoundingBox
        self.Text = ''
        self.merged = merged
        self.__calculateMedians()
        self.__appendText(Text)
        self.avgheight = avgheight
        self.stdheight = stdheight
        self.blockid=0.0
        self.listids=[]

    def __calculateMedians(self):
        self.XMedian=(min(self.BoundingBox[0].X,self.BoundingBox[3].X) + max(self.BoundingBox[1].X,self.BoundingBox[2].X))/2
        self.YMedian=(min(self.BoundingBox[0].Y,self.BoundingBox[3].Y) + max(self.BoundingBox[1].Y,self.BoundingBox[2].Y))/2
    
    def getBoxesAsArray(self):
        result=[]
        for box in self.BoundingBox:
            result.append([box.X,box.Y])
        return result

    def getBoxesAsRectangle(self):
        return (self.BoundingBox[0].X,self.BoundingBox[0].Y,(self.BoundingBox[2].X-self.BoundingBox[0].X),(self.BoundingBox[2].Y-self.BoundingBox[0].Y))

    def __appendText(self, Text):
        self.Text += Text
        if Text.endswith('.'):
            self.EndSentence=True
        else:
            self.EndSentence=False

    def appendLine(self,line):
        line.merged = True
        self.__appendText(" " + line.Text)
        self.BoundingBox[0] = BBoxUtils.minXminY(0,self,line)
        self.BoundingBox[1] = BBoxUtils.maxXminY(1,self,line)
        self.BoundingBox[2] = BBoxUtils.maxXmaxY(2,self,line)
        self.BoundingBox[3] = BBoxUtils.minXmaxY(3,self,line)
        self.__calculateMedians()
        self.endIdx=line.endIdx
        
    @classmethod
    def from_azure(cls, index, data):
        points = list()
        array=data["boundingBox"]
        if ( len(array) > 4 ):
            x = array[0]
            y = array[1]          
            points.append(BBOXPoint(x,y))
            x = array[2]
            y = array[3]
            points.append(BBOXPoint(x, y))
            x = array[4]
            y = array[5]
            points.append(BBOXPoint(x, y))
            x = array[6]
            y = array[7]
            points.append(BBOXPoint(x, y))
            # Make sure the X of the line is consistent to the first word of the same. 
            if len(data['words'])>0:
                points[0].X = data['words'][0]["boundingBox"][0]+1
                points[3].X = data['words'][0]["boundingBox"][6]+1
        else:
            points = list(map(BBOXPoint.from_azure, array))
            if len(data['words'])>0:
                points[0].X = data['words'][0]["boundingBox"][0].X+1
                points[3].X = data['words'][0]["boundingBox"][3].X+1
          
        wordheights=[]
        # Check Line in anomaly
        for wordbox in data['words']:
            wordheights.append(wordbox['boundingBox'][5]-wordbox['boundingBox'][1])
        # calculate the average 
        npheights = np.array(wordheights)
        avgheight = np.average(npheights)
        stdheight = np.std(npheights, dtype=np.float64)
        return cls(Idx=index,BoundingBox=points,Text=data['text'],stdheight=stdheight,avgheight=avgheight)

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
    def __init__(self, Id:int = 0,ClockwiseOrientation:float = 0.0,Width:float = 0.0,Height:float = 0.0,Unit:str = "pixel",Language:str="en",Text:str=None,Lines:List[BBOXNormalizedLine]=None):
        self.Id=Id
        self.ClockwiseOrientation=ClockwiseOrientation
        self.Width=Width
        self.Height=Height
        self.Unit=Unit
        self.Language=Language
        self.Text=Text
        self.Lines=Lines
    @classmethod
    def from_azure(cls, data):
        lines=[BBOXNormalizedLine.from_azure(i,line) for i,line in enumerate(data["lines"])] 
        return cls(Id=data["page"],ClockwiseOrientation=data["clockwiseOrientation"],Width=data["width"],Height=data["height"],Unit=data["unit"],Lines=lines)

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
        pages = list(map(BBOXPageLayout.from_azure, data["recognitionResults"]))
        return cls(status=data["status"],recognitionResults=pages)
    @classmethod
    def from_google(cls, document):
        pages = list(map(BBOXPageLayout.from_google,document.pages))
        return cls(status="success",original_text=document.text,recognitionResults=pages)

class BBoxHelper():

    # Support to use a custom configuration file.
    def __init__(self, customcfgfilepath=None, customlogfilepath=None, annotate=False, annotationconfig=None):
        if customcfgfilepath:
            with open(customcfgfilepath) as json_file:
                bboxconfig=BBOXConfig.from_json(json.loads(json_file.read()))
        if customlogfilepath:
            logging.config.fileConfig(customlogfilepath)
            bboxlogger = logging.getLogger('bboxhelper')
        self.annotate=annotate
        if annotationconfig:
            bboxconfig=BBOXAnnotate.from_json(json.loads(annotationconfig))

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
        """
        newtext = ""
        # Rotate the BBox of each page based on its corresponding orientation
        for item in response.pages:
            bboxlogger.debug("Processing Page {}".format(str(item.Id)))
            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[0]
            rotation = round(item.ClockwiseOrientation,0)
            bboxlogger.debug("Orientation {}".format(str(rotation)))
            # TODO Do the Math for clockwise orientation
            if (rotation >= 360-1 or rotation == 0):
                bboxlogger.debug("no rotation adjustment required")
            elif (rotation >= 270-1):
                # //Rotate 90 clockwise
                for x in item.Lines:
                    x.BoundingBox = BBoxUtils.rotateBoundingBox(item.Width, item.Height, x.BoundingBox, -90)
            elif (rotation >= 180-1):
                # // Rotate 180
                for x in item.Lines:
                    x.BoundingBox = BBoxUtils.rotateBoundingBox(item.Width, item.Height, x.BoundingBox, 180)
            elif (rotation >= 90-1):
                # //Rotate 90 counterclockwise
                for x in item.Lines:
                    x.BoundingBox = BBoxUtils.rotateBoundingBox(item.Width, item.Height, x.BoundingBox, 90)
            else:
                bboxlogger.info("TODO rotation adjustment required ? ")

            newtext += self.processOCRPageLayout(item, sortingAlgo, boxSeparator).Text

            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[1]
            else:
                # Default page separator
                newtext += '\r\n'

        response.Text = str(newtext)
        return response

    def __processLineBoundingBoxes(self, lines, alignment, unit): 
        boxref = 0
        Xthresholdratio = bboxconfig.config[unit].Thresholds[alignment].Xthresholdratio
        Ythresholdratio = bboxconfig.config[unit].Thresholds[alignment].Ythresholdratio
        if ( alignment == LeftAlignment):
            boxref = 0
            # //Adjustment for bullet list text. 
            for line in lines:
                if (line.Text.startswith(". ")):
                    line.BoundingBox[boxref].X = line.BoundingBox[boxref].X + bboxconfig.config[unit].ImageTextBoxingBulletListAdjustment
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: (o.BoundingBox[boxref].X,o.BoundingBox[boxref].Y))
        elif (alignment == RightAlignment):
            boxref = 1
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: o.BoundingBox[boxref].X,reverse=True)
        elif (alignment == CenteredAlignment):
            boxref = 1
            XSortedList = sorted([o for o in lines if o.merged == False],key= lambda o: (o.XMedian,o.BoundingBox[boxref].Y))
        else:
            bboxlogger.error("__processLineBoundingBoxes : Unknown text alignment")

        bboxlogger.debug("bounding boxes count {}".format(len(XSortedList)))

        regions = list(list())
        regions.append(list())
        regionx = 0.0
        regionidx = 0

        # //First Pass on the X Axis 
        for line in XSortedList:
            xcurrent = line.BoundingBox[boxref].X

            if (alignment == CenteredAlignment):
                xcurrent = line.XMedian

            lowb=(regionx - (Xthresholdratio * bboxconfig.config[unit].ImageTextBoxingXThreshold))
            highb=(regionx + (Xthresholdratio * bboxconfig.config[unit].ImageTextBoxingXThreshold))
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
            lines.sort(key=lambda o : o.BoundingBox[boxref].Y)
            # YSortedList = sorted(lines,key=lambda o : o.BoundingBox[boxref].Y)
            # // the entries are now sorted ascending their Y axis
            regiony = 0.0
            bboxlogger.debug("{1}|Region with {0} lines.".format(str(len(lines)),alignment))

            for line in lines:
                # //Top Left Y
                ycurrent = line.BoundingBox[boxref].Y
                # lowb=(regiony - (Ythresholdratio * bboxconfig.config[unit].ImageTextBoxingYThreshold))
                lowb=regiony-(regiony*0.1)
                highb=(regiony + (Ythresholdratio * bboxconfig.config[unit].ImageTextBoxingYThreshold))
                bboxlogger.debug("{7}|Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.BoundingBox),str(line.Text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent < highb)),str(regiony),alignment))

                if (regiony == 0.0):
                    prevline = line
                elif (ycurrent >= lowb and ycurrent < highb):
                    prevline.appendLine(line)
                else:
                    prevline = line

                # //Take the bottom left Y axis as new reference
                # regiony = line.BoundingBox[3].Y
                regiony = line.BoundingBox[2].Y
        return XSortedList

    def processOCRPageLayout(self, input_json, sortingAlgo=None, boxSeparator:str = None):
        """ processOCRPageLayout method
            Process a single page from an OCR input, returns the same page with enhanced boxing data & text.
        """
        if isinstance(input_json,str):
            page=BBOXPageLayout.from_azure(json.loads(input_json))
        elif isinstance(input_json,BBOXPageLayout):
            page=input_json

        inlines=[o for o in page.Lines if o.merged == False]
        bboxlogger.debug("{1}|Input # lines {0}".format(len(inlines),str(page.Id)))

        # Go through potential Text Alignment : Left, Right and Centered.
        for alignment in Alignments:
            bboxlogger.debug("{1}|Processing {0}".format(alignment,str(page.Id)))
            page.Lines = self.__processLineBoundingBoxes(page.Lines,alignment,page.Unit)

        outlines=[o for o in page.Lines if o.merged == False]
        bboxlogger.debug("{1}|Output # lines {0}".format(len(outlines),str(page.Id)))

        if sortingAlgo is None:
            # Default Sorting Strategy 
            # Based on the W/H ratio we set the sorting strategy
            if page.Width/page.Height > 1.0:
                YXSortedOutput=False
            else: 
                YXSortedOutput=True

            if (YXSortedOutput):
                bboxlogger.debug("{0}|Sorting by YX".format(str(page.Id)))
                sortedBlocks = sorted(outlines,key= lambda o: (o.BoundingBox[0].Y, o.XMedian))
            else:
                bboxlogger.debug("{0}|Default sorting strategy".format(str(page.Id)))
                sortedBlocks = sorted(outlines,key= lambda o: (o.BoundingBox[0].X, o.YMedian))
        else:
            sortedBlocks = sortingAlgo(page.Id,page.Width,page.Height,blocks=outlines)

        # Output the actual from the sorted blocks
        newtext = ""
        for i,block in enumerate(sortedBlocks):
            # block.blockid = i
            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[0]
            else:
                newtext+=boxSeparator[0]
            # Normalized to Rectangles? 
            if bboxconfig.rectangleNormalization:
                BBoxUtils.makeRectangle(block)
            newtext+=block.Text
            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[1]
                else:
                    # newtext+=os.linesep
                    newtext+='\r\n'
            else:
                newtext+=boxSeparator[1]

        # // Setting the new Normalized Lines we created.
        page.Lines = sortedBlocks
        # // Updating the Text after our processing.
        page.Text = newtext
        return page
