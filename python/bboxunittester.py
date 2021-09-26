import os
import os.path
import sys
import time

from enum import Enum
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from timeit import default_timer as timer

try:
    from inspect import getfullargspec as get_arg_spec
except ImportError:
    from inspect import getargspec as get_arg_spec

# OCRLAYOUT Import
try:
    from ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint
    print("PyPI Package imported")
except ImportError:
    print("Local Package imported")
    from ocrlayout_pkg.ocrlayout.bboxhelper import BBOXOCRResponse,BBoxHelper,BBOXPoint

# OCR Engines supported so far  
from testing.bboxtester_aws import AWSOCREngine
from testing.bboxtester_google import GoogleOCREngine
from testing.bboxtester_azure import AzureOCREngine, AzureReadEngine
from testing.bboxtester_utils import OCRUtils

# Inject a specific logging.conf for testing.
bboxhelper=BBoxHelper(customlogfilepath=os.path.join(os.path.dirname(os.path.realpath(__file__)), './bboxtester.conf'))

IMAGES_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../images")

# Put the version we're testing here so we can control regression
VERSION='v0.9'

RESULTS_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "../tests-results."+VERSION)

# ocrengines=[ AWSOCREngine("AWS",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER), GoogleOCREngine("Google",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER), AzureOCREngine("AZURE OCR",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER), AzureReadEngine("Azure READ",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER) ]
ocrengines=[ AzureReadEngine("Azure READ",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER) ]

import unittest
from test import support

def iterate_all_images(ocrengines=[],filter=None,callOCR=True,verbose=False):
    """OCR Text detection for all images 
    Iterate through all images located in the IMAGES_FOLDER and call all OCR Engines
    """
    for filename in os.listdir(IMAGES_FOLDER):
        if filter:
            if filter not in filename:
                continue
        if '.DS_Store' in filename:
            continue
        imgfullpath=os.path.join(IMAGES_FOLDER, filename)

        start = timer()
        print(f"{filename} started at {time.strftime('%X')}")

        p = Path(filename)
        (imgname,imgext) = os.path.splitext(p.name)
        if imgext not in '.pdf':
            OCRUtils.draw_cv2_boxes(image=imgfullpath,outputdir=RESULTS_FOLDER)

        for engine in ocrengines:
            engine.detect_text(imgfullpath, callOCR, verbose)

        end = timer()
        print(f"{filename} finished at {time.strftime('%X')}")
        print(f"Execution time in seconds: {end - start}") # Time in seconds, e.g. 5.38091952400282

class AzureTest(unittest.TestCase):

    # Only use setUp() and tearDown() if necessary
    def setUp(self):
        self.ocrengines=[ AzureReadEngine("Azure READ",bboxhelper, IMAGES_FOLDER, RESULTS_FOLDER) ]

    def tearDown(self):
        # ... code to execute to clean up after tests ...
        print(f'Azure test done.')

    def test_all_images(self):
        # Test feature one.
        iterate_all_images(ocrengines=self.ocrengines)

if __name__ == '__main__':
    unittest.main()

#python -m test -uall
