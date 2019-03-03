import logging
import sys
from math import fabs

from lib.config import ApplicatoinConfig

class Caculator(object):
    def __init__(self):
        self.logger = logging.getLogger('default')

        self.precision = float(ApplicatoinConfig().get_config_item('config', 'precision'))

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
            if settlements[i] < self.precision:
                raise Exception('settlements i is zero, index: ' + str(i))
            try:
                if fabs(settlements[i] - n_lowest) < self.precision:
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
                if rsv_list[i] < self.precision:
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