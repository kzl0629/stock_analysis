from lib.logger_util import init, backup_log_file
from stock import Dealor
import datetime
from lib.util import con_net_req
#clear_log_file()
backup_log_file()
init()

stkDealor = Dealor()


# print stock_details_list
# stkDealor.stocks_to_txt()
# stkDealor.update_hitory_data()

# stkDealor.filter(0, 100, 0, 100, 10, 50)
#
# stkDealor.indexor_filter('history_data')

result = stkDealor.single_stock_indexor('002830', 'resource/history_data')
print result[-1]
print 'over'
