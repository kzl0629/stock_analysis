# -*- coding:utf-8 -*-
__all__ = ['process_num', 'http_timeout']

import requests
import logging
import datetime
from multiprocessing import Pool

import gevent
from lib.config import ApplicatoinConfig

process_num = int(ApplicatoinConfig().get_config_item('config', 'default_process_num'))
http_timeout = float(ApplicatoinConfig().get_config_item('config', 'http_timeout'))

def request_timeout(url, timout=http_timeout):
    logger = logging.getLogger('default')
    while True:
        try:
            start_time = datetime.datetime.now()
            logger.debug('request time:\t' + url + '\t' + str(start_time))
            response = requests.get(url, timeout=timout)
            logger.debug('request time:\t' + url + '\t' + str(datetime.datetime.now() - start_time))

            break
        except requests.exceptions.Timeout, e:
            logger.info('Connect timeout ' + url)
            continue
        except Exception,e:
            logger.error('request_timeout error: ' + str(e.message) + 'url: ' + url)
            raise e

    return response


def con_exec_proxy(obj, func_name, arg):
    return obj.__getattribute__(func_name)(arg)

def con_exec(func, list_args, processes=process_num):
    logger = logging.getLogger('default')

    res_list = []
    pool = Pool(processes=processes)
    for item in list_args:
        res = pool.apply_async(con_exec_proxy, (func.im_self, func.__name__, item,))
        logger.info(con_exec.__name__ + ' submit request:\t' + str(item))
        res_list.append(res)

    result_details_list = []
    for i in range(len(list_args)):
        result_details = res_list[i].get()
        logger.info(con_exec.__name__ + ' get return: ' + str(result_details))
        result_details_list.append(result_details)
    return result_details_list

def con_net_req(func, list_args):
    logger = logging.getLogger('default')

    handler_list = []
    for item in list_args:
        handler = gevent.spawn(func, item)
        logger.info('con_net_req submit request:\t' + str(item))
        handler_list.append(handler)

    gevent.joinall(handler_list)
    result_details_list = []
    for i in range(len(list_args)):
        result_details = handler_list[i].value
        logger.info('con_net_req get return: ' + str(result_details))
        result_details_list.append(result_details)
    return result_details_list


def con_with_thread():
    pass

def max ( *args):
    size = len(args)
    if args == None or size == 0:
        raise Exception("max args is None or size == 0")

    if size == 1:
        return args[0]

    tmp = args[0]
    for item in args:
        if item > tmp:
            tmp = item

    return tmp


def min(*args):
    size = len(args)
    if args == None or size == 0:
        raise Exception("min args is None or size == 0")

    if size == 1:
        return args[0]
    tmp = args[0]
    for item in args:
        if item < tmp:
            tmp = item
    return tmp

