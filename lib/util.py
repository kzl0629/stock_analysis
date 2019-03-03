# -*- coding:utf-8 -*-
__all__ = ['processNum', 'http_timeout', 'http_retry_times', 'conExecProxy', 'conCreateObj']

import logging
import json
import time
from multiprocessing import Pool
from gevent.pool import Pool as GEventPool
import socket
import os
import gevent

import requests
import etcd3
import redis

from lib.config import ApplicatoinConfig
from lib.singletan import Singletan

processNum = int(ApplicatoinConfig().getConfigItem('config', 'default_process_num'))
http_timeout = float(ApplicatoinConfig().getConfigItem('config', 'http_timeout'))
http_retry_times = int(ApplicatoinConfig().getConfigItem('config', 'retry_times'))
processPool = None
geventPool = None

def initProcessPool():
    global processPool
    if processPool == None:
        processPool = Pool(processes=processNum)

def initGEventPool():
    from gevent import monkey
    monkey.patch_all()
    global geventPool
    if geventPool == None:
        geventPool = GEventPool(processNum)

def processProxy(cls, funcName, args):
    result = None
    logger = logging.getLogger('default')
    logger.info('function %s started' % (funcName))
    try:
        result = getattr(cls, funcName)(*args)
    except Exception,e:
        logger.error('processProxy %s, %s, %s' % (funcName, e, str(args)))
        raise e
    return result

def conExecProxy(obj, funcName, args):
    result = None
    logger = logging.getLogger('default')
    logger.info('conExec start one request')
    try:
        result = obj.__getattribute__(funcName)(*args)
    except Exception,e:
        logger.error('conExecProxy %s, %s' % (e, str(args)))
        raise e

    return result

def conCreateObj(cls, args):
    return cls(*args)

def conExec(function, listArgs, processes=processNum):
    resList = conExecWithoutRet(function, listArgs, processes=processNum)

    #get result
    resultDetailsList = []
    for i in range(len(listArgs)):
        resultDetails = resList[i].get()
        resultDetailsList.append(resultDetails)
    return resultDetailsList

def conExecWithoutRet(function, listArgs, processes=processNum):
    logger = logging.getLogger('default')

    initProcessPool()

    # call funcion or instance method or create obj, listArgs format:[ [function_arg1, function_arg2,], [function_arg1, function_arg2,] ]
    resList = []
    res = None
    for item in listArgs:
        if type(function).__name__ == 'function':
            if type(item).__name__ == 'list':
                args = tuple(item)
            else:
                args = (item,)
            res = processPool.apply_async(function, args)
        elif type(function).__name__ == 'instancemethod':
            # one object calls the same instancemethod parallel
            res = processPool.apply_async(conExecProxy, (function.im_self, function.__name__, item,))
        elif type(function).__name__ == 'str':
            # differnt objects calls the same instancemethod parallel，arg format: object, func_name, args
            res = processPool.apply_async(conExecProxy, (item[0], function, item[1:],))
        elif type(function).__name__ == 'type':
            # create obj parallel, arg format: class, init args
            res = processPool.apply_async(conCreateObj, (function, item))
        else:
            raise Exception('unexpected function %s' % function)
        logger.info('conExec submit one request')
        resList.append(res)
    return resList

def conExecWithoutRet2(function, listArgs, processes=processNum):
    logger = logging.getLogger('default')
    initProcessPool()

    # call funcion or instance method or create obj, listArgs format:[ [function_arg1, function_arg2,], [function_arg1, function_arg2,] ]
    resList = []
    res = None
    for item in listArgs:
        if type(function).__name__ == 'function':
            if type(item).__name__ == 'list':
                args = tuple(item)
            else:
                args = (item,)
            res = processPool.apply_async(function, args)
        elif type(function).__name__ == 'instancemethod':
            # one object calls the same instancemethod parallel
            res = processPool.apply_async(conExecProxy, (function.im_self, function.__name__, item,))
        elif type(function).__name__ == 'str':
            # differnt objects calls the same instancemethod parallel，arg format: object, func_name, args
            res = processPool.apply_async(conExecProxy, (item[0], function, item[1:],))
        elif type(function).__name__ == 'type':
            # create obj parallel, arg format: class, init args
            res = processPool.apply_async(conCreateObj, (function, item))
        else:
            raise Exception('unexpected function %s' % function)
        logger.info('conExec submit one request')
        resList.append(res)
    return resList

def request_post(url, jsonInput, headers={}, timeout=http_timeout):
    logger = logging.getLogger('default')
    jsonStr = ''
    if type(jsonInput).__name__ == 'dict':
        jsonStr = json.dumps(jsonInput)
    elif type(jsonInput).__name__ == 'str':
        jsonStr =jsonInput
    else:
        raise Exception('json type is error %s' % type(jsonInput))

    for i in range(0, http_retry_times):
        try:
            headers['Content-Type'] = 'application/json'
            logger.info('request post url:%s data:%s ' % (url, jsonStr[0:1000]))
            response = requests.post(url, data=jsonStr, headers=headers, timeout=timeout)
            break
        except requests.exceptions.Timeout, e:
            logger.info('Connect timeout url:%s retry times:%' % (url, i))
            continue
        except Exception,e:
            logger.error('request_post error url:%s retry times:%s msg: %s' % (url, i, e))
            raise e
    content = response.content
    try:
        content = json.loads(content)
    except:
        pass

    return response.status_code, content

def request_get(url, headers={}, timeout=http_timeout):
    logger = logging.getLogger('default')
    response = None
    for i in range(0, http_retry_times):
        try:
            response = requests.get(url,  headers=headers, timeout=timeout)
            logger.info('request get url:%s ' % (url,))
            break
        except requests.exceptions.Timeout, e:
            logger.info('Connect timeout url:%s retry times:%s' % (url, i))
            time.sleep(1)
            continue
        except Exception,e:
            logger.error('request_get error url:%s retry times:%s msg: %s' % (url, i, e))
            raise e

    if response == None:
        msg = 'request_get url error, url:%s retry times:%s' % (url, i)
        logger.error(msg)
        raise Exception(msg)
    return response.status_code, response.content

def createServerSocket(serverAddress):
    logger = logging.getLogger('default')
    # Make sure the socket does not already exist
    try:
        if os.path.exists(serverAddress):
            os.unlink(serverAddress)
    except OSError, e:
        if os.path.exists(serverAddress):
            msg = 'unlink server_address error:%s, msg:%s' % (serverAddress, e)
            logger.error(msg)
            raise e

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(serverAddress)
    logger.info('bind server_address %s' % (serverAddress))
    sock.listen(5)

    return sock


class EtcdV3(object):
    __metaclass__ = Singletan

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.connEtcd()

    def getConn(self):
        return  self.conn

    def connEtcd(self):
        ac = ApplicatoinConfig()
        if self.host == None:
            self.host = ac.getConfigItem('env_var', 'etcd_host')
        if self.port == None:
            self.port = ac.getConfigItem('env_var', 'etcd_port')
        try:
            self.conn = etcd3.client(self.host, self.port)
        except Exception,e:
            logger = logging.getLogger('default')
            logger.error('connect etcd error host:%s, port:%s' % (self.host, self.port))
            raise e


class RedisClient(object):
    __metaclass__ = Singletan

    def __init__(self, host=None, port=None, db=None):
        self.host = host
        self.port = port
        self.db = db
        self.connRedis()

    def connRedis(self):
        ac = ApplicatoinConfig()
        if self.host == None:
            self.host = ac.getConfigItem('env_var', 'redis_host')
        if self.port == None:
            self.port = ac.getConfigItem('env_var', 'redis_port')
        if self.db == None:
            self.db = ac.getConfigItem('env_var', 'redis_db')

        try:
            self.redisConn = redis.StrictRedis(host=self.host, port=self.port, db=self.db)
        except Exception,e:
            logger = logging.getLogger('default')
            logger.error('connect redis error host:%s, port:%s, db:%s' % (self.host, self.port, self.db))
            raise e

    def getConn(self):
        return  self.redisConn

def conGevent(func, list_args):
    initGEventPool()

    retItor = geventPool.imap_unordered(func, list_args)
    resultList = []
    for ret in retItor:
        resultList.append(ret)
    return resultList
