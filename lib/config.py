# -*- coding:utf-8 -*-

import os
import ConfigParser
from lib.singletan import Singletan


class ApplicatoinConfig(object):
    __metaclass__ = Singletan
    configPath = os.path.dirname(__file__) + '/../resource/config.ini'

    def __init__(self):
        self.cf = ConfigParser.ConfigParser()
        self._readConfig()

    def _readConfig(self):
        self.cf.read(ApplicatoinConfig.configPath)

    def _updateConfig(self, section, option, value=None):
        self._readConfig()
        self.cf.set(section, option, value)
        with open(ApplicatoinConfig.configPath, 'w') as f:
            self.cf.write(f)

    def getConfigItem(self, section, key):
        return self.cf.get(section, key)
