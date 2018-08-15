# -*- coding:utf-8 -*-
__all__ = ['precision']

import sys
import os
import re
import time
import logging
import csv
from math import fabs
import datetime

# from gevent import monkey
import tushare
import requests

from lib.util import max, min, con_net_req
from lib.config import ApplicatoinConfig

# monkey.patch_all()
precision = float(ApplicatoinConfig().get_config_item('config', 'precision'))


class Dealor(object):
    logger = logging.getLogger('default')
    history_path = ApplicatoinConfig().get_config_item('stock_file', 'history_path')
    day_history_path = ApplicatoinConfig().get_config_item('stock_file', 'day_history_path')

    def __init__(self):
        self.logger.info('start stock %s', str(datetime.datetime.now()))
        pass

    def filter(self, low_pe, hi_pe,
               low_pb, high_pb, low_value, high_value):

        stock_detail_file = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        with open(stock_detail_file, 'r') as f1:
            lines = f1.readlines()
            lines = map(lambda x: x.replace('\n', ''), lines)

        stock_detail_filtered = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail_filtered')
        with open(stock_detail_filtered, 'w') as f2:
            for line in lines:
                items = line.split(',')
                if len(items) < 7:
                    continue
                #item must be bigger than low and lower than high
                if low_pe != None and float(items[2]) < low_pe:
                    continue
                if hi_pe != None and float(items[2]) > hi_pe:
                    continue
                if low_pb != None and float(items[3]) < low_pb:
                    continue
                if high_pb != None and float(items[3]) > high_pb:
                    continue
                file_path = Dealor.history_path + os.path.sep + items[1] + '.csv'
                with open(file_path, 'r') as f:
                    file_size = os.path.getsize(file_path)
                    if file_size > 500:
                        f.seek(-500, 2)
                    stock_lines = f.readlines()
                    try:
                        close_value = stock_lines[-1].split(',')[3]
                    except Exception,e:
                        pass
                market_value = float(close_value) * float(items[4])
                if low_value != None and float(market_value) < low_value:
                    continue
                if high_value != None and float(market_value) > high_value:
                    continue

                f2.write(line + '\n')

    def stocks_to_txt(self):
        stock_detail_file = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        stock_detail = tushare.get_stock_basics()
        with open(stock_detail_file, 'w') as f:
            for item in stock_detail.iterrows():
                code = item[0]
                if code.startswith('60') or code.startswith('00'):
                    detail = item[1].tolist()
                    # '名称', '代码', '市盈率', '市净率', '流通股本' , '同比利润'+ '\n'
                    line = '%s,%s,%s,%s,%s,%s,%s\n' % (detail[0], code, detail[3], detail[13], detail[4], detail[18], detail[19] )
                    f.write(line)
            f.flush()

    def _download_history_data(self, stock):
        today = datetime.datetime.now().__str__().split(' ')[0]
        file_path = Dealor.history_path + os.path.sep + stock + '.csv'
        if os.path.exists(file_path) == False:
            data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=1000,)
            data.to_csv(file_path)
        else:
            with open(file_path, 'r') as f:
                file_size = os.path.getsize(file_path)
                if file_size > 500:
                    f.seek(-500, 2)
                lines = f.readlines()
                if len(lines) <= 2:
                    data = tushare.get_k_data(stock, start='1990-12-01', end=today, autype='qfq', retry_count=1000, )
                    data.to_csv(file_path)
                    return
                items = lines[-1].split(',')
                num = int(items[0])
                start_date = items[1]
            #append new data
            data = tushare.get_k_data(stock, start=start_date, end=today, autype='qfq', retry_count=1000,)
            with open(file_path, 'a') as f:
                itor = data.iterrows()
                itor.next()
                for row in itor:
                    num += 1
                    line = '%s,%s\n' % (num, ','.join(map(str,row[1].tolist())))
                    f.write(line)
                f.flush()

    def get_stock_codes(self):
        stock_detail = ApplicatoinConfig().get_config_item('stock_file', 'stock_detail')
        with open(stock_detail, 'r') as f1:
            lines = f1.readlines()
            lines = map(lambda x: x.split(',')[1], lines)

        return lines

    def update_hitory_data(self):
        stock_codes = self.get_stock_codes()

        if os.path.exists(Dealor.history_path) == False:
            os.mkdir(Dealor.history_path)

        start_time = time.time()
        self.logger.info('will download sotck list %s len %s' % (str(stock_codes), len(stock_codes)))
        con_net_req(self._download_history_data, stock_codes)

        print time.time() - start_time, 'update_hitory_data'


    def single_stock_indexor(self, code, data_dir):
        file_name = code + '.csv'
        csv_reader = csv.reader(open(data_dir + os.path.sep + file_name, 'r'))
        csv_reader.next()

        settlements = []
        day_lowest = []
        day_highest = []
        for row in csv_reader:
            if float(row[3]) < precision:
                continue
            settlements.append(float(row[3]))
            day_lowest.append(float(row[5]))
            day_highest.append(float(row[4]))
        if len(settlements) == 0:
            return [], [], [], [], [], [], []

        indexor = Indexor()
        k_value, d_value, j_value = indexor.calc_kdj(settlements, day_lowest, day_highest)
        try:
            diff, dea9, macd = indexor.cal_macd(settlements, day_lowest, day_highest)
        except:
            print code,'code',settlements
            raise Exception('Unexpected Exception')

        ltp = indexor.calc_ltp(settlements)
        return k_value, d_value, j_value, diff, dea9, macd, ltp

    def indexor_filter(self, code_list_src, filter='stock_detail'):
        #map code to details
        stock_detail = ApplicatoinConfig().get_config_item('stock_file', filter)
        with open(stock_detail, 'r') as f:
            detail_lines = f.readlines()
        code_dtl_map = {}
        for i in range(0, len(detail_lines)):
            code = detail_lines[i].split(',')[1]
            code_dtl_map[code] = detail_lines[i]

        lines = None
        dir = ApplicatoinConfig().get_config_item('stock_file', 'history_path')
        if code_list_src == 'stock_detail':
            lines = list(code_dtl_map.keys())
        elif code_list_src == 'history_data':
            lines = os.listdir(dir)
            for i in range(0, len(lines)):
                lines[i] = lines[i].split('.')[0]
        else:
            raise Exception('Unexpected Error')

        f1 = open(ApplicatoinConfig().get_config_item('stock_file', 'macd_filter'), 'w')
        f2 = open(ApplicatoinConfig().get_config_item('stock_file', 'kdj_filter'), 'w')
        f3 = open(ApplicatoinConfig().get_config_item('stock_file', 'all_indexor_filter'), 'w')
        f4 = open(ApplicatoinConfig().get_config_item('stock_file', 'ltp_filter'), 'w')

        for code in lines:
            self.logger.debug('cal single stock indexor ' + code)
            k_value, d_value, j_value, diff, dea9, macd, ltp = self.single_stock_indexor(code, dir)

            macd_flag = False
            kdj_flag = False
            ltp_flag = False

            if self._gold_branch(diff, dea9):
                if code_dtl_map.get(code):
                    f1.write(code_dtl_map.get(code))
                else:
                    f1.write(code + '\n')
                macd_flag = True
            if self._gold_branch(k_value, d_value):
                if code_dtl_map.get(code):
                    f2.write(code_dtl_map.get(code))
                else:
                    f2.write(code + '\n')
                kdj_flag = True
            if len(ltp) > 0 and ltp[-1][0] > 0:
                if code_dtl_map.get(code):
                    f4.write(code_dtl_map.get(code))
                else:
                    f4.write(code + '\n')
                ltp_flag = True

            if macd_flag and kdj_flag and ltp_flag:
                if code_dtl_map.get(code):
                    f3.write(code_dtl_map.get(code))
                else:
                    f3.write(code + '\n')
            f1.flush()
            f2.flush()
            f3.flush()

        f1.close()
        f2.close()
        f3.close()


    def conjun_indexor(self, *indexor_list):
        if indexor_list == None and len(indexor_list) == 1:
            return
        filter_file = ApplicatoinConfig().get_config_item('stock_file', '%s_filter' % indexor_list[0])
        fd = open(filter_file, 'r')
        result_set = set(fd.readlines())
        for i in range(1, len(indexor_list)):
            fd = open(ApplicatoinConfig().get_config_item('stock_file', '%s_filter' % indexor_list[i]), 'r')
            tmp_set = set(fd.readlines())
            result_set = result_set & tmp_set
        dir_name = os.path.dirname(filter_file)
        file_name = dir_name + os.path.sep + '_'.join(indexor_list) + '_filter.txt'
        with open(file_name, 'w') as f:
            f.writelines(result_set)
            f.flush()
        return


    def _gold_branch(self, fast_line, slow_line):
        if len(fast_line) == 0:
            return False

        if fast_line[-1] > slow_line[-1]:
            if len(fast_line) < 5:
                return True
            for i in range(-5, 0):
                if fast_line[i] < slow_line[i]:
                    return True
            return False
        else:
            return False

    def download_day_data(self, stock):
        stock_dir = '%s/%s' % (self.day_history_path, stock)
        if os.path.exists(stock_dir) is False:
            os.mkdir(stock_dir)

        lines = None
        with open('%s/%s.csv' % (self.history_path, stock)) as f:
            lines = f.readlines()

        del lines[0]
        over_flag = 0
        for line_num in range(len(lines) - 1, -1, -1):
            date = lines[line_num].split(',')[1]
            year = int(date.split('-')[0])
            if year <= 2016:
                continue

            stock_file_path = '%s/%s_%s.csv' % (stock_dir, stock, date)
            if os.path.exists(stock_file_path) is False:
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
                    with open(stock_file_path, 'w') as f:
                        f.write('none\n')
                        f.flush()
                    if over_flag > 365:
                        self.logger.info('last day data is none:%s %s' % (stock, date))
                        break
                    continue
                over_flag = 0
                df.to_csv(stock_file_path)
                self.logger.info('write day data:%s' % stock_file_path)
            else:
                self.logger.info('day data exists:%s' % stock_file_path)
                continue

        return

    def download_all_day_data(self):
        stock_codes = self.get_stock_codes()

        start_time = time.time()
        self.logger.info('will download_all_day_data stock list %s len %s' % (str(stock_codes), len(stock_codes)))
        for code in stock_codes:
            self.download_day_data(code)
        print time.time() - start_time, 'download_all_day_data'


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

    #calc new three price
    def calc_ltp(self, settlements):
        if len(settlements) <=3:
            return []
        if len(settlements) >= 100:
            settlements = settlements[-100:]

        direction = True

        result_list = [settlements[0]]
        result_list_loc = [0]
        low = 0
        high = 0

        for i in range(1,len(settlements)):
            # up direction
            if direction == True:
                #bigger than lowest
                if settlements[i] >= result_list[low] :
                    if settlements[i] <= result_list[high]:
                        continue
                    else:
                        result_list.append(settlements[i])
                        result_list_loc.append(i)
                        if high - low == 2:
                            low += 1
                        high += 1
                #smaller than lowest, direction will be changed
                else:
                    result_list.append(-settlements[i])
                    result_list_loc.append(i)
                    direction = False
                    high += 1
                    low = high
            # down direction
            else:
                # smaller than the highest
                if settlements[i] <= -result_list[high] :
                    if settlements[i] >= -result_list[low]:
                        continue
                    else:
                        result_list.append(-settlements[i])
                        result_list_loc.append(i)
                        if low - high == 2:
                            high += 1
                        low += 1
                #bigger than highest, direction will be changed
                else:
                    result_list.append(settlements[i])
                    result_list_loc.append(i)
                    direction = True
                    low += 1
                    high = low

        return zip(result_list, result_list_loc)