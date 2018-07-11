# -*- coding:utf-8 -*-

import os
import shutil
import datetime
import logging.config

from lib.config import  ApplicatoinConfig


def init():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'supress_abs_warn' : True,
        'formatters': {
            'verbose': {
                'format': "[%(asctime)s]  %(levelname)s [%(filename)s:%(lineno)s:%(funcName)s]:%(process)d:%(thread)d %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
            'simple2': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'logging.NullHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'cloghandler.ConcurrentRotatingFileHandler',
                # 当达到10MB时分割日志
                'maxBytes': 1024 * 1024 * 10,
                # 最多保留50份文件
                'backupCount': 50,
                # If delay is true,
                # then file opening is deferred until the first call to emit().
                'filename': ApplicatoinConfig().get_config_item('config', 'log_file'),
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'default': {
                'handlers': ['file',],
                'level': 'DEBUG',
            },
        }
    })

def clear_log_file():
    log_file = ApplicatoinConfig().get_config_item('config', 'log_file')
    if os.path.exists(log_file):
        os.remove(log_file)

def backup_log_file():
    log_file = ApplicatoinConfig().get_config_item('config', 'log_file')
    if os.path.isfile(log_file):
        timestamp = datetime.datetime.now().__str__().split('.')[0].replace(' ', '_').replace(':', '_')
        shutil.move(log_file, log_file + '_' + timestamp)

    base_path = os.path.dirname(log_file)
    tmp = os.listdir(base_path)
    dir_list = []
    for i in range(0, len(tmp)):
        if tmp[i].startswith(os.path.basename(log_file + '_')):
            dir_list.append(tmp[i])
    if len(dir_list) > 3:
        dir_list.sort()
        for item in dir_list[0:-3]:
            os.remove(base_path + os.path.sep + item)
