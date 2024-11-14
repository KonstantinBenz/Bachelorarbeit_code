import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

logDir = "logs"
if not os.path.exists(logDir):
    os.makedirs(logDir)
currentDate = datetime.now().strftime('%Y_%m_%d')
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logFile = os.path.join(logDir, f"{currentDate}.log")
fileHandler = TimedRotatingFileHandler(logFile, when="midnight", interval=1, backupCount=7)
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.INFO)
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
