'''
Deletes all files in ../media whose last access time is > 1 minute.
Designed to be run via cron.
'''
import os
import time



#---------------------------------------
#Setup logging
import logging
import logging.handlers
import traceback
logfmt = '%(levelname)s:  %(message)s\t(%(asctime)s)'
datefmt= '%m/%d/%Y %I:%M:%S %p'
formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
logger = logging.getLogger('__main__')
logging.root.setLevel(logging.DEBUG)
#ch = logging.StreamHandler() #console handler
#ch.setFormatter(formatter)
LOGGING_DIR = os.path.join(os.path.dirname(__file__),"../logs")
if not os.path.isdir(LOGGING_DIR): os.mkdir(LOGGING_DIR)
rfh = logging.handlers.RotatingFileHandler(filename=os.path.join(LOGGING_DIR,'purge_media.log'),maxBytes=1000000,backupCount=5)
rfh.setFormatter(formatter)
logger.addHandler(rfh)
#Print tracebacks to the logfile
def dumpTraceback():
  fp = open(os.path.join(LOGGING_DIR,'purge_media.log'),'a')
  traceback.print_exc(file=fp)
  fp.close()
#---------------------------------------






MEDIA_DIR = os.path.join(os.path.dirname(__file__),'../media/')

def main():
  deleted_MB = 0
  for f in [os.path.join(MEDIA_DIR,i) for i in os.listdir(MEDIA_DIR)]:  
    (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(f)
    now = time.time()
    if now-atime > 60:
      os.remove(f)    
      deleted_MB += size/1048576.0
  if round(deleted_MB) > 0:
    logger.info('Deleted %0.2f MB from media/' % deleted_MB)

if __name__ == "__main__":
  try:
    main()
  except:
    dumpTraceback()
