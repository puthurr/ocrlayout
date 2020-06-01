import logging
import logging.config
from os import path

def get_logger():
    # Load Logging default configuration 
    log_file_path = path.join(path.dirname(path.abspath(__file__)), 'config/logging.conf')
    logging.config.fileConfig(log_file_path)
    bboxlogger = logging.getLogger('bboxhelper')  # get a logger
    bboxlogger.setLevel(logging.INFO)
    return bboxlogger
