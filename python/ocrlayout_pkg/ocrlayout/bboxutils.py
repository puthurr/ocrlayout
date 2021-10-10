# Import required modules.
import math
import copy
from types import new_class
import numpy as np
from numpy.core.fromnumeric import sort

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
    def enforceRectangle(cls,line): 
        # X 
        line.boundingbox[0].X=line.boundingbox[3].X = min(line.boundingbox[0].X,line.boundingbox[3].X)
        line.boundingbox[1].X=line.boundingbox[2].X = max(line.boundingbox[1].X,line.boundingbox[2].X)
        # Y
        line.boundingbox[0].Y=line.boundingbox[1].Y = min(line.boundingbox[0].Y,line.boundingbox[1].Y)
        line.boundingbox[2].Y=line.boundingbox[3].Y = max(line.boundingbox[2].Y,line.boundingbox[3].Y)

    @classmethod
    def draw_boxes_on_page(cls,canvas,blocks,scale=1):
        """Draw the blocks of text on a vanilla canvas."""       
        for block in blocks:
            (minh,maxh)=block.getHeightRange(scale)
            (minw,maxw)=block.getWidthRange(scale)
            canvas[minh:maxh,minw:maxw]=block.id

        return canvas

#
# Bounding Boxes Sorting class
#
class BBoxContourCluster():
    def __init__(self, parent_cluster, rid, axis, startindex, endindex, value = 0, level = 0, gaplength = 0):
        self.rid=rid
        self.level=level
        self.startindex=startindex
        self.endindex=endindex
        # Axis specific
        self.axis=axis
        self.axis_sum=value
        self.axis_size=max(0,endindex-startindex)+1
        self.gap=gaplength
        self.blockid=-1
        # Sorting field
        self.sorting=[]
        self.xtranslate=0
        self.ytranslate=0
        self.optimized=False

        if parent_cluster:
            self.sorting=copy.deepcopy(parent_cluster.sorting)
            self.xtranslate+=parent_cluster.xtranslate
            self.ytranslate+=parent_cluster.ytranslate

        self.sorting.append(str(self.level)+str(self.rid))

    def isRootCluster(self):
        return (self.level==0) and (self.rid==0)

    def calculateAxisSize(self):
        self.axis_size=max(0,self.endindex-self.startindex)+1

    # def caculateAxisSum(self,canvas):
    #     self.calculateAxisSize()
    #     sum_tuples=BBoxSort.__summarizeCanvas(BBoxSort.__getClusterCanvas(self,canvas,yshift,xshift))
    #     self.axis_sum=sum_tuples(self.axis)

    def getClusterAbsoluteCoordinates(self):
        x=self.xtranslate
        y=self.ytranslate
        if self.axis==0:
            x+=self.startindex
        else:
            y+=self.startindex
        return (x,y)

    def getSorting(self):
        return [int(o) for o in self.sorting]
        # return map(int,self.sorting)


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

        # STEP 1 - Make empty canvas
        canvas=np.zeros((int(height*scale),int(width*scale)),np.uint32)

        # STEP 2 - Draw all the boxes on the canvas
        canvas=BBoxUtils.draw_boxes_on_page(canvas,blocks,scale)
        bboxlogger.debug("{0}|contoursSort - bounding boxes applied on canvas".format(str(pageId)))

        # STEP 3 - Cluster the blocks
        yshift=0
        xshift=0
        sumAxis= cls.__summarizeCanvas(canvas)
        # lineContours=cls.__clusterBlocks(canvas,blocks,width,height,scale,yshift,xshift,sumAxis)
        lineContours=cls.__assignBlocksToClusters(canvas,blocks,width,height,scale,yshift,xshift,sumAxis)
        bboxlogger.debug("{0}|contoursSort - boxes clustered".format(str(pageId)))

        # STEP 4 - Sort list on block sorting attribute n-tuple
        contours_sorted = sorted(lineContours,key= lambda o: o.sorting)
        bboxlogger.debug("{0}|contoursSort - sorted on block rank".format(str(pageId)))

        return contours_sorted

    @classmethod
    def findClusters(cls,parent_cluster,axis,sumAxis,level=0, gapthreshhold=1):
        bboxlogger.debug("Finding cluster(s) on axis {0} ".format(str(axis)))
        # Loop the summed values
        startindex = -1
        sumValue = -1
        clusters = []
        clusters_count=0
        compVal = True
        gaplength = 0
        for i, val in enumerate(sumAxis):
            # logical test to detect change between 0 and > 0
            testVal = (val > 0)
            if testVal == compVal:
                if startindex==-1:
                    startindex=i
                    sumValue=val
                endIndex=max(startindex,i-1)
                # When the value changed to a 0, the previous rows
                # contained contours, so add start/end index to list
                if val == 0:
                    if gaplength > gapthreshhold:
                        clusters_count+=1
                        new_cluster=BBoxContourCluster(parent_cluster,clusters_count,axis,startindex,endIndex,sumValue,level,gaplength)
                        clusters.append(new_cluster)
                    else:
                        # Previous Cluster ending
                        if len(clusters)>0:
                            prevCluster=clusters[-1]
                            clusters[-1]=BBoxContourCluster(parent_cluster,clusters_count,axis,prevCluster.startindex,endIndex,prevCluster.axis_sum,level,prevCluster.gap)
                        else:
                        # Starting a new cluster
                            clusters_count+=1
                            new_cluster=BBoxContourCluster(parent_cluster,clusters_count,axis,startindex,endIndex,sumValue,level,gaplength)
                            clusters.append(new_cluster)
                            # clusters.append(BBoxContourCluster(clusters_count,axis,startindex,endIndex,parent,level,gaplength))
                    startindex = -1
                    gaplength=1
                compVal = not compVal
            else:
                if val==0:
                    gaplength+=1
                sumValue = val

            if i == (len(sumAxis)-1):
                if startindex>-1:
                    clusters_count+=1
                    new_cluster=BBoxContourCluster(parent_cluster,clusters_count,axis,startindex,i,val,level,gaplength)
                    clusters.append(new_cluster)

        return clusters


    @classmethod
    def optimizeClusters(cls,parent_cluster,axis,clusters,level=0):
        bboxlogger.debug("Optimize cluster(s) on axis {0} ".format(str(axis)))
        optimized_clusters=[]
        if len(clusters)>1:
            remaining_cluster=BBoxContourCluster(parent_cluster,2,axis,-1,-1,0,level,1)
            remaining_cluster.optimized=True
            for i,cluster in enumerate(clusters):
                if i==0:
                    optimized_clusters.append(cluster)
                else:
                    if remaining_cluster.startindex==-1 :
                        remaining_cluster.startindex=cluster.startindex
                    else:
                        remaining_cluster.startindex=min(remaining_cluster.startindex,cluster.startindex)
                    remaining_cluster.endindex=max(remaining_cluster.endindex,cluster.endindex)                    
            optimized_clusters.append(remaining_cluster)
            bboxlogger.debug("Optimized cluster Axis {0} StartIdx {1} EndIdx {2} ".format(str(axis),str(remaining_cluster.startindex),str(remaining_cluster.endindex)))
        else:
            optimized_clusters.append(clusters[0])
        return optimized_clusters



    # # Not efficient when dealing with inch scale
    # @classmethod
    # def __summarizeOneAxis(cls,canvas,axis=0):
    #     # Axis Sum Handling
    #     bboxlogger.debug("Sum axis {0} with canvas shape {1}".format(str(axis),str(canvas.shape)))
    #     sumAxis = np.sum(canvas,axis=axis,dtype=np.uint32)
    #     bboxlogger.debug("Sum axis {0} done. Sum shape {1}".format(str(axis),sumAxis.shape))
    #     return sumAxis

    @classmethod
    def __summarizeCanvas(cls,canvas):
        sumAxis0 = np.sum(canvas,axis=0,dtype=np.uint32)
        sumAxis1 = np.sum(canvas,axis=1,dtype=np.uint32)
        bboxlogger.debug("Sum All - Axis {0} shape {1}. Axis {2} shape {3}".format(str(0),sumAxis0.shape,str(1),sumAxis1.shape))
        # result = [tuple(map(sum, zip(*ele))) for ele in zip(*canvas)]
        return [sumAxis0,sumAxis1]

    @classmethod
    def __getClusterCanvas(cls,cluster,canvas,yshift=0,xshift=0):
        # Determine the cluster canvas            
        # Axis = 1 identifies rows in a page
        if cluster.axis==1:
            cluster_canvas = canvas[cluster.startindex+xshift:cluster.endindex+1+xshift,:]
            if not cluster.isRootCluster():
                cluster.ytranslate+=cluster.startindex
        else:
        # Axis = 0 identifies columns in a page
            cluster_canvas = canvas[:,cluster.startindex+yshift:cluster.endindex+1+yshift]
            if not cluster.isRootCluster():
                cluster.xtranslate+=cluster.startindex
        return  cluster_canvas

    @classmethod
    def __recurseClusters(cls,level,clusters,canvas,yshift=0,xshift=0):
        inner_clusters=[]
        for i,cluster in enumerate(clusters):
            bboxlogger.debug("---")
            bboxlogger.debug("Level {0} Cluster {1} StartIndex {2} EndIndex {3} Axis-Size {4} Axis {6} Gap {5}".format(level,i,cluster.startindex,cluster.endindex,cluster.axis_size,cluster.gap,cluster.axis))

            # Shape the cluster canvas
            cluster_canvas=cls.__getClusterCanvas(cluster,canvas,yshift,xshift)
            bboxlogger.debug("Cluster canvas shape {0}".format(cluster_canvas.shape))

            # Summarize the cluster canvas
            subsumaxis=cls.__summarizeCanvas(cluster_canvas)
          
            if cluster.optimized:
                cluster.calculateAxisSize()
                cluster.axis=np.absolute(cluster.axis-1)

            # Find sub-cluster(s) on the same axis or reset axis
            sameAxisSubClusters=cls.findClusters(cluster,cluster.axis,subsumaxis[cluster.axis],level)

            if (len(sameAxisSubClusters) > 1):
                bboxlogger.debug("Level {0} Cluster {1} - Found {2} clusters on the same axis {3}".format(level,i,str(len(sameAxisSubClusters)),str(cluster.axis)))
                inner_clusters.extend(cls.__recurseClusters(level+1,sameAxisSubClusters,cluster_canvas,yshift,xshift))
            else:
                # Reverse the cluster axis to find sub clusters...
                revertaxis=np.absolute(cluster.axis-1)
                oppositeAxisSubClusters=cls.findClusters(cluster,revertaxis,subsumaxis[revertaxis],level)

                # Always try to optimize first 
                oppositeAxisSubClusters=cls.optimizeClusters(cluster,revertaxis,oppositeAxisSubClusters,level)

                if (len(oppositeAxisSubClusters) > 1):
                    bboxlogger.debug("Level {0} Cluster {1} - Found {2} clusters on the opposite axis {3}".format(level,i,str(len(oppositeAxisSubClusters)),str(revertaxis)))
                    inner_clusters.extend(cls.__recurseClusters(level+1,oppositeAxisSubClusters,cluster_canvas,yshift,xshift))
                else:
                    if (len(oppositeAxisSubClusters) > 0):
                        # the single opposite cluster will be used to determine the block id
                        bboxlogger.debug("Level {0} Cluster {1} - Unique opposite cluster found".format(level,i))

                        same_axis_cluster=sameAxisSubClusters[0]
                        opposite_cluster=oppositeAxisSubClusters[0]
                        # if cluster.optimized:
                        #     cluster.blockid=int(opposite_cluster.axis_sum/cluster.axis_size)
                        # else:
                        cluster.blockid=int(opposite_cluster.axis_sum/same_axis_cluster.axis_size)

                        bboxlogger.debug("Level {0} Cluster {1} - Assigned Block Id {2}".format(level,i,cluster.blockid))
                    else:
                        bboxlogger.debug("Level {0} Cluster {1} - ERROR No opposite cluster found.".format(level,i))

            # When we exhaust all clusterization we add the cluster to the list. 
            if (len(sameAxisSubClusters) <= 1 and len(oppositeAxisSubClusters) <=1):
                bboxlogger.debug("Level {0} Cluster {1} Adding cluster with axis sum set to {2}".format(level,i,cluster.axis_sum))
                inner_clusters.append(cluster)

        return inner_clusters

    @classmethod
    def __assignBlocksToClusters(cls,canvas,blocks,width,height,scale=1,yshift=0,xshift=0,axis_sum=None,axis=0):

        # Default Axis 0 first (horizontal for height clusters)
        root_cluster=BBoxContourCluster(None,0,0,0,width)

        # Start the clusters iteration
        clusters = cls.__recurseClusters(0,[root_cluster],canvas,yshift,xshift)
        
        # Width*Height
        wh=width*height
        lineContours = []
        #
        # ASSIGN BLOCKS TO CORRESPONDING CLUSTER
        #
        bboxlogger.debug("---")
        bboxlogger.debug("Enumerate {0} cluster(s) to assign them to blocks".format(str(len(clusters))))

        # loop contours, find the boundingrect,
        # compare to line-values
        # store line number,  x value and contour index in list
        for i,cluster in enumerate(clusters):
            lines_counter=0
            bboxlogger.debug("Cluster {0} Axis {5} StartIndex {1} EndIndex {2} Size {3} BlockId {4}".format(i,cluster.startindex,cluster.endindex,cluster.axis_size,cluster.blockid,cluster.axis))

            # Loop through non assigned blocks.
            for j,block in enumerate([o for o in blocks if o.cluster<0]):
                # (x,y,w,h) = block.getBoxesAsRectangle(scale)
                # (cx,cy) = cluster.getClusterAbsoluteCoordinates()
                # if ( cluster.xtranslate == x and cluster.ytranslate== y):
                #     lines_counter+=1
                #     block.cluster=1
                #     block.sorting=cluster.getSorting()
                #     block.sorting.append(block.ymedian-(width-block.xmedian)*0.1)
                #     lineContours.append(block)
                #     break

                if block.id == cluster.blockid:
                    bboxlogger.debug("Cluster - Block match on id {0}".format(cluster.blockid))
                    lines_counter+=1
                    block.cluster=1
                    block.sorting=cluster.getSorting()
                    # block.sorting=(block.cluster,block.ymedian-(width-block.xmedian)*0.1)
                    # block.sorting.append(block.ymedian-(width-block.xmedian)*0.1)

                    lineContours.append(block)
                    break

                # if cluster.axis==1:
                #     # Y-axis clusters aka columns
                #     if y >= (cluster.startindex+yshift) and y <= (cluster.endindex+yshift):
                #         lines_counter+=1

                #         block.cluster=1
                #         block.sorting=cluster.getSorting()
                #         # block.sorting=(block.cluster,block.ymedian-(width-block.xmedian)*0.1)
                #         block.sorting.append(block.ymedian-(width-block.xmedian)*0.1)

                #         lineContours.append(block)
                # else:
                #     # X-axis clusters aka rows
                #     if x >= (cluster.startindex+xshift) and x <= (cluster.endindex+xshift):
                #         lines_counter+=1

                #         block.cluster=1
                #         block.sorting=cluster.getSorting()
                #         # block.cluster=cluster.level
                #         # block.subcluster=cluster.rid
                #         # block.sorting=(block.cluster,block.xmedian-(height-block.ymedian)*0.1)
                #         block.sorting.append(block.xmedian-(height-block.ymedian)*0.1)

                #         lineContours.append(block)

            bboxlogger.debug("Cluster {0} Axis {3} assigned to {1} line(s) blockid {2} ".format(i,lines_counter,cluster.blockid,cluster.axis))

        return lineContours
