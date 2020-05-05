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
from PIL import Image, ImageDraw

from bboxhelper import (BBOXNormalizedLine, BBOXOCRResponse, BBOXPageLayout,
                       BBOXPoint)

class BBoxImageHelper():

    def __init__(self):
        super().__init__()
        log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
        logging.config.fileConfig(log_file_path)
        self.logger = logging.getLogger('bboxhelper')  # get a logger

    def save_boxed_image(self,image,fileout):
        if fileout:
            image.save(fileout)
        else:
            image.show()

    def draw_boxes(self, image, ocrresponse:BBOXOCRResponse, color):
        """Draw a border around the image using the hints in the vector list."""
        draw = ImageDraw.Draw(image)
        for page in ocrresponse.recognitionResults:
            for bound in page.Lines:
                self.logger.debug("Drawing Rectangle {}".format(str(bound.BoundingBox)))
                draw.polygon([
                # draw.rectangle([
                    bound.BoundingBox[0].X, bound.BoundingBox[0].Y,
                    bound.BoundingBox[1].X, bound.BoundingBox[1].Y,
                    bound.BoundingBox[2].X, bound.BoundingBox[2].Y,
                    bound.BoundingBox[3].X, bound.BoundingBox[3].Y], 
                    outline=color)
        return image

        # image = Image.open(filename)
        # draw_boxes(image, bounds, 'red')
