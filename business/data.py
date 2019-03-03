import os
import datetime
import logging
import time

import tushare
import csv
import requests

from lib.config import ApplicatoinConfig
from lib.util import conGevent

class Downlaoder(object):
    def __init__(self):
        self.ac = ApplicatoinConfig()
        self.kDataPath = self.ac.getConfigItem('business', 'k_data_path')
        self.logger = logging.getLogger('default')

    def getDetails(self):
        stock_detail_file = ApplicatoinConfig().getConfigItem('business', 'stock_detail')
        stock_detail = tushare.get_stock_basics()
        stock_detail.to_csv(stock_detail_file + '_tmp')

        with open(stock_detail_file + '_tmp', 'r') as f1:
            with open(stock_detail_file, 'w') as f2:
                reader = csv.reader(f1)
                header = reader.next()
                f2.write(','.join(header) + '\n')

                for line in reader:
                    if line[0].startswith('60') or line[0].startswith('00'):
                        f2.write(','.join(line) + '\n')
                f2.flush()
        os.remove(stock_detail_file + '_tmp')

    def _kDataOnce(self, stock):
        today = datetime.datetime.now().__str__().split(' ')[0]
        self.logger.info('start download stock %s, data:%s' % (stock, today))
        filePath = self.kDataPath + os.path.sep + stock + '.csv'
        if os.path.exists(filePath) == False:
            data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=1000,)
            data.to_csv(filePath)
        else:
            with open(filePath, 'r') as f:
                fileSize = os.path.getsize(filePath)
                if fileSize > 500:
                    f.seek(-500, 2)
                lines = f.readlines()
                if len(lines) <= 2:
                    data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=1000, )
                    data.to_csv(filePath)
                    return
                items = lines[-1].split(',')
                num = int(items[0])
                startDate = items[1]
            #append new data
            data = tushare.get_k_data(stock, start=startDate, end=today, autype='qfq', retry_count=1000,)
            with open(filePath, 'a') as f:
                itor = data.iterrows()
                itor.next()
                for row in itor:
                    num += 1
                    line = '%s,%s\n' % (num, ','.join(map(str,row[1].tolist())))
                    f.write(line)
                f.flush()
        self.logger.info('finish download stock %s, data:%s' % (stock, today))

    def getStockCodes(self):
        stock_detail = self.ac.getConfigItem('business', 'stock_detail')
        with open(stock_detail, 'r') as f1:
            lines = f1.readlines()
            del lines[0]
            lines = map(lambda x: x.split(',')[0], lines)

        return lines

    def getKData(self):
        stock_codes = self.getStockCodes()

        if os.path.exists(self.kDataPath) == False:
            os.mkdir(self.kDataPath)

        startTime = time.time()
        self.logger.info('will download sotck list %s len %s' % (str(stock_codes), len(stock_codes)))
        conGevent(self._kDataOnce, stock_codes)

        print time.time() - startTime, 'update_hitory_data'


    def _dayDataOnce(self, stock):
        dayDataPath = self.ac.getConfigItem('business', 'day_data_path')
        stockDir = '%s/%s' % (dayDataPath, stock)
        if os.path.exists(stockDir) is False:
            os.mkdir(stockDir)

        lines = None
        with open('%s/%s.csv' % (self.kDataPath, stock)) as f:
            lines = f.readlines()

        del lines[0]
        over_flag = 0
        #get very date from k_data
        for line_num in range(len(lines) - 1, -1, -1):
            date = lines[line_num].split(',')[1]
            year = int(date.split('-')[0])
            if year <= 2016:
                continue

            stockFilePath = '%s/%s_%s.csv' % (stockDir, stock, date)
            if os.path.exists(stockFilePath) is False:
                try:
                    df = tushare.get_tick_data(stock, date=date, src='tt')
                    # if df is None:
                    #     df = tushare.get_tick_data(stock, date=date, src='sn')
                    #     if df is not None:
                    #         self.logger.info('tt data is none but sn is good:%s %s' % (stock, date))
                except Exception,e:
                    self.logger.info('get exception :%s %s , msg:%s' % (stock, date, e.message))
                    continue
                except requests.exceptions.Timeout, e:
                    self.logger.info('get timeout exception :%s %s , msg:%s' % (stock, date, e.message))
                    time.sleep(50)
                    continue

                if df is None:
                    over_flag += 1
                    self.logger.info('day data is none:%s %s, num: %s' % (stock, date, over_flag))
                    with open(stockFilePath, 'w') as f:
                        f.write('none\n')
                        f.flush()
                    if over_flag > 365:
                        self.logger.info('last day data is none:%s %s' % (stock, date))
                        break
                    continue
                over_flag = 0
                df.to_csv(stockFilePath)
                self.logger.info('write day data:%s' % stockFilePath)
            else:
                self.logger.info('day data exists:%s' % stockFilePath)
                continue

        return

    def getDayData(self):
        stock_codes = self.getStockCodes()

        startTime = time.time()
        self.logger.info('will download sotck list %s len %s' % (str(stock_codes), len(stock_codes)))
        conGevent(self._dayDataOnce, stock_codes)

        print time.time() - startTime, 'update_hitory_data'
