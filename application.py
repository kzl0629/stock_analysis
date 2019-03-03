
import datetime

import tushare

from business.data import Downlaoder
from lib.logger_util import initLog

initLog()

start = datetime.datetime.now()
# ts.get_today_all()
# import tushare as ts

# df = ts.get_index()
# stock_detail = tushare.get_stock_basics()
# print datetime.datetime.now() - start
#
# print stock_detail

obj1 = Downlaoder()
# obj1.getDetails()
# obj1._kDataOnce('601162')
obj1.getKData()
# obj1._dayDataOnce('601162')
obj1.getDayData()