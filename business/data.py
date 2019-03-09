import os
import datetime
import logging
import time
import json

import tushare
import csv
import requests

from lib.config import ApplicatoinConfig
from lib.util import conGevent, mkdirOnce

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
            data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=10,)
            if data.empty:
                self.logger.error('get k data error:stock %s, start %s, end %s' % (stock, '1990-12-01', today))
                return (stock, False)
            data.to_csv(filePath)
            self.logger.info('all data, finish download stock %s, start_date %s, end_date:%s' % (stock, '1990-12-01', today))
            return (stock, True)
        else:
            with open(filePath, 'r') as f:
                fileSize = os.path.getsize(filePath)
                if fileSize > 500:
                    f.seek(-500, 2)
                lines = f.readlines()
                if len(lines) <= 2:
                    data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=10, )
                    if data.empty:
                        self.logger.error('get k data error:stock %s, start %s, end %s' % (stock, '1990-12-01', today))
                        return (stock, False)
                    data.to_csv(filePath)
                    self.logger.info('less all date, finish download stock %s, start_date %s, end_date:%s' % (stock, '1990-12-01', today))
                    return (stock, True)
                items = lines[-1].split(',')
                num = int(items[0])
                startDate = items[1]
            #append new data
            data = tushare.get_k_data(stock, start=startDate, end=today, autype='qfq', retry_count=10,)
            if data.empty:
                self.logger.error('get k data error:stock %s, start %s, end %s' % (stock, startDate, today))
                return (stock, False)
            with open(filePath, 'a') as f:
                itor = data.iterrows()
                itor.next()
                for row in itor:
                    num += 1
                    line = '%s,%s\n' % (num, ','.join(map(str,row[1].tolist())))
                    f.write(line)
                f.flush()

        self.logger.info('less date, finish download stock %s, start_date %s, end_date:%s' % (stock, startDate, today))
        return (stock, True)


    def _getStockCodes(self):
        stock_detail = self.ac.getConfigItem('business', 'stock_detail')
        with open(stock_detail, 'r') as f1:
            lines = f1.readlines()
            del lines[0]
            lines = map(lambda x: x.split(',')[0], lines)

        return lines

    def getKData(self):
        stock_codes = self._getStockCodes()
        mkdirOnce(self.kDataPath)

        startTime = time.time()
        bl = self.getBLCode().keys()
        stock_codes = [i for i in stock_codes if i not in bl]

        for i in range(0, 5):
            self.logger.info('it is %s time to download sotck list %s len %s' % (i, str(stock_codes), len(stock_codes)))
            resultList = conGevent(self._kDataOnce, stock_codes)

            stock_codes = []
            for item in resultList:
                if item[1] == False:
                    stock_codes.append(item[0])
            if stock_codes == []:
                break
            else:
                time.sleep(5)

        self.logger.info('%s %s' % (time.time() - startTime,  'update_hitory_data'))

        if stock_codes != []:
            self.logger.error('failed to download k data:%s' % (stock_codes))
            # update black list
            with open('resource/data_dir/blacklist', 'r') as f:
                lines = f.readlines()
            for item in stock_codes:
                lines.append('%s,name,reason\n' % (item))

            with open('resource/data_dir/blacklist', 'w') as f:
                map(f.write,lines)
                f.flush()
            self.logger.error('finish to update black list:%s' % (lines))


    def _dayDataOnce(self, stocktDict):
        stock, dateList = stocktDict.items()[0]

        dayDataPath = self.ac.getConfigItem('business', 'day_data_path')
        tmp = self.ac.getConfigItem('business', 'lst_day_data')
        dateFormat = self.ac.getConfigItem('business', 'stock_datetime_format')
        lstDownloadDate = datetime.datetime.strptime(tmp, dateFormat)

        stockDir = '%s/%s' % (dayDataPath, stock)
        if os.path.exists(stockDir) is False:
            os.mkdir(stockDir)

        if dateList == None:
            lines = None
            with open('%s/%s.csv' % (self.kDataPath, stock)) as f:
                lines = f.readlines()
            del lines[0]
            dateList = []
            for line_num in range(len(lines) - 1, -1, -1):
                date = lines[line_num].split(',')[1]
                curDate = datetime.datetime.strptime(date, dateFormat)
                if curDate > lstDownloadDate:
                    dateList.append(date)
                else:
                    break

        self.logger.info('stock code %s, day data once will download date:%s' % (stock, dateList))

        over_flag = 0
        failureList = []
        #get very date from k_data
        for date in dateList:
            stockFilePath = '%s/%s_%s.csv' % (stockDir, stock, date)
            if os.path.exists(stockFilePath):
                self.logger.info('exist the day data, stockFilePath %s' % (stockFilePath))
                continue
            try:
                df = tushare.get_tick_data(stock, date=date, src='tt', retry_count=10)
            except Exception, e:
                failureList.append(date)
                self.logger.info('get exception :%s %s , msg:%s' % (stock, date, e.message))
                continue
            except requests.exceptions.Timeout, e:
                failureList.append(date)
                self.logger.info('get timeout exception :%s %s , msg:%s' % (stock, date, e.message))
                time.sleep(50)
                continue

            if df is None or df.empty:
                over_flag += 1
                status = 'none'
                if df is not None and df.empty:
                    status = 'empty'
                self.logger.info('day data status %s :%s %s, num: %s' % (status, stock, date, over_flag))
                if over_flag > 90:
                    self.logger.info('last day data is none or empty 90 days:%s %s' % (stock, date))
                    break
                failureList.append(date)
                continue
            over_flag = 0
            df.to_csv(stockFilePath)
            self.logger.info('write day data:%s' % stockFilePath)

        if failureList == []:
            return None
        else:
            return {stock:failureList}


    def getDayData(self):
        mkdirOnce('resource/data_dir/day_data')

        #get stock codes
        stockCodes = self._getStockCodes()
        startTime = time.time()
        bl = self.getBLCode().keys()
        stockCodes = [i for i in stockCodes if i not in bl]

        #download day data
        stockList = []
        #stockList's structure is [{cod1:[date1, date2]},{cod2:[date1, date2]}]
        map(lambda x: stockList.append({x:None}), stockCodes)
        for i in range(0, 5):
            self.logger.info('retry times: %s, will download sotck day date, list %s len %s' % (i, str(stockCodes), len(stockCodes)))
            stockList = conGevent(self._dayDataOnce, stockList)
            stockList = filter(lambda x: x != None, stockList)
            if not stockList:
                break
            time.sleep(15)

        #update failure_day_data
        failureFilePath = 'logs/failure_day_data.json'
        with open(failureFilePath, 'r') as f:
            try:
                failureJson = json.load(f)
            except ValueError,e:
                failureJson = {}

            for i in range(0,len(stockList)):
                dictItem = stockList[i]
                stockCode, failureDate = dictItem.items()[0]
                if failureJson.get(stockCode):
                    failureJson[stockCode].extend(failureDate)
                else:
                    failureJson[stockCode] = failureDate

        jsonStr = json.dumps(failureJson)
        with open(failureFilePath, 'w') as f:
            f.write(jsonStr)
            f.flush()
        self.logger.info('%s %s' % (time.time() - startTime, 'update_hitory_data'))

        # update last download day data date
        dayDataPath = self.ac.getConfigItem('business', 'day_data_path')
        tmp = os.listdir('%s/%s' % (dayDataPath, '000001'))
        tmp.sort()
        lstDate = tmp[-1].split('_')[1].split('.')[0]
        self.logger.info('set lst_day_data as %s' % (lstDate))
        self.ac._updateConfig('business', 'lst_day_data', lstDate)


    def getBLCode(self):
        blFile = 'resource/data_dir/blacklist'
        blDict = {}
        with open(blFile, 'r') as f1:
            lines = f1.readlines()
            map(lambda x: blDict.update({x.split(',')[0]: x}), lines)

        return blDict

    def deleteBLCode(self):
        blDict = self.getBLCode()
        bl = blDict.keys()
        self.logger.info('black list,  download sotck list %s len %s' % (str(bl), len(bl)))
        resultList = conGevent(self._kDataOnce, bl)

        for item in resultList:
            if item[1] == True:
                blDict.pop(item[0])
        if blDict != {}:
            with open('resource/data_dir/blacklist', 'w') as f:
                map(f.write, blDict.values())
                f.flush()
