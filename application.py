
from business.data import Downlaoder
from lib.logger_util import initLog

initLog()

def defaultDownloadProcessor():
    obj1 = Downlaoder()
    obj1.getDetails()
    obj1.deleteBLCode()
    obj1.getKData()
    obj1.getDayData()


defaultDownloadProcessor()