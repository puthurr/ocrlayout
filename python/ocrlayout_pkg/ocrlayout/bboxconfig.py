# Import required modules.
import json
import os
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
    def __init__(self,ImageTextBoxingXThreshold,ImageTextBoxingYThreshold,ImageTextBoxingBulletListAdjustment,GoogleLineBreakThresholdInPixel,Thresholds={}):
        self.ImageTextBoxingXThreshold=ImageTextBoxingXThreshold
        self.ImageTextBoxingYThreshold=ImageTextBoxingYThreshold
        self.ImageTextBoxingBulletListAdjustment=ImageTextBoxingBulletListAdjustment
        self.GoogleLineBreakThresholdInPixel=GoogleLineBreakThresholdInPixel
        self.Thresholds=Thresholds
    @classmethod
    def from_json(cls, data):
        obj={}
        Thresholds=data["Thresholds"]
        for key in Thresholds:
            obj[key]=BBOXConfigEntryThreshold.from_json(Thresholds[key])
        return cls(data["ImageTextBoxingXThreshold"],data["ImageTextBoxingYThreshold"],data["ImageTextBoxingBulletListAdjustment"],data["GoogleLineBreakThresholdInPixel"],obj)

class BBOXConfig():
    def __init__(self,lineMergeChar,rectangleNormalization,config={}):
        self.config=config
        self.lineMergeChar=lineMergeChar
        self.rectangleNormalization=rectangleNormalization
    
    def get_Thresholds(self,unit,ppi=1):
        return self.config[unit].Thresholds

    def get_ImageTextBoxingBulletListAdjustment(self,unit,ppi=1):
        return self.config[unit].ImageTextBoxingBulletListAdjustment
    
    def get_ImageTextBoxingXThreshold(self,unit,ppi=1):
        return self.config[unit].ImageTextBoxingXThreshold
    
    def get_ImageTextBoxingYThreshold(self,unit,ppi=1):
        return self.config[unit].ImageTextBoxingYThreshold
        
    @classmethod
    def from_json(cls, data):
        ocfg={}
        cfgs=data["config"]
        for key in cfgs:
            ocfg[key]=BBOXConfigEntry.from_json(cfgs[key])
        return cls(lineMergeChar=data["lineMergeChar"],rectangleNormalization=data["rectangleNormalization"],config=ocfg)

    @classmethod
    def get_config(cls):
        # Load deafult Configuration
        json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/config.json")
        with open(json_file_path) as json_file:
            bboxconfig=cls.from_json(json.loads(json_file.read()))
        return bboxconfig
