import os
import datetime
import logging

from exceptions.exceptions import MissingPythonPathEnvVariable


def logger ():
    date_str = datetime.datetime.now().strftime("%Y%m%d.%H.%M.%S.log")
    if not os.getenv("PYTHONPATH"): 
        raise MissingPythonPathEnvVariable("PYTHONPATH is not set")

    log_directory = os.getenv("PYTHONPATH") + "/logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logging.basicConfig(filename=f"{log_directory}/{date_str}", encoding='utf-8', level=logging.INFO)
    #logging.setLoggerClass(AILogger)
    #loggerx = logging.getLogger('AILogger')
    loggerx = logging.getLogger()
    loggerx.setLevel(logging.DEBUG)
    return loggerx