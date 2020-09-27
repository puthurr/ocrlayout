# Import required modules.
import logging.config
import math

from datetime import datetime
from os import path
from typing import List

import numpy as np

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
    def draw_boxes_on_page(cls,canvas,blocks,scale=1):
        """Draw the blocks of text in a vanilla canvas."""       
        origy, origx = canvas.shape
        miny, minx = canvas.shape
        maxy = 0
        maxx = 0
        # Axis 0 - sum of each column
        sumAxis0=np.zeros((1,origx),np.uint32)
        # Axis 1 - sum of each row
        sumAxis1=np.zeros((1,origy),np.uint32)
        for block in blocks:
            (minh,maxh)=block.getHeightRange(scale)
            (minw,maxw)=block.getWidthRange(scale)
            canvas[minh:maxh,minw:maxw]=block.id
            # Find the coordinates to crop the canvas to improve performance and memory usage
            minx=min(minx,minw)
            miny=min(miny,minh)
            maxx=max(maxx,maxw)
            maxy=max(maxy,maxh)
            sumAxis0[0][minw:maxw]=1
            sumAxis1[0][minh:maxh]=1

        # Make sure we stay in the canvas
        miny=max(miny-1,0)
        minx=max(minx-1,0)
        maxy=min(maxy+1,origy)
        maxx=min(maxx+1,origx)
        # Crop the current canvas
        # canvas = canvas[miny:maxy,minx:maxx]
        return canvas, 0, 0, [sumAxis0,sumAxis1]

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
        """Main sorting method to approach the natural reading."""
        bboxlogger.debug("{0}|contoursSort width:{1} height:{2} scale:{3}".format(str(pageId),str(width),str(height),str(scale)))
        # Make empty canvas
        canvas=np.zeros((int(height*scale),int(width*scale)),np.uint32)
        # Draw all the boxes on the canvas
        canvas,yshift,xshift,sumAxis=BBoxUtils.draw_boxes_on_page(canvas,blocks,scale)
        bboxlogger.debug("{0}|contoursSort - boxes applied on canvas".format(str(pageId)))
        # Cluster the blocks 
        lineContours=cls.__clusterBlocks(canvas,blocks,width,height,scale,yshift,xshift,sumAxis)
        bboxlogger.debug("{0}|contoursSort - boxes clustered".format(str(pageId)))
        # Sort list on block sorting
        contours_sorted = sorted(lineContours,key= lambda o: o.sorting)
        bboxlogger.debug("{0}|contoursSort - sorted on block rank".format(str(pageId)))

        return contours_sorted

    @classmethod
    def findClusters(cls,sumAxis,gapthreshhold=1):
        # Loop the summed values
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
                    if gaplength > gapthreshhold:
                        clusters.append((startindex,i-1,gaplength))
                    else:
                        if len(clusters)>0:
                            (start,end,gap)=clusters[-1]
                            clusters[-1]=(start,i-1,gap)
                        else:
                            clusters.append((startindex,i-1,gaplength))
                    # startindex = i+1
                    startindex = 0
                    gaplength=1
                compVal = not compVal
            else:
                if val==0:
                    gaplength+=1

            if i == (len(sumAxis)-1):
                if startindex>0:
                    clusters.append((startindex,i,gaplength))
                # if len(clusters)>0:
                #     (start,end,gap)=clusters[-1]
                #     clusters[-1]=(start,i,gap)
                # else:
                #     clusters.append((startindex,i,gaplength))

        return clusters

    # Not efficient when dealing with inch scale
    @classmethod
    def sumAxis(cls,canvas,axis=0):
        # Axis Sum Handling
        bboxlogger.debug("Finding (sub-)cluster(s) on axis {0} with canvas shape {1}".format(str(axis),str(canvas.shape)))
        # Sum all entries on a particular axis
        # sumAxis = np.trim_zeros(np.sum(canvas,axis=axis,dtype=np.uint64),'b')
        sumAxis = np.sum(canvas,axis=axis,dtype=np.uint32)
        bboxlogger.debug("Sum on axis {0} done. Sum shape {1}".format(str(axis),sumAxis.shape))
        return sumAxis

    @classmethod
    def __clusterBlocks(cls,canvas,blocks,width,height,scale=1,yshift=0,xshift=0,axis_sum=None,axis=0):
        # Default Axis 0 first (horizontal for height clusters)
        clusters=cls.findClusters(axis_sum[axis][0])

        # if there is only single cluster then we shall revert to the opposite axis strategy
        if len(clusters)<=1:
            bboxlogger.debug("No cluster(s) found on axis {0}. Switching to opposite axis.".format(str(axis)))
            axis=np.absolute(axis-1)
            # axis_sum[axis]=cls.sumAxis(canvas,axis)
            clusters=cls.findClusters(axis_sum[axis][0])

        bboxlogger.debug("Found {0} clusters on axis {1}".format(str(len(clusters)),str(axis)))

        # Width*Height
        wh=width*height

        lineContours = []
        # loop contours, find the boundingrect,
        # compare to line-values
        # store line number,  x value and contour index in list
        for i,cluster in enumerate(clusters):
            lines_counter=0
            (startindex,endindex,gap) = cluster
            bboxlogger.debug("Cluster {0} StartIndex {1} EndIndex {2} Size {3} Gap {4}".format(i,startindex,endindex,(endindex-startindex),gap))
            # Identify if we could find subclusters i.e. handling multi columns layout
            if axis==1:
                # subclusters=cls.findClusters(canvas[startindex:endindex,:],axis=0)
                # subsumaxis=cls.sumAxis(canvas[startindex+yshift:endindex+yshift,:],axis=0)
                temp = canvas[startindex+xshift:endindex+xshift,:]
                bboxlogger.debug(temp.shape)
                subsumaxis=cls.sumAxis(temp,axis=0)
                subclusters=cls.findClusters(subsumaxis)
            else:
                # subclusters=cls.findClusters(canvas[:,startindex:endindex],axis=1)
                temp = canvas[:,startindex+xshift:endindex+xshift]
                bboxlogger.debug(temp.shape)
                subsumaxis=cls.sumAxis(temp,axis=1)
                subclusters=cls.findClusters(subsumaxis)

            bboxlogger.debug("Cluster {0} - Found {1} sub-cluster(s) on axis {2}".format(i,len(subclusters),np.absolute(axis-1)))
        
            # Loop through non assigned blocks.
            for j,block in enumerate([o for o in blocks if o.cluster<0]):
                (x,y,w,h) = block.getBoxesAsRectangle(scale)
                if axis==1:
                    # Y-axis clusters aka rows
                    if y >= (startindex+yshift) and y <= (endindex+yshift):
                        lines_counter+=1
                        block.cluster=i
                        block.subcluster=0
                        if len(subclusters)>1:
                            # Do something special
                            for ic,subc in enumerate(subclusters):
                                bboxlogger.debug("Cluster {0} - Sub-Cluster {1} on X-Axis processing...".format(i,ic))
                                (subcstart,subcend,subcgap)=subc
                                if x >= (subcstart+yshift) and x <= (subcend+yshift):
                                    block.subcluster=ic
                                    break
                            block.sorting=(block.cluster,block.subcluster,block.ymedian)
                        else:
                            block.rank+=(block.xmedian/(np.shape(canvas)[1]/scale))
                            block.rank+=(block.ymedian/(np.shape(canvas)[0]/scale))*0.01
                            block.sorting=(block.cluster,block.subcluster,block.rank)
                            pass

                        lineContours.append(block)
                else:
                    # X-axis clusters aka columns
                    if x >= (startindex+xshift) and x <= (endindex+xshift):
                        lines_counter+=1
                        block.cluster=i
                        block.subcluster=0
                        if len(subclusters)>1:
                            # Do something special
                            for ic,subc in enumerate(subclusters):
                                bboxlogger.debug("Cluster {0} - Sub-Cluster {1} on X-Axis processing...".format(i,ic))
                                (subcstart,subcend,subcgap)=subc
                                if y >= (subcstart+xshift) and y <= (subcend+xshift):
                                    block.subcluster=ic
                                    break
                            block.sorting=(block.cluster,block.subcluster,block.xmedian)
                        else:
                            block.rank+=(block.ymedian/(np.shape(canvas)[0]/scale))
                            block.rank+=(block.xmedian/(np.shape(canvas)[1]/scale))*0.01

                            block.sorting=(block.cluster,block.subcluster,block.rank)
                            pass

                        lineContours.append(block)

            bboxlogger.debug("Cluster {0} assigned to {1} lines".format(i,lines_counter))

        return lineContours
