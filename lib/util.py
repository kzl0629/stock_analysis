# -*- coding:utf-8 -*-
__all__ = ['proxies', 'auth', 'process_num', 'http_timeout']

import requests
import logging
from requests import Response
from requests.auth import HTTPProxyAuth
from multiprocessing import Pool

from lib.config import ApplicatoinConfig
proxies ={"http":"http://proxy.huawei.com:8080","https":"https://proxy,huawei.com:8080"}
auth = HTTPProxyAuth('k00399859', 'qgmmztmn_6')
proxies = None
auth = None

process_num = int(ApplicatoinConfig().get_config_item('config', 'default_process_num'))
http_timeout = float(ApplicatoinConfig().get_config_item('config', 'http_timeout'))


def request_timeout(url, timout=http_timeout):
    logger = logging.getLogger('default')
    while True:
        try:
            response = Response()
            if proxies is not None:
                response = requests.get(url, proxies=proxies, auth=auth)
            else:
                response = requests.get(url, timeout=timout)
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

