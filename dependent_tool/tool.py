import os
import datetime

def del_none_data():
    path_pre = '../data_dir/day_history_data'
    stocks = os.listdir(path_pre)

    for stock in stocks:
        day_datas = os.listdir('%s/%s' % (path_pre, stock))
        for day_data in day_datas:
            file_path = '%s/%s/%s' % (path_pre, stock, day_data)
            if os.path.getsize(file_path) == 5:
                os.remove(file_path)

def rename_none_data():
    path_pre = '../data_dir/day_history_data'
    stocks = os.listdir(path_pre)

    for stock in stocks:
        day_datas = os.listdir('%s/%s' % (path_pre, stock))
        for day_data in day_datas:
            file_path = '%s/%s/%s' % (path_pre, stock, day_data)
            if os.path.getsize(file_path) == 5:
                os.rename(file_path, file_path + '_none')

def del_old_data(year, month, day):
    oldest = datetime.date(year, month, day)
    path_pre = '../data_dir/day_history_data'
    stocks = os.listdir(path_pre)

    for stock in stocks:
        day_datas = os.listdir('%s/%s' % (path_pre, stock))
        for day_data in day_datas:
            datetuple = day_data.split('_')[1].split('-')
            cur_date = datetime.date(int(datetuple[0]), int(datetuple[1]), int(datetuple[2].split('.')[0]))
            if cur_date < oldest:
                file_path = '%s/%s/%s' % (path_pre, stock, day_data)
                os.remove(file_path)


del_old_data(2017, 10, 01)