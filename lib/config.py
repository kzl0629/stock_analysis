# -*- coding:utf-8 -*-

import os
import ConfigParser

class singletan(type):
    def __init__(self, name, father, attr):
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance == None:
            self.instance = super(singletan, self).__call__(*args,**kwargs)
        return self.instance

class ApplicatoinConfig(object):
    __metaclass__ = singletan
    config_path = '/../resource/config.ini'

    def __init__(self):
        self.cf = ConfigParser.ConfigParser()

    def list_config(self):
        pass

    def _read_config(self):
        cur_path = os.path.dirname(__file__)
        config_path = cur_path + ApplicatoinConfig.config_path
        self.cf.read(config_path)

    def get_config_item(self, section, key):
        self._read_config()
        return self.cf.get(section, key)
