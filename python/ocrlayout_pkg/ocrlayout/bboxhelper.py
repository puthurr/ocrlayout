# Import required modules.
import concurrent.futures
import json
import logging
import logging.config
import os
import time
import math
from timeit import default_timer as timer

# BBOX Model 
from .bboxmodel import BBOXOCRResponse, BBOXPageLayout
# BBOX Utils
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
# BBoxHelper Main Class
#
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

    def processAzureOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,concurrency:bool = True, max_workers:int = 4,verbose=None):
        """ processAzureOCRResponse method
            Process an OCR Response input from Azure and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)

        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_azure(json.loads(input),bboxconfig, bboxlogger)
        elif isinstance(input,dict):
            response=BBOXOCRResponse.from_azure(input,bboxconfig, bboxlogger)
        elif isinstance(input,BBOXOCRResponse):
            response=input
        else:
            return None

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator,concurrency,max_workers)

    def processGoogleOCRResponse(self,input,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,concurrency:bool = True, max_workers:int = 4,verbose=None):
        """ processGoogleOCRResponse method
            Process an OCR Response input from Google and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)
            
        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_google(json.loads(input),bboxconfig, bboxlogger)
        elif isinstance(input,dict):
            response=BBOXOCRResponse.from_google(input,bboxconfig, bboxlogger)
        elif isinstance(input,BBOXOCRResponse):
            response=input
        else:
            return None

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator,concurrency, max_workers)

    def processAWSOCRResponse(self,input,width,height,sortingAlgo=BBoxSort.contoursSort,boxSeparator:str = None,concurrency:bool = True, max_workers:int = 4,verbose=None):
        """ processAWSOCRResponse method
            Process an OCR Response input from AWS and returns a new BBox format OCR response.
        """
        if verbose:
            bboxlogger.setLevel(logging.DEBUG)

        #load the input json into a response object
        if isinstance(input,str):
            response=BBOXOCRResponse.from_aws_detect_document_text(json.loads(input),width,height,bboxconfig, bboxlogger)
        elif isinstance(input,dict):
            response=BBOXOCRResponse.from_aws_detect_document_text(input,width,height,bboxconfig, bboxlogger)
        elif isinstance(input,BBOXOCRResponse):
            response=input
        else:
            return None

        if response:
            return self.__processOCRResponse(response,sortingAlgo,boxSeparator,concurrency,max_workers)

    def __applyRotation(self,page,initialRotation=0):
        """__applyRotation method
        """
        rotation = round(page.clockwiseorientation,0)
        bboxlogger.debug("{0}|Orientation {1}".format(str(page.id),str(rotation)))
        page_width=page.width
        page_height=page.height
        rotation_threshold=1
        applied_rotation=initialRotation

        # Bounding Boxes Orientation
        # if ( rotation != 0):
        #     # TODO Do the Math for clockwise orientation
        #     for line in page.lines:
        #         bboxlogger.debug("Before rotation {}".format(line.boundingbox))
        #         test = BBoxUtils.rotateLineBoundingBox(line.boundingbox, -1*page.clockwiseorientation)
        #         bboxlogger.debug("After rotation 1 {}".format(test))
        #         test = BBoxUtils.rotateLineBoundingBox(line.boundingbox, page.clockwiseorientation)
        #         bboxlogger.debug("After rotation 2 {}".format(test))

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

        return (page, page_width, page_height, applied_rotation)

    def __processPage(self,page, sortingAlgo=BBoxSort.contoursSort, boxSeparator:str = None):
        """processPage
        Process a single page of an OCR Response (Azure,Google,AWS). 
        
        Returns the modified page object. 
        """
        bboxlogger.debug("{0}|Processing Page {0} with {1} lines.".format(str(page.id),len(page.lines)))

        # STEP 1 - ROTATE
        # Rotate the Bounding boxes when an angle is detected
        page,page_width,page_height,applied_rotation = self.__applyRotation(page)

        # STEP 2 - ENFORCE RECTANGLE
        # Once rotated we can enforce bounding box rectangle rule.
        if bboxconfig.rectangleNormalization:
            for line in page.lines:
                BBoxUtils.enforceRectangle(line)

        # STEP 3 - PAGE PROCESSING
        # Invoke the page processing
        try:
            page = self.__processOCRPageLayout(page, sortingAlgo, boxSeparator)
        except Exception as identifier:
            bboxlogger.warning("{0}|Exception ".format(identifier.__cause__))
            pass

        bboxlogger.debug("{0}|Processed Page {0} with {1} bbox lines.".format(str(page.id),len(page.lines)))

        # STEP 4 - UNDO ROTATION 
        # Revert the rotation of the bounding boxes back to its original orientation
        if applied_rotation!=0:
            for line in page.lines:
                line.boundingbox = BBoxUtils.rotateBoundingBox(page.width, page.height, line.boundingbox, int(-applied_rotation))
                # recalculate medians for drawing the boxes correctly
                line.calculateMedians()
            # Restore W/H 
            page.width = page_width
            page.height = page_height

        bboxlogger.debug("{0}|Completed Page {0} with {1} lines.".format(str(page.id),len(page.lines)))

        return page 

    def __processOCRResponse(self, response, sortingAlgo=BBoxSort.contoursSort, boxSeparator:str = None, concurrency:bool = True, max_workers:int = 4):
        """processOCRResponse method
        Process an OCR Response input (Azure,Google,AWS) and returns a new BBox format OCR response.

        Iterate through each page of the response and process it. Before processing we tackle the boxes 
        orientation. 
        """
        newtext = ""

        # Timer start for measuring OCR response processing time
        start = timer()
        bboxlogger.debug("Performance - Processing OCR Response started time {0}".format(time.strftime('%X')))

        if concurrency:
            # Process each page concurrently 
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_pages = {executor.submit(self.__processPage, page, sortingAlgo, boxSeparator):page.id for page in response.pages}
                concurrent.futures.wait(future_pages,return_when=concurrent.futures.ALL_COMPLETED)
                # for future in concurrent.futures.as_completed(future_pages):
                #         page_id = future_pages[future]
                #         bboxlogger.debug('Thread - page %r completed ' % (page_id))
                #         try:
                #             data = future.result()
                #         except Exception as exc:
                #             bboxlogger.debug('Thread - Page %r generated an exception: %s' % (page_id, exc))
                #         else:
                #             bboxlogger.debug('Thread - Page %r page is %d lines' % (page_id, len(data.lines)))
        else:
            # Process each page sequentially
            for page in response.pages:
                page = self.__processPage(page, sortingAlgo, boxSeparator)

        # Build the final text output for the document with annotations if configured
        for page in response.pages:
            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[0]

            if page.text:
                newtext += page.text

            if self.annotate and bboxannotate.pageTag:
                newtext+=bboxannotate.pageTag[1]
            else:
                # TODO #3
                # Default page separator
                newtext += os.linesep

        response.text = str(newtext)

        # Capture the End OCR processing time
        end = timer()
        bboxlogger.debug("Performance - Processing OCR Response completed time {0}".format(time.strftime('%X')))
        bboxlogger.debug(f"Performance - Execution time in seconds: {end - start}") # Time in seconds, e.g. 5.38091952400282

        return response

    def __processLineBoundingBoxes(self, lines, alignment, unit, ppi):
        """__processLineBoundingBoxes method
        Process an OCR Response input (Azure,Google,AWS) and returns a new BBox format OCR response.

        Iterate through each page of the response and process it. Before processing we tackle the boxes 
        orientation. 
        """
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
            XSortedList=[]

        bboxlogger.debug("bounding boxes count {}".format(len(XSortedList)))

        regions = list(list())
        regions.append(list())
        regionx = 0.0
        regionidx = 0

        # STEP 1 - X-Axis sorted 
        # //First Pass on the X Axis 
        for line in XSortedList:
            xcurrent = line.boundingbox[boxref].X

            if (alignment == CenteredAlignment):
                xcurrent = line.xmedian

            lowb=math.floor(regionx - (Xthresholdratio * bboxconfig.get_ImageTextBoxingXThreshold(unit,ppi)))
            highb=math.ceil(regionx + (Xthresholdratio * bboxconfig.get_ImageTextBoxingXThreshold(unit,ppi)))

            if lowb>0.0:
                bboxlogger.debug("{6}|Region X-step Id:{0} X:{1} LowX {2}<{3}<{4} HighX | Same Region? {5} ".format(str(regionidx),str(regionx),str(lowb),str(xcurrent),str(highb),str((xcurrent >= lowb and xcurrent <= highb)),alignment))

            if (regionx == 0.0):
                regions[regionidx].append(line)
                regionx = xcurrent
            # //can be improved by testing the upper X boundaries eventually
            elif (xcurrent >= lowb and xcurrent <= highb):
                regions[regionidx].append(line)
                # Adjust the regionx to take care of slight deviation
                if ( not alignment == CenteredAlignment ):
                    regionx = math.floor((xcurrent + regionx) / 2)
            else:
                # // Add new region 
                regions.append(list())
                regionidx+=1
                regions[regionidx].append(line)
                regionx = xcurrent

        bboxlogger.debug("{1}|Found {0} regions.".format(len(regions),alignment))

        # STEP 2 - Y-Axis sorted 
        # //Second Pass on the Y Axis 
        for regidx,lines in enumerate(regions):
            lines.sort(key=lambda o : o.boundingbox[boxref].Y)
            # YSortedList = sorted(lines,key=lambda o : o.boundingbox[boxref].Y)
            # // the entries are now sorted ascending their Y axis
            regiony = 0.0
            bboxlogger.debug("{1}|Region {2} Y-step with {0} lines.".format(str(len(lines)),alignment, regidx))

            for line in lines:
                # //Top Left Y
                ycurrent = line.boundingbox[boxref].Y
                # lowb=(regiony - (Ythresholdratio * bboxconfig.config[unit].ImageTextBoxingYThreshold))
                lowb=math.floor(regiony-(regiony*0.05))
                highb=math.ceil((regiony + (Ythresholdratio * bboxconfig.get_ImageTextBoxingYThreshold(unit,ppi))))

                bboxlogger.debug("{7}-{8}|Line bbox {0} {6} {1} | LowY {2}<{3}<{4} HighY | Merge {5}".format(str(line.boundingbox),str(line.text),str(lowb),str(ycurrent),str(highb),str((ycurrent >= lowb and ycurrent <= highb)),str(regiony),alignment,regidx))

                if (regiony == 0.0):
                    prevline = line
                # elif (ycurrent >= lowb and ycurrent < highb):
                elif (ycurrent >= lowb and ycurrent < highb):
                    prevline.mergeLine(line,bboxconfig.lineMergeChar)
                else:
                    prevline = line

                # //Take the bottom left Y axis as new reference
                # regiony = line.boundingbox[3].Y
                regiony = line.boundingbox[2].Y
        return XSortedList

    def __processOCRPageLayout(self, page:BBOXPageLayout, sortingAlgo=None, boxSeparator:str = None):
        """ processOCRPageLayout method
            Process a single page from an OCR input, returns the same page with enhanced boxing data & text.
        """
        inlines=[o for o in page.lines if o.merged == False]
        bboxlogger.debug("{1}|Input # lines {0}".format(len(inlines),str(page.id)))

        # STEP 1 - ALIGNMENT-BASED MERGE 
        #
        # Go through potential Text Alignment : Left, Right and Centered.
        for alignment in Alignments:
            bboxlogger.debug("{1}|Processing {0}".format(alignment,str(page.id)))
            page.lines = self.__processLineBoundingBoxes(page.lines,alignment,page.unit,page.ppi)

        # STEP 2 - EXTRA LEFT-ALIGNMENT-BASED MERGE 
        #
        # Another pass on LeftAlignment
        bboxlogger.debug("{1}-2|Processing {0}".format(LeftAlignment,str(page.id)))
        page.lines = self.__processLineBoundingBoxes(page.lines,LeftAlignment,page.unit,page.ppi)

        outlines=[o for o in page.lines if o.merged == False]
        bboxlogger.debug("{1}|Output {0} lines before sorting...".format(len(outlines),str(page.id)))

        # STEP 3 - SORTING
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

        # STEP 4 - TEXT OUTPUT
        # Once sorted correctly with reading approx we can output the actual text 
        # 
        newtext = ""
        for i,block in enumerate(sortedBlocks):
            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[0]
            else:
                newtext+=boxSeparator[0]

            newtext+=block.text

            if boxSeparator is None:
                if self.annotate and bboxannotate.blockTag:
                    newtext+=bboxannotate.blockTag[1]
                else:
                    # look ahead the next block see if we could do a last minute merge on the text only. 
                    if (i+1<len(sortedBlocks)):
                        # if block.getClusterId() != sortedBlocks[i+1].getClusterId() and (not sortedBlocks[i+1].text[0].isupper()):
                        if not (block.text.isupper() or sortedBlocks[i+1].text[0].isupper() or sortedBlocks[i+1].text[0].isdigit()):
                            if block.text.strip().endswith("."):
                                newtext+=os.linesep
                            elif block.text.strip().endswith("-"):
                                newtext=newtext[:-1]
                                # newtext+=''
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
