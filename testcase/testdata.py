
import unittest
import os
import logging
import json

from business.data import Downlaoder
from lib.util import conGevent


class TestData(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('default')

        self.downloader = Downlaoder()
        self.dataDir= 'resource/data_dir'
        with open(self.dataDir + '/stock_detail.txt') as f:
            self.detailStockCode = f.readlines()
        bl = self.downloader.getBLCode().keys()
        self.detailStockCode = [i for i in self.detailStockCode if i.split(',')[0] not in bl]
        del self.detailStockCode[0]

    def tearDown(self):
        pass

    def testLastestKData(self):
        kStockCode = os.listdir(self.dataDir + '/k_data')

        notInList = []
        for item in self.detailStockCode:
            tmp = item.split(',')[0] + '.csv'
            if  tmp not in kStockCode:
                notInList.append(tmp)

        self.assertEqual(notInList, [],)

    def testBlAV(self):
        blDict = self.downloader.getBLCode()
        bl = blDict.keys()
        self.logger.info('black list,  download sotck list %s len %s' % (str(bl), len(bl)))
        resultList = conGevent(self.downloader._kDataOnce, bl)

        for item in resultList:
            self.assertEqual(item[1], False )

    def testDayDataFailure(self):
        with open('logs/failure_day_data.json', 'r') as f:
            try:
                failureJson = json.load(f)
            except ValueError,e:
                self.assertEqual('not failure date', 'not failure date')

        stockListOrg = map(lambda x: {x[0]: x[1]}, failureJson.items())
        stockList = conGevent(self.downloader._dayDataOnce, stockListOrg)
        stockList = filter(lambda x: x != None, stockList)

        stockDictOrg = {}
        map(lambda x: stockDictOrg.update, stockListOrg)
        stockDict = {}
        map(lambda x: stockDict.update, stockList)

        result = []
        for key, value in stockDictOrg.items():
            value2 = stockDict[key]
            value.sort()
            value2.sort()
            if value != value2:
                result.append(key)

        if result != []:
            failureFilePath = 'logs/failure_day_data.json'
            with open(failureFilePath, 'w') as f:
                f.write(json.dumps(stockDict))
                f.flush()

        self.assertEquals(result, [])
