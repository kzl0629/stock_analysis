from lib.logger_util import init, backup_log_file
from lib.config import ApplicatoinConfig
from stock import Dealor


#clear_log_file()
backup_log_file()
init()

stkDealor = Dealor()

# stkDealor._download_history_data('600477')
#
# stkDealor.update_stock_list()
#
# stkDealor.stocks_to_txt()
stkDealor.update_hitory_data('slow')
# stkDealor.filter(0,100,0,100,1,100,50, None)

stkDealor.indexor_filter()

# k_value, d_value, j_value, diff, dea9, macd = stkDealor.single_stock_indexor('600477')
#
# print k_value[-5:], d_value[-5:], diff[-5:], dea9[-5:]
