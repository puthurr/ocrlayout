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

class BBoxUtils():

    @classmethod
    def rotateBoundingBox(cls,Width:float,Height:float,boundingBox,rotationv:int):
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

    @classmethod
    def minXminY(cls,index,prevline,line): 
        prevline.BoundingBox[index].X = min(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = min(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    @classmethod
    def minXmaxY(cls,index,prevline,line): 
        prevline.BoundingBox[index].X = min(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = max(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    @classmethod
    def maxXminY(cls,index,prevline,line):
        prevline.BoundingBox[index].X = max(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = min(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]
    @classmethod
    def maxXmaxY(cls,index,prevline,line): 
        prevline.BoundingBox[index].X = max(prevline.BoundingBox[index].X, line.BoundingBox[index].X)
        prevline.BoundingBox[index].Y = max(prevline.BoundingBox[index].Y, line.BoundingBox[index].Y)
        return prevline.BoundingBox[index]

    @classmethod
    def makeRectangle(cls,line): 
        # X 
        # 
        line.BoundingBox[0].X=line.BoundingBox[3].X = min(line.BoundingBox[0].X,line.BoundingBox[3].X)
        line.BoundingBox[1].X=line.BoundingBox[2].X = max(line.BoundingBox[1].X,line.BoundingBox[2].X)
        # Y
        line.BoundingBox[0].Y=line.BoundingBox[1].Y = min(line.BoundingBox[0].Y,line.BoundingBox[1].Y)
        line.BoundingBox[2].Y=line.BoundingBox[3].Y = max(line.BoundingBox[2].Y,line.BoundingBox[3].Y)

