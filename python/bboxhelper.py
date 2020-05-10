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
from pathlib import Path
from typing import List

import requests

from bboxutils import BBoxUtils

#
# Bounding Boxes Config Classes
#
class BBOXConfigEntryThreshold():
    def __init__(self,Xthresholdratio,Ythresholdratio):
        self.Xthresholdratio=Xthresholdratio
        self.Ythresholdratio=Ythresholdratio
    @classmethod
    def from_json(cls, data):
        return cls(**data)

class BBOXConfigEntry():
    def __init__(self,ImageTextBoxingXThreshold,ImageTextBoxingYThreshold,ImageTextBoxingBulletListAdjustment,Thresholds={}):
        self.ImageTextBoxingXThreshold=ImageTextBoxingXThreshold
        self.ImageTextBoxingYThreshold=ImageTextBoxingYThreshold
        self.ImageTextBoxingBulletListAdjustment=ImageTextBoxingBulletListAdjustment
        self.Thresholds=Thresholds
    @classmethod
    def from_json(cls, data):
        obj={}
        Thresholds=data["Thresholds"]
        for key in Thresholds:
            obj[key]=BBOXConfigEntryThreshold.from_json(Thresholds[key])
        return cls(data["ImageTextBoxingXThreshold"],data["ImageTextBoxingYThreshold"],data["ImageTextBoxingBulletListAdjustment"],obj)

class BBOXConfig():
    def __init__(self,rectangleNormalization,config={}):
        self.config=config
        self.rectangleNormalization=rectangleNormalization
    @classmethod
    def from_json(cls, data):
        ocfg={}
        cfgs=data["config"]
        for key in cfgs:
            ocfg[key]=BBOXConfigEntry.from_json(cfgs[key])
        return cls(data["rectangleNormalization"],config=ocfg)
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
    def __init__(self, BoundingBox: List[BBOXPoint], Text:str = None, merged:bool=False):
        self.BoundingBox = BoundingBox
        self.Text = ''
        self.merged = merged
        self.XMedian=(min(self.BoundingBox[0].X,self.BoundingBox[3].X) + max(self.BoundingBox[1].X,self.BoundingBox[2].X))/2
        self.YMedian=(min(self.BoundingBox[0].Y,self.BoundingBox[3].Y) + max(self.BoundingBox[1].Y,self.BoundingBox[2].Y))/2
        self.__appendText(Text)

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
        
    @classmethod
    def from_azure(cls, data):
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
        else:
            points = list(map(BBOXPoint.from_azure, array))
        return cls(BoundingBox=points,Text=data['text'])
    @classmethod
    def from_google(cls, block):
        points = list()
        for bb in block.bounding_box.vertices:
            points.append(BBOXPoint(bb.x,bb.y))
        # Text of the block
        block_text=""
        for paragraph in block.paragraphs:
            for word in paragraph.words:
                for symbol in word.symbols:
                    block_text+=symbol.text
                    if symbol.property.detected_break:
                        if symbol.property.detected_break.type in [1,2,3]:
                            block_text+=" "
                        elif symbol.property.detected_break.type==5:
                            block_text+='\r\n'
                            # EOL_SURE_SPACE
        return cls(BoundingBox=points,Text=block_text)

class BBOXPageLayout():
    def __init__(self, Page:int = 0,ClockwiseOrientation:float = 0.0,Width:float = 0.0,Height:float = 0.0,Unit:str = "pixel",Language:str="en",Text:str=None,Lines:List[BBOXNormalizedLine]=None):
        self.Page=Page
        self.ClockwiseOrientation=ClockwiseOrientation
        self.Width=Width
        self.Height=Height
        self.Unit=Unit
        self.Language=Language
        self.Text=Text
        self.Lines=Lines
    @classmethod
    def from_azure(cls, data):
        lines = list(map(BBOXNormalizedLine.from_azure, data["lines"]))
        return cls(Page=data["page"],ClockwiseOrientation=data["clockwiseOrientation"],Width=data["width"],Height=data["height"],Unit=data["unit"],Lines=lines)
    @classmethod
    def from_google(cls, page):
        lines = list(map(BBOXNormalizedLine.from_google, page.blocks))
        # return cls(Page=1,Width=page.width,Height=page.height,Language=page.property.detectedLanguages[0].languageCode,Lines=lines)
        return cls(Page=1,Width=page.width,Height=page.height,Lines=lines)

class BBOXOCRResponse():
    def __init__(self,status:str = None,Text:str=None,original_text:str=None,recognitionResults:List[BBOXPageLayout]=None):
        self.status =status
        self.original_text=original_text
        self.Text=Text
        self.recognitionResults=recognitionResults
    @classmethod
    def from_azure(cls, data):
        pages = list(map(BBOXPageLayout.from_azure, data["recognitionResults"]))
        return cls(status=data["status"],recognitionResults=pages)
    @classmethod
    def from_google(cls, document):
        pages = list(map(BBOXPageLayout.from_google,document.pages))
        return cls(status="success",original_text=document.text,recognitionResults=pages)

# Constants
LeftAlignment="LeftAlignment"
RightAlignment="RightAlignment"
CenteredAlignment="CenteredAlignment"

Alignments = [LeftAlignment,RightAlignment,CenteredAlignment]

class BBoxHelper():

    def __init__(self):
        # Load configuration
        json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
        with open(json_file_path) as json_file:
            self.ocrconfig=BBOXConfig.from_json(json.loads(json_file.read()))
        log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
        logging.config.fileConfig(log_file_path)
        self.logger = logging.getLogger('bboxhelper')  # get a logger

    def processOCRResponse(self, input_json, YXSortedOutput:bool = False, boxSeparator:str = None):
        #load the input json into a response object
        if isinstance(input_json,str):
            response=BBOXOCRResponse.from_azure(json.loads(input_json))
        elif isinstance(input_json,BBOXOCRResponse):
            response=input_json

        newtext = ""
        # Rotate the BBox of each page based on its corresponding orientation
        for item in response.recognitionResults:
            self.logger.debug("Processing Page {}".format(str(item.Page)))
            rotation = round(item.ClockwiseOrientation,0)
            self.logger.debug("Orientation {}".format(str(rotation)))
            # TODO Do the Math for clockwise orientation
            if (rotation >= 360-1 or rotation == 0):
                self.logger.debug("no rotation adjustment required")
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
                self.logger.info("TODO rotation adjustment required ? ")

            newtext += self.processOCRPageLayout(item, YXSortedOutput, boxSeparator).Text
            # TODO add support for page separator
            # newtext += '\r\n'

        response.Text = str(newtext)
        return response

    def __processLineBoundingBoxes(self, layout:BBOXPageLayout, alignment:str): 
        boxref = 0
        Xthresholdratio = self.ocrconfig.config[layout.Unit].Thresholds[alignment].Xthresholdratio
        Ythresholdratio = self.ocrconfig.config[layout.Unit].Thresholds[alignment].Ythresholdratio
        if ( alignment == LeftAlignment):
            boxref = 0
            # //Adjustment for bullet list text. 
            for line in layout.Lines:
                if (line.Text.startswith(". ")):
                    line.BoundingBox[boxref].X = line.BoundingBox[boxref].X + self.ocrconfig.config[layout.Unit].ImageTextBoxingBulletListAdjustment
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: (o.BoundingBox[boxref].X,o.BoundingBox[boxref].Y))
        elif (alignment == RightAlignment):
            boxref = 1
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: o.BoundingBox[boxref].X,reverse=True)
        elif (alignment == CenteredAlignment):
            boxref = 1
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: (o.XMedian,o.BoundingBox[boxref].Y))
        else:
            self.logger.error("__processLineBoundingBoxes : Unknown text alignment")

        self.logger.debug("bounding boxes count {}".format(len(XSortedList)))

        regions = list(list())
        regions.append(list())
        regionx = 0.0
        regionidx = 0

        # //First Pass on the X Axis 
        for line in XSortedList:
            xcurrent = line.BoundingBox[boxref].X

            if (alignment == CenteredAlignment):
                xcurrent = line.XMedian

            lowb=(regionx - (Xthresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingXThreshold))
            highb=(regionx + (Xthresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingXThreshold))
            if lowb>0.0:
                self.logger.debug("{6}|Region Id:{0} X:{1} LowX {2}<{3}<{4} HighX | Same Region? {5} ".format(str(regionidx),str(regionx),str(lowb),str(xcurrent),str(highb),str((xcurrent >= lowb and xcurrent <= highb)),alignment))

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

        self.logger.debug("{1}|Found {0} regions".format(len(regions),alignment))

        # //Second Pass on the Y Axis 
        for lines in regions:
            lines.sort(key=lambda o : o.BoundingBox[boxref].Y)
            # YSortedList = sorted(lines,key=lambda o : o.BoundingBox[boxref].Y)
            # // the entries are now sorted ascending their Y axis
            regiony = 0.0
            self.logger.debug("{1}|Region with {0} lines.".format(str(len(lines)),alignment))

            for line in lines:
                # //Top Left Y
                ycurrent = line.BoundingBox[boxref].Y
                # lowb=(regiony - (Ythresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingYThreshold))
                lowb=regiony-(regiony*0.01)
                highb=(regiony + (Ythresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingYThreshold))
                self.logger.debug("{7}|Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.BoundingBox),str(line.Text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent <= highb)),str(line.XMedian),alignment))

                if (regiony == 0.0):
                    prevline = line
                elif (ycurrent >= lowb and ycurrent <= highb):
                    prevline.appendLine(line)
                else:
                    prevline = line

                # //Take the bottom left Y axis as new reference
                regiony = line.BoundingBox[3].Y
        return XSortedList

    def processOCRPageLayout(self, input_json, YXSortedOutput:bool = False, boxSeparator:str = None):
        if isinstance(input_json,str):
            layout=BBOXPageLayout.from_azure(json.loads(input_json))
        elif isinstance(input_json,BBOXPageLayout):
            layout=input_json

        inlines=[o for o in layout.Lines if o.merged == False]
        self.logger.debug("{1}|Input # lines {0}".format(len(inlines),str(layout.Page)))

        for alignment in Alignments:
            self.logger.debug("{1}|Processing {0}".format(alignment,str(layout.Page)))
            layout.Lines = self.__processLineBoundingBoxes(layout,alignment)

        outlines=[o for o in layout.Lines if o.merged == False]
        self.logger.debug("{1}|Output # lines {0}".format(len(outlines),str(layout.Page)))

        # Sorting Strategy 
        # Based on the W/H ratio we set the sorting strategy
        # if layout.Width/layout.Height > 1.0:
        #     YXSortedOutput=False
        # else: 
        #     YXSortedOutput=True

        if (YXSortedOutput):
            self.logger.debug("{0}|Sorting by YX".format(str(layout.Page)))
            # //Sort the new boxes by Y then X and output the text out of it
            XSortedList = sorted(outlines,key= lambda o: (o.YMedian, o.XMedian))
            # XSortedList = sorted(outlines,key= lambda o: (o.BoundingBox[0].Y, o.BoundingBox[0].X))
        else:
            self.logger.debug("{0}|Sorting by XY".format(str(layout.Page)))
            XSortedList = sorted(outlines,key= lambda o: (o.XMedian, o.YMedian))

        # Output
        newtext = ""
        for line in XSortedList:
            # Normalized to Rectangles? 
            if self.ocrconfig.rectangleNormalization:
                BBoxUtils.makeRectangle(line)
            newtext+=line.Text
            if (boxSeparator):
                newtext+=boxSeparator 
            else:
                # newtext+=os.linesep
                newtext+='\r\n'

        # // Setting the new Normalized Lines we created.
        layout.Lines = XSortedList
        # // Updating the Text after our processing.
        layout.Text = newtext
        return layout
