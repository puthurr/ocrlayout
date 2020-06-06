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

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import bboxlog

bboxlogger = bboxlog.get_logger()

#
# Annotation Class
#
class BBOXAnnotate():
    def __init__(self,pageTag:None,blockTag:None,paragraphTag:None,sentenceTag:None):
        self.pageTag = pageTag
        self.blockTag = blockTag
        self.paragraphTag = paragraphTag
        self.sentenceTag = sentenceTag
    @classmethod
    def from_json(cls, data):
        return cls(pageTag=data["pageTag"],blockTag=data["blockTag"],paragraphTag=data["paragraphTag"],sentenceTag=data["sentenceTag"])

#
# Bounding Boxes Utils class
#
class BBoxUtils():

    @classmethod
    def rotateBoundingBox(cls,Width:float,Height:float,boundingBox,rotationv:int):
        """Rotation of the BoundingBox utility function"""
        newboundary = list()
        if (rotationv == 90):
            newboundary.append(boundingBox[0].inv())
            newboundary.append(boundingBox[1].inv())
            newboundary.append(boundingBox[2].inv())
            newboundary.append(boundingBox[3].inv())
            # Adjusting the X axis to preserve the original height order
            newboundary[0].X = Height - newboundary[0].X
            newboundary[1].X = Height - newboundary[1].X
            newboundary[2].X = Height - newboundary[2].X
            newboundary[3].X = Height - newboundary[3].X
        elif (rotationv == -90):
            newboundary.append(boundingBox[0].inv())
            newboundary.append(boundingBox[1].inv())
            newboundary.append(boundingBox[2].inv())
            newboundary.append(boundingBox[3].inv())
            # Adjusting the Y axis to preserve the original width order
            newboundary[0].Y = Width - newboundary[0].Y
            newboundary[1].Y = Width - newboundary[1].Y
            newboundary[2].Y = Width - newboundary[2].Y
            newboundary[3].Y = Width - newboundary[3].Y
        elif (rotationv == 180):
            newboundary.append(boundingBox[1])
            newboundary.append(boundingBox[0])
            newboundary.append(boundingBox[3])
            newboundary.append(boundingBox[2])
            # //Adjust the Y axis 
            newboundary[0].Y = Height - newboundary[0].Y
            newboundary[1].Y = Height - newboundary[1].Y
            newboundary[2].Y = Height - newboundary[2].Y
            newboundary[3].Y = Height - newboundary[3].Y
        elif (rotationv == -180):
            newboundary.append(boundingBox[2])
            newboundary.append(boundingBox[3])
            newboundary.append(boundingBox[0])
            newboundary.append(boundingBox[1])
            # # //Adjust the Y axis 
            newboundary[0].Y = Height - newboundary[0].Y
            newboundary[1].Y = Height - newboundary[1].Y
            newboundary[2].Y = Height - newboundary[2].Y
            newboundary[3].Y = Height - newboundary[3].Y
        else:
            newboundary.append(boundingBox)
        return newboundary

    @classmethod
    def rotateLineBoundingBox(cls,boundingbox, angle):
        newboundary = list()
        rad=math.radians(angle)
        for box in boundingbox:
            # original formula
            # box.X = box.X*math.cos(rad) - box.Y*math.sin(rad)
            # box.Y = box.X*math.sin(rad) + box.Y*math.cos(rad)
            box.X = box.X*math.cos(rad) + box.Y*math.sin(rad)
            box.Y = box.X*math.sin(rad) - box.Y*math.cos(rad)
            newboundary.append(box)
        return newboundary

    @classmethod
    def minXminY(cls,index,prevline,line): 
        prevline.boundingbox[index].X = min(prevline.boundingbox[index].X, line.boundingbox[index].X)
        prevline.boundingbox[index].Y = min(prevline.boundingbox[index].Y, line.boundingbox[index].Y)
        return prevline.boundingbox[index]
    @classmethod
    def minXmaxY(cls,index,prevline,line): 
        prevline.boundingbox[index].X = min(prevline.boundingbox[index].X, line.boundingbox[index].X)
        prevline.boundingbox[index].Y = max(prevline.boundingbox[index].Y, line.boundingbox[index].Y)
        return prevline.boundingbox[index]
    @classmethod
    def maxXminY(cls,index,prevline,line):
        prevline.boundingbox[index].X = max(prevline.boundingbox[index].X, line.boundingbox[index].X)
        prevline.boundingbox[index].Y = min(prevline.boundingbox[index].Y, line.boundingbox[index].Y)
        return prevline.boundingbox[index]
    @classmethod
    def maxXmaxY(cls,index,prevline,line): 
        prevline.boundingbox[index].X = max(prevline.boundingbox[index].X, line.boundingbox[index].X)
        prevline.boundingbox[index].Y = max(prevline.boundingbox[index].Y, line.boundingbox[index].Y)
        return prevline.boundingbox[index]

    @classmethod
    def makeRectangle(cls,line): 
        # X 
        # 
        line.boundingbox[0].X=line.boundingbox[3].X = min(line.boundingbox[0].X,line.boundingbox[3].X)
        line.boundingbox[1].X=line.boundingbox[2].X = max(line.boundingbox[1].X,line.boundingbox[2].X)
        # Y
        line.boundingbox[0].Y=line.boundingbox[1].Y = min(line.boundingbox[0].Y,line.boundingbox[1].Y)
        line.boundingbox[2].Y=line.boundingbox[3].Y = max(line.boundingbox[2].Y,line.boundingbox[3].Y)

    @classmethod
    def draw_boxes_on_page(cls,image,blocks,color,scale=1,padding=0):
        """Draw the blocks of text in an image using OpenCV."""
        for block in blocks:
            pts = np.array(block.getBoxesAsArray(scale), np.int32)
            pts = pts.reshape((-1,1,2))
            cv2.polylines(image,[pts],True,(255,255,255))
        return image

    # @classmethod
    # def determine_ppi(cls,width,height):
    #     ppi=72
    #     while True:
    #         ppi+=1
    #         pwidth=width*ppi
    #         pheight=height*ppi
    #         if (pwidth.is_integer() and pheight.is_integer()):
    #             return ppi

#
# Bounding Boxes Sorting class
#
class BBoxSort():

    # Define the multiple Sorting strategy 
    @classmethod
    def sortXY(cls,pageId,width,height,blocks):
        return sorted(blocks,key= lambda o: (o.boundingbox[0].X, o.ymedian))

    @classmethod
    def sortYX(cls,pageId,width,height,blocks):
        return sorted(blocks,key= lambda o: (o.boundingbox[0].Y, o.xmedian))

    @classmethod
    def sortOCRBlocks(cls,pageId,width,height,blocks):
        boxref = 0
        # xsortedlist = sorted([o for o in blocks if o.merged == False],key= lambda o: (o.boundingbox[boxref].X,o.boundingbox[boxref].Y))
        xsortedlist = sorted([o for o in blocks if o.merged == False],key= lambda o: (o.xmedian,o.boundingbox[boxref].Y))
        blockcounter=0.0
        for block in xsortedlist:
            blockcounter+=1
            block.rank+=blockcounter
            block.listids.append(blockcounter)

        ysortedlist = sorted([o for o in xsortedlist if o.merged == False],key= lambda o: (o.boundingbox[boxref].Y,o.boundingbox[boxref].X))
        blockcounter=0.0
        for block in ysortedlist:
            blockcounter+=2
            block.rank+=blockcounter
            block.listids.append(blockcounter)

        return sorted([o for o in ysortedlist if o.merged == False],key= lambda o: (o.rank,o.boundingbox[boxref].Y))

    @classmethod
    def contoursSort(cls,pageId,width,height,blocks,scale=1):
        bboxlogger.debug("{0}|contoursSort width:{1} height:{2} scale:{3}".format(str(pageId),str(width),str(height),str(scale)))
        # Make empty black image
        image=np.zeros((int(height*scale),int(width*scale)),np.uint8)
        img = BBoxUtils.draw_boxes_on_page(image,blocks,"white",scale)
        # Cluster the blocks by Y 
        lineContours=cls.__clusterBlocks(img,blocks,scale)
        # Sort list on block rank
        contours_sorted = sorted(lineContours,key= lambda o: o.rank)
        return contours_sorted

    @classmethod
    def findClusters(cls,nparray,axis=0,gapthreshhold=1):
        # sum all entries on a particular axis
        sumAxis = np.sum(nparray,axis=axis,dtype=np.uint64)
        # loop the summed values
        startindex = 0
        clusters = []
        compVal = True
        gaplength = 0
        for i, val in enumerate(sumAxis):
            # logical test to detect change between 0 and > 0
            testVal = (val > 0)
            if testVal == compVal:
                if startindex==0:
                    startindex=i
                # when the value changed to a 0, the previous rows
                # contained contours, so add start/end index to list
                if val == 0:
                    if gaplength >= gapthreshhold:
                        clusters.append((startindex,i,gaplength))
                    else:
                        if len(clusters)>0:
                            (start,end,gap)=clusters[-1]
                            clusters[-1]=(start,i,gap)
                        else:
                            clusters.append((startindex,i,gaplength))
                    startindex = i+1
                    gaplength=1
                compVal = not compVal
            else:
                if val==0:
                    gaplength+=1
            if i == len(sumAxis):
                if len(clusters)>0:
                    (start,end,gap)=clusters[-1]
                    clusters[-1]=(start,i,gap)
                else:
                    clusters.append((startindex,i,gaplength))

        return clusters

    @classmethod
    def __clusterBlocks(cls,img,blocks,scale=1,axis=0):
        # try to identify clusters of blocks
        clusters=cls.findClusters(img,axis)

        # if there is only single cluster then we shall revert to the opposite axis strategy
        if len(clusters)<=1:
            axis=np.absolute(axis-1)
            clusters=cls.findClusters(img,axis)

        bboxlogger.debug("Found {0} clusters on axis {1}".format(str(len(clusters)),str(axis)))

        lineContours = []
        # loop contours, find the boundingrect,
        # compare to line-values
        # store line number,  x value and contour index in list
        for i,cluster in enumerate(clusters):
            for j,block in enumerate(blocks):
                (x,y,w,h) = block.getBoxesAsRectangle(scale)
                if axis==1:
                    # Horizontal
                    if y >= cluster[0] and y <= cluster[1]:
                        # lineContours.append([line[0],x,j])
                        block.rank+=i
                        block.listids.append(block.rank)
                        # block.rank+=(block.xmedian/(np.shape(img)[1]/scale))
                        block.rank+=(x/np.shape(img)[1])
                        block.listids.append(block.rank)
                        #
                        block.rank+=(block.ymedian/(np.shape(img)[0]/scale))*0.01
                        block.listids.append(block.rank)
                        lineContours.append(block)
                else:
                    # Vertical
                    if x >= cluster[0] and x <= cluster[1]:
                        # the cluster id weight
                        block.rank+=i
                        block.listids.append(block.rank)
                        # the vertical median weight
                        # block.rank+=(block.ymedian/(np.shape(img)[0]/scale))
                        block.rank+=(y/np.shape(img)[0])
                        block.listids.append(block.rank)
                        # the horizontal median weight
                        block.rank+=(block.xmedian/(np.shape(img)[1]/scale))*0.01
                        block.listids.append(block.rank)
                        lineContours.append(block)

        return lineContours
