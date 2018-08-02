from lib.logger_util import init, backup_log_file
from stock import Dealor
import datetime

#clear_log_file()
backup_log_file()
init()

stkDealor = Dealor()


# stkDealor.update_stock_list()
# stock_details_list = con_net_req(stkDealor._list_details, ['sz002556', 'sz002557' ])
# stkDealor.stocks_to_txt()
stkDealor.update_hitory_data()

# stkDealor.filter(0,100,0,100,1,100,50, None)


stkDealor.indexor_filter('history_data',
                        'resource/history_data')
# stkDealor.conjun_indexor('macd', 'ltp', 'kdj')
# stkDealor._download_history_data('sz000679')
# k_value, d_value, j_value, diff, dea9, macd, ltp = stkDealor.single_stock_indexor('000063','resource/history_data')
#
# print ltp
#

print 'over'
