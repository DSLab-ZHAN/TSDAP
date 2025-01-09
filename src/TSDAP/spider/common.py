#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   common.py
@Time    :   2024/10/25 02:38:48
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Spider Common Objects
'''


import ctypes

from enum import IntEnum
from multiprocessing.managers import SyncManager


class SpiderCodes(IntEnum):
    STATUS_SUCCESS = 0
    STATUS_EXIT_UNEXPECTED = 1
    STATUS_DOG_TRIGGER = 2


class ContainerStatus(IntEnum):
    CREATED = 0
    RUNNING = 1
    TIMER_WAITING = 2
    TERMINATED = -1


class SpiderShares():
    def __init__(self, manager: SyncManager) -> None:
        self.is_stop_event = manager.Event()

        self.is_daemon = manager.Value(ctypes.c_bool, False)
        self.is_dog_trigger = manager.Value(ctypes.c_bool, False)

        self.is_logs = manager.Value(ctypes.c_bool, False)
        self.logs = manager.Value(ctypes.c_wchar_p, "")

        self.spider_db_dir = manager.Value(ctypes.c_wchar_p, "")

        self.ret_code = manager.Value(ctypes.c_byte, 0)
