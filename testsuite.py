#coding=utf8

import unittest
from testcase.testdata import TestData
from lib.logger_util import initLog

initLog()

suite = unittest.TestSuite()
# suite.addTest(TestData('testLastestKData'))
# suite.addTest(TestData('testBlAV'))
suite.addTest(TestData('testDayDataFailure'))
# 执行测试
runner = unittest.TextTestRunner()
runner.run(suite)
