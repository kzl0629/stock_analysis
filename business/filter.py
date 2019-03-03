import os
import csv

from lib.config import ApplicatoinConfig
from business.indexor import Caculator

class Selector(object):
    def __init__(self):
        self.ac = ApplicatoinConfig()
        self.precision = float(self.ac.get_config_item('config', 'precision'))
    def single_stock_indexor(self, code, data_dir):
        file_name = code + '.csv'
        csvReader = csv.reader(open(data_dir + os.path.sep + file_name, 'r'))
        csvReader.next()

        settlements = []
        day_lowest = []
        day_highest = []
        for row in csvReader:
            if float(row[3]) < self.precision:
                continue
            settlements.append(float(row[3]))
            day_lowest.append(float(row[5]))
            day_highest.append(float(row[4]))
        if len(settlements) == 0:
            return [], [], [], [], [], [], []

        calculator = Caculator()
        k_value, d_value, j_value = calculator.calc_kdj(settlements, day_lowest, day_highest)
        try:
            diff, dea9, macd = calculator.cal_macd(settlements, day_lowest, day_highest)
        except:
            print code,'code',settlements
            raise Exception('Unexpected Exception')

        ltp = calculator.calc_ltp(settlements)
        return k_value, d_value, j_value, diff, dea9, macd, ltp

    def indexor_filter(self, code_list_src, filter='stock_detail'):
        #map code to details
        stock_detail = self.ac.get_config_item('stock_file', filter)
        with open(stock_detail, 'r') as f:
            detail_lines = f.readlines()
        code_dtl_map = {}
        for i in range(0, len(detail_lines)):
            code = detail_lines[i].split(',')[1]
            code_dtl_map[code] = detail_lines[i]

        lines = None
        dir = self.ac.get_config_item('stock_file', 'history_path')
        if code_list_src == 'stock_detail':
            lines = list(code_dtl_map.keys())
        elif code_list_src == 'history_data':
            lines = os.listdir(dir)
            for i in range(0, len(lines)):
                lines[i] = lines[i].split('.')[0]
        else:
            raise Exception('Unexpected Error')

        f1 = open(self.ac.get_config_item('stock_file', 'macd_filter'), 'w')
        f2 = open(self.ac.get_config_item('stock_file', 'kdj_filter'), 'w')
        f3 = open(self.ac.get_config_item('stock_file', 'all_indexor_filter'), 'w')
        f4 = open(self.ac.get_config_item('stock_file', 'ltp_filter'), 'w')

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
        filter_file = self.ac.get_config_item('stock_file', '%s_filter' % indexor_list[0])
        fd = open(filter_file, 'r')
        result_set = set(fd.readlines())
        for i in range(1, len(indexor_list)):
            fd = open(self.ac.get_config_item('stock_file', '%s_filter' % indexor_list[i]), 'r')
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
