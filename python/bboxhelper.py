# Import required modules.
import io
import json
import logging
import os
import random
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
import json
import math
import requests
import logging
import logging.config
from os import path
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
    def __init__(self,config={}):
        self.config=config
    @classmethod
    def from_json(cls, data):
        ocfg={}
        cfgs=data["config"]
        for key in cfgs:
            ocfg[key]=BBOXConfigEntry.from_json(cfgs[key])
        return cls(config=ocfg)
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
    def from_json(cls, data):
        return cls(**data)

class BBOXNormalizedLine():
    def __init__(self, BoundingBox: List[BBOXPoint], Text:str = None, merged:bool=False):
        self.BoundingBox = BoundingBox
        self.Text = Text
        self.merged = merged
        self.XMedian=(self.BoundingBox[0].X + self.BoundingBox[1].X)/2
    @classmethod
    def from_json(cls, data):
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
            points = list(map(BBOXPoint.from_json, array))
        return cls(BoundingBox=points,Text=data['text'])

class BBOXPageLayout():
    def __init__(self, Page:int = 0,ClockwiseOrientation:float = 0.0,Width:float = 0.0,Height:float = 0.0,Unit:str = "Pixel",Language:str="en",Text:str=None,Lines:List[BBOXNormalizedLine]=None):
        self.Page=Page
        self.ClockwiseOrientation=ClockwiseOrientation
        self.Width=Width
        self.Height=Height
        self.Unit=Unit
        self.Language=Language
        self.Text=Text
        self.Lines=Lines
    @classmethod
    def from_json(cls, data):
        lines = list(map(BBOXNormalizedLine.from_json, data["lines"]))
        return cls(Page=data["page"],ClockwiseOrientation=data["clockwiseOrientation"],Width=data["width"],Height=data["height"],Unit=data["unit"],Lines=lines)

class BBOXOCRResponse():
    def __init__(self,status:str = None,Text:str=None,recognitionResults:List[BBOXPageLayout]=None):
        self.status =status
        self.Text=Text
        self.recognitionResults=recognitionResults
    @classmethod
    def from_json(cls, data):
        pages = list(map(BBOXPageLayout.from_json, data["recognitionResults"]))
        return cls(status=data["status"],recognitionResults=pages)

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

    def __rotateBoundingBox(self,Width:float,Height:float,boundingBox:List[BBOXPoint],rotationv:int):
        newboundary = list()
        if (rotationv == 90):
            newboundary.append(boundingBox[0].inv())
            newboundary.append(boundingBox[1].inv())
            newboundary.append(boundingBox[2].inv())
            newboundary.append(boundingBox[3].inv())
            # //Adjusting the Y axis
            newboundary[0].Y = Width - boundingBox[0].X
            newboundary[1].Y = Width - boundingBox[1].X
            newboundary[2].Y = Width - boundingBox[2].X
            newboundary[3].Y = Width - boundingBox[3].X
        elif (rotationv == -90):
            newboundary.append(boundingBox[0].inv())
            newboundary.append(boundingBox[1].inv())
            newboundary.append(boundingBox[2].inv())
            newboundary.append(boundingBox[3].inv())
            # //Adjusting the X axis 
            newboundary[0].X = Height - boundingBox[1].Y
            newboundary[1].X = Height - boundingBox[0].Y
            newboundary[2].X = Height - boundingBox[3].Y
            newboundary[3].X = Height - boundingBox[2].Y
        elif (rotationv == 180):
            newboundary.append(boundingBox[1])
            newboundary.append(boundingBox[0])
            newboundary.append(boundingBox[3])
            newboundary.append(boundingBox[2])
            # //Adjust the Y axis 
            newboundary[0].Y = Height - boundingBox[1].Y
            newboundary[1].Y = Height - boundingBox[0].Y
            newboundary[2].Y = Height - boundingBox[3].Y
            newboundary[3].Y = Height - boundingBox[2].Y
        else:
            newboundary.append(boundingBox)
        return newboundary

    def processOCRResponse(self, input_json, YXSortedOutput:bool = False, boxSeparator:str = None):
        #load the input json into a response object
        response=BBOXOCRResponse.from_json(json.loads(input_json))
        newtext = ""
        # Rotate the BBox of each page based on its corresponding orientation
        for item in response.recognitionResults:
            self.logger.debug("Processing Page {}".format(str(item.Page)))
            rotation = round(item.ClockwiseOrientation,0)
            self.logger.debug("Orientation {}".format(str(rotation)))
            if (rotation >= 360-1 or rotation == 0):
                self.logger.debug("no rotation adjustment required")
            elif (rotation >= 270-1):
                # //Rotate 90 clockwise
                for x in item.Lines:
                    x.BoundingBox=self.__rotateBoundingBox(item.Width, item.Height, x.BoundingBox, -90)
            elif (rotation >= 180-1):
                # // Rotate 180
                for x in item.Lines:
                    x.BoundingBox = self.__rotateBoundingBox(item.Width, item.Height, x.BoundingBox, 180)
            elif (rotation >= 90-1):
                # //Rotate 90 counterclockwise
                for x in item.Lines:
                    x.BoundingBox = self.__rotateBoundingBox(item.Width, item.Height, x.BoundingBox, 90)
            else:
                self.logger.info("TODO rotation adjustment required ? ")

            newtext += self.processOCRPageLayout(item, YXSortedOutput, boxSeparator).Text
            newtext += os.linesep

        response.Text = str(newtext)
        return response

    def __minXminY(self,index,prevline,line): 
        prevline.BoundingBox[index].X = min(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = min(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    def __minXmaxY(self,index,prevline,line): 
        prevline.BoundingBox[index].X = min(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = max(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    def __maxXminY(self,index,prevline,line):
        prevline.BoundingBox[index].X = max(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = min(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    def __maxXmaxY(self,index,prevline,line): 
        prevline.BoundingBox[index].X = max(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = max(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]

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
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: o.BoundingBox[boxref].X)
        elif (alignment == RightAlignment):
            boxref = 1
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: o.BoundingBox[boxref].X,reverse=True)
        elif (alignment == CenteredAlignment):
            boxref = 1
            XSortedList = sorted([o for o in layout.Lines if o.merged == False],key= lambda o: o.XMedian)
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
                self.logger.debug("Region Id:{0} X:{1} LowX {2}<{3}<{4} HighX | Same Region? {5} ".format(str(regionidx),str(regionx),str(lowb),str(xcurrent),str(highb),str((xcurrent >= lowb and xcurrent <= highb))))

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

        self.logger.debug("Found {} regions".format(len(regions)))

        # //Second Pass on the Y Axis 
        for lines in regions:
            lines.sort(key=lambda o : o.BoundingBox[boxref].Y)
            # YSortedList = sorted(lines,key=lambda o : o.BoundingBox[boxref].Y)
            # // the entries are now sorted ascending their Y axis
            regiony = 0.0
            self.logger.debug("** Region with {0} lines.".format(str(len(lines))))

            for line in lines:
                # //Top Left Y
                ycurrent = line.BoundingBox[boxref].Y
                # lowb=(regiony - (Ythresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingYThreshold))
                lowb=regiony-(regiony*0.01)
                highb=(regiony + (Ythresholdratio * self.ocrconfig.config[layout.Unit].ImageTextBoxingYThreshold))
                self.logger.debug("Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.BoundingBox),str(line.Text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent <= highb)),str(line.XMedian)))

                if (regiony == 0.0):
                    prevline = line
                elif (ycurrent >= lowb and ycurrent <= highb):
                    line.merged = True
                    # //Merge current box with previous 
                    prevline.Text += " " + line.Text;
                    # //Merge the BoundingBox coordinates
                    prevline.BoundingBox[0] = self.__minXminY(0,prevline,line)
                    prevline.BoundingBox[1] = self.__maxXminY(1,prevline,line)
                    prevline.BoundingBox[2] = self.__maxXmaxY(2,prevline,line)
                    prevline.BoundingBox[3] = self.__minXmaxY(3,prevline,line)
                else:
                    prevline = line

                # //Take the bottom left Y axis as new reference
                regiony = line.BoundingBox[3].Y
        return XSortedList

    def processOCRPageLayout(self, input_json, YXSortedOutput:bool = False, boxSeparator:str = None):

        if isinstance(input_json,str):
            layout=BBOXPageLayout.from_json(json.loads(input_json))
        elif isinstance(input_json,BBOXPageLayout):
            layout=input_json

        inlines=[o for o in layout.Lines if o.merged == False]
        self.logger.debug("Input # lines {}".format(len(inlines)))

        for alignment in Alignments:
            self.logger.debug("Processing {}".format(alignment))
            layout.Lines = self.__processLineBoundingBoxes(layout,alignment)

        outlines=[o for o in layout.Lines if o.merged == False]
        self.logger.debug("Output # lines {}".format(len(outlines)))

        if (YXSortedOutput):
            self.logger.debug("Sorting by YX")
            # //Sort the new boxes by Y then X and output the text out of it
            XSortedList = sorted(outlines,key= lambda o: (o.BoundingBox[0].Y, o.XMedian))
            # XSortedList = sorted(outlines,key= lambda o: (o.BoundingBox[0].Y, o.BoundingBox[0].X))
        else:
            self.logger.debug("Sorting by XY")
            XSortedList = sorted(outlines,key= lambda o: (o.BoundingBox[0].X, o.BoundingBox[0].Y))

        # Output
        newtext = ""
        for line in XSortedList:
            newtext+=line.Text
            if (boxSeparator):
                newtext+=boxSeparator 
            else:
                newtext+=os.linesep

        # // Setting the new Normalized Lines we created.
        layout.Lines = XSortedList
        # // Updating the Text after our processing.
        layout.Text = newtext
        return layout
