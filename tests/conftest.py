#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   conftest.py
@Time    :   2024/10/17 23:52:28
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Pytest config file
'''


import logging
import os
import sys


sys.path.append(os.path.join('src'))
logging.captureWarnings(True)


def pytest_configure(config):
    config.option.log_level = "WARNING"
