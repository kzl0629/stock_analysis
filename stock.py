# -*- coding:utf-8 -*-
__all__ = ['precision']

import sys
import os
import re
import time
import shutil
import logging
import csv
from math import fabs
import datetime

from bs4 import BeautifulSoup
import tushare

from lib.util import request_timeout, con_exec, max, min
from lib.config import ApplicatoinConfig


precision = float(ApplicatoinConfig().get_config_item('config', 'precision'))


class Dealor(object):
    logger = logging.getLogger('default')
    history_path = ApplicatoinConfig().get_config_item('stock_file', 'history_path')

    def __init__(self):
        self.logger.info('start stock %s', str(datetime.datetime.now()))
        pass

    def _list_stock (self):
        response =  request_timeout("http://quote.eastmoney.com/stock_list.html", 10)
        if response.status_code != 200:
            raise Exception("request error: " + str(response.status_code) + " " + response.content)
        soup = BeautifulSoup(response.content)
        tags = soup.find_all('a')
        tags = tags [386: -44]
        print len(tags)
        stock_list = []
        for item in tags:
            if not item.get('href'):
                continue
            stock = re.split('/', item['href'])[3].split('.')[0]
            loc = stock[0: 2]
            num = stock[2:]
            if num.startswith('900'):
                continue
            if num.startswith('1'):
                continue
            if num.startswith('20'):
                continue
            if num.startswith('30'):
                continue
            stock_code = loc + num
            stock_code = stock_code.encode('ascii','ignore')
            stock_list.append(stock_code)
        return stock_list

    def _list_details(self, code):
        start_time = time.time()
        response = request_timeout('http://qt.gtimg.cn/q=' + code)
        self.logger.debug('request time:\t' + code + '\t' + str(time.time() - start_time))
        if response.status_code != 200:
            return ("error: " + str(response.status_code) + " " + response.content)
        if response.content.startswith('pv_none_match=1;') or \
                response.content.startswith('v_pv_none_match'):
            return ('error', code, 0)
        try:
            details = re.split('~', response.content)
            if details[5] == '0.00':
                return ('error: stock is stopped', code, 0)
            name = details[1]
            code = code.encode('ascii','ignore')
            static_pe= details[53][0:-3]
            dym_pe = details[52]
            pb = details[46]
            currency_value = details[44]
        except Exception,e:
            logging.error('response is unexpected:' + response.content + 'code: ' + code)
            sys.exit()
        return name, code, static_pe, dym_pe, pb, currency_value

    def filter(self, low_static_pe, high_static_pe, low_dyn_pe, hi_dyn_pe,
               low_pb, high_pb, low_value, high_value):

        stock_detail_file = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        with open(stock_detail_file, 'r') as f1:
            lines = f1.readlines()
        lines = ''.join(lines).split('\n')

        stock_detail_filtered = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail_filtered')
        with open(stock_detail_filtered, 'w') as f2:
            for line in lines:
                items = line.split('\t')
                if len(items) < 7:
                    continue
                #item must be bigger than low and lower than high
                if low_static_pe != None and float(items[3]) < low_static_pe:
                    continue
                if high_static_pe != None and float(items[3]) > high_static_pe:
                    continue
                if low_dyn_pe != None and float(items[4]) < low_dyn_pe:
                    continue
                if hi_dyn_pe != None and float(items[4]) > hi_dyn_pe:
                    continue
                if low_pb != None and float(items[5]) < low_pb:
                    continue
                if high_pb != None and float(items[5]) > high_pb:
                    continue
                if low_value != None and float(items[6]) < low_value:
                    continue
                if high_value != None and float(items[6]) > high_value:
                    continue

                if float(items[3]) > float(items[4]):
                    continue

                f2.write(line + '\n')


    def update_stock_list(self):
        start_time = time.time()
        #get all stocks
        stocks = self._list_stock()
        stock_details_list = con_exec(self._list_details, stocks)

        #write stock code to file
        stock_code = ApplicatoinConfig().get_config_item('stock_file', 'stock_code')
        with open(stock_code, 'w') as f:
            for stock_details in stock_details_list:
                self.logger.info('get code: ' + stock_details[1] + ' ' + stock_details[0])
                if stock_details[0]. startswith('error'):
                    continue
                try:
                    if stock_details[2] == '' or float(stock_details[2]) == 0:
                        continue
                except Exception,e:
                    self.logger.error('cratical error' + '\t' + stock_details[1])
                    print 'cratical error' + '\t' + stock_details[1]
                    sys.exit()
                f.write(stock_details[1] + '\n')
            f.flush()
        print time.time() - start_time


    def stocks_to_txt(self):
        stock_code = ApplicatoinConfig().get_config_item('stock_file', 'stock_code')
        with open(stock_code, 'r') as f1:
            lines = f1.readlines()
        lines = ''.join(lines).split('\n')
        del lines[-1]

        start_time = time.time()

        stock_detail = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        stock_details_list = con_exec(self._list_details, lines)
        with open(stock_detail, 'w') as f:
            #f.write('名称' + '\t' + '代码' + '\t' + '静态市盈率' + '动态市盈率' + 'pb' + 'currency_value' + '\n')
            seq = 0
            for stock_details in stock_details_list:
                self.logger.info('get code: ' + stock_details[1] + ' ' + stock_details[0])
                if stock_details[0]. startswith('error'):
                    continue
                try:
                    if stock_details[2] == '' or float(stock_details[2]) == 0:
                        continue
                except Exception,e:
                    self.logger.error('cratical error' + '\t' + stock_details[1])
                    print 'cratical error' + '\t' + stock_details[1]
                    sys.exit()
                seq += 1
                f.write(str(seq) + '\t' + stock_details[0] + '\t' + stock_details[1][2:] + '\t' + stock_details[2] +
                        '\t' + stock_details[3] + '\t' + stock_details[4] + '\t' + stock_details[5]
                        + '\n')
            f.flush()
        print time.time() - start_time

    def _download_history_data_slow(self, stock):
        stock = stock[2:]
        data = tushare.get_h_data(stock)
        with open(Dealor.history_path + os.path.sep + stock + '.csv', 'w') as f:
            header = 'date, code, name, close, high, low, open\n'
            f.write(header)
            for row in data.iterrows():
                values = row[1].__str__().split('\n')
                line = '%s, %s, %s, %s, %s, %s, %s\n' % \
                       (row[0].__str__().split()[0], stock, 'NULL', values[2].split()[-1], values[1].split()[-1],
                        values[3].split()[-1], values[0].split()[-1])
                f.write(line)
            f.flush()
        return stock

    def _download_history_data_fast(self, stock):
        if stock[0:2] == 'sh':
            stock = '0' + stock[2:]
        elif stock[0:2] == 'sz':
            stock = '1' + stock[2:]


        res = request_timeout('http://quotes.money.163.com/service/chddata.html?code='
                              + stock +
                              '&start=19901219&end=20380426&fields=TCLOSE;HIGH;LOW;TOPEN;'
                              'LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP', 10)
        self.logger.info('download_history_data: ' + stock)
        if res == None:
            self.logger.info('request error')
            sys.exit(0)
        with open(Dealor.history_path + os.path.sep + stock[1:] + '.csv', 'w') as f:
            f.write(res.content)
            f.flush()

        return stock

    def update_hitory_data(self, mode):
        stock_code = ApplicatoinConfig().get_config_item('stock_file', 'stock_code')
        with open(stock_code, 'r') as f1:
            lines = f1.readlines()
        lines = ''.join(lines).split('\n')
        del lines[-1]

        if os.path.exists(Dealor.history_path):
            shutil.rmtree(Dealor.history_path)
        os.mkdir(Dealor.history_path)

        start_time = time.time()
        #con_exec(self._download_history_data, lines, 1)
        if mode == 'slow':
            for line in lines:
                retry_times = 10
                for i in range(0, retry_times):
                    try:
                        self._download_history_data_slow(line)
                        self.logger.info('download sotck %s at %s' % (str(line),str(datetime.datetime.now())))
                        break
                    except Exception, e:
                        self.logger.error('_download_history_data retry: ' + str(i) +
                                          ' stock:' + str(line) + ' ' + e.__str__())
                        time.sleep(55)
        elif mode == 'fast':
            process_num = int(ApplicatoinConfig().get_config_item('config', 'download_history_process_num'))
            con_exec(self._download_history_data_fast, lines, process_num)
        else:
            raise Exception('Unexpect Error')
        print time.time() - start_time

    def single_stock_indexor(self, code):
        file_name = code + '.csv'
        csv_reader = csv.reader(open(Dealor.history_path + os.path.sep + file_name, 'r'))
        csv_reader.next()

        settlements = []
        day_lowest = []
        day_highest = []
        for row in csv_reader:
            if float(row[3]) < precision:
                continue
            settlements.insert(0, float(row[3]))
            day_lowest.insert(0, float(row[5]))
            day_highest.insert(0, float(row[4]))

        indexor = Indexor()
        k_value, d_value, j_value = indexor.calc_kdj(settlements, day_lowest, day_highest)
        try:
            diff, dea9, macd = indexor.cal_macd(settlements, day_lowest, day_highest)
        except:
            print code,'code',settlements
            raise Exception('Unexpected Exception')
        return k_value, d_value, j_value, diff, dea9, macd

    def indexor_filter(self):
        lines = None
        stock_detail = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        with open(stock_detail, 'r') as f:
            lines = f.readlines()

        f1 = open(ApplicatoinConfig().get_config_item('stock_file', 'macd_filter'), 'w')
        f2 = open(ApplicatoinConfig().get_config_item('stock_file', 'kdj_filter'), 'w')
        f3 = open(ApplicatoinConfig().get_config_item('stock_file', 'all_indexor_filter'), 'w')
        for line in lines:
            self.logger.debug('cal single stock indexor ' + code)
            code = line.split('\t')[2]
            k_value, d_value, j_value, diff, dea9, macd = self.single_stock_indexor(code)
            macd_flag = False
            kdj_flag = False
            if self._gold_branch(diff, dea9):
                f1.write(code + '\n')
                macd_flag = True
            if self._gold_branch(k_value, d_value):
                f2.write(code + '\n')
                kdj_flag = True
            if macd_flag and kdj_flag:
                f3.write(code + '\n')
            f1.flush()
            f2.flush()
            f3.flush()

        f1.close()
        f2.close()
        f3.close()

    def _gold_branch(self, fast_line, slow_line):
        if fast_line[-1] > slow_line[-1]:
            if len(fast_line) < 5:
                return True
            for i in range(-5, 0):
                if fast_line[i] < slow_line[i]:
                    return True
            return False
        else:
            return False

class Indexor(object):
    def __init__(self):
        self.logger = logging.getLogger('default')

    def _ema2 (self, settlements, low, high, day):
        value_list = []
        for i in range(0,len(settlements)):
            value_list.append((settlements[i] * 2 + high[i] + low[i]) / 4)
        ratio = float (2) / (day + 1)
        ema_list = [ value_list[0] * ratio]
        for i in range (1, len(value_list)):
            ema_tmp  = (1 - ratio) * ema_list[i - 1] + ratio * value_list[i]
            ema_list.append (ema_tmp)
        return ema_list

    def _ema (self, value_list, day):
        ratio = float (2) / (day + 1)
        ema_list = [ value_list[0] * ratio]
        for i in range (1, len(value_list)):
            ema_tmp  = (1 - ratio) * ema_list[i - 1] + ratio * value_list[i]
            ema_list.append (ema_tmp)
        return ema_list

    def cal_macd(self, settlements, low, high):
        ema26 = self._ema(settlements, 26)
        ema12 = self._ema(settlements, 12)

        diff = []
        for i in range(len(settlements)):
            diff.append(ema12[i] - ema26[i])
        dea9 = self._ema(diff, 9)

        for i in range(len(dea9)):
            diff[i] = round(diff[i], 2)
        for i in range(len(dea9)):
            dea9[i] = round(dea9[i], 2)
        macd = []
        for i in range(len(settlements)):
            macd.append(2 * (diff[i] - dea9[i]))
        return diff, dea9, macd

    def _rsv(self, settlements, day_lowest, day_highest, day):

        rsv_list = list([50 for i in range(day - 1)])

        for i in range(day - 1, len(settlements)):
            if i == 220:
                pass
            n_lowest = min(*day_lowest[i - day + 1:i + 1])
            n_highest = max(*day_highest[i - day + 1:i + 1])
            if settlements[i] < precision:
                raise Exception('settlements i is zero, index: ' + str(i))
            try:
                if fabs(settlements[i] - n_lowest) < precision:
                    rsv_list.append(1.0)
                else:
                    rsv_list.append((settlements[i] - n_lowest) / (n_highest - n_lowest) * 100)
            except Exception, e:
                print settlements[i], n_lowest, n_highest, i
                print e.message
                sys.exit()

        return rsv_list

    def calc_kdj(self, settlements, day_lowest, day_highest):
        rsv_list = self._rsv(settlements, day_lowest, day_highest, 9)
        ratio = 1.0 / 3.0

        k_value = [50]
        d_value = [50]
        j_value = [50]
        try:
            for i in range(1, len(settlements)):
                if rsv_list[i] < precision:
                    raise Exception('rsv_list i less than precision, index: ' + str(i) + ' value ' + str(rsv_list[i]))
                k_value.append(round(ratio * rsv_list[i] + (1 - ratio) * k_value[i - 1], 2))
                d_value.append(round(ratio * k_value[i] + (1 - ratio) * d_value[i - 1], 2))
                j_value.append(round(3 * k_value[i] - 2 * d_value[i], 2))
        except Exception, e:
            print i, e.message

        return k_value, d_value, j_value
