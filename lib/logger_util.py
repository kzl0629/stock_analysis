# -*- coding:utf-8 -*-

import os
import shutil
import datetime
import logging.config

from lib.config import  ApplicatoinConfig


def initLog():
    backupLogFile()
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'supress_abs_warn' : True,
        'formatters': {
            'verbose': {
                'format': "[%(asctime)s]  %(levelname)s [%(filename)s:%(lineno)s:%(funcName)s]:%(process)d:%(thread)d %(message)s",
                'datefmt': ApplicatoinConfig().getConfigItem('config', 'datetime_format')
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
                'backupCount': 100,
                # If delay is true,
                # then file opening is deferred until the first call to emit().
                'filename': ApplicatoinConfig().getConfigItem('config', 'log_file'),
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'default': {
                'handlers': [ApplicatoinConfig().getConfigItem('config', 'log_handler'),],
                'level': ApplicatoinConfig().getConfigItem('config', 'log_level'),
            },
        }
    })

def clearLogFile():
    logFile = ApplicatoinConfig().getConfigItem('config', 'log_file')
    if os.path.exists(logFile):
        os.remove(logFile)

def backupLogFile():
    logFile = ApplicatoinConfig().getConfigItem('config', 'log_file')
    if os.path.isfile(logFile):
        timestamp = datetime.datetime.now().__str__().split('.')[0].replace(' ', '_').replace(':', '_')
        shutil.move(logFile, logFile + '_' + timestamp)

    basePath = os.path.dirname(logFile)

    tmp = os.listdir(basePath)
    dirList = []
    for i in range(0, len(tmp)):
        if tmp[i].startswith(os.path.basename(logFile + '_')):
            dirList.append(tmp[i])
    if len(dirList) > 3:
        dirList.sort()
        for item in dirList[0:-3]:
            os.remove(basePath + os.path.sep + item)
