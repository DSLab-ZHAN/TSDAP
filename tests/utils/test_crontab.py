#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_crontab.py
@Time    :   2024/11/04 15:02:55
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Test file of crontab
'''


import TSDAP.utils.crontab as crontab

from threading import Timer
from datetime import datetime
from random import randint


class TestCrontab:
    def test_parse_cron_field(self):
        assert crontab.parse_cron_field('*', 0, 59) == list(range(0, 60))
        assert crontab.parse_cron_field('0,15,30,45', 0, 59) == [0, 15, 30, 45]
        assert crontab.parse_cron_field('0-5', 0, 59) == [0, 1, 2, 3, 4, 5]
        assert crontab.parse_cron_field('*/15', 0, 59) == [0, 15, 30, 45]
        assert crontab.parse_cron_field('0/15', 0, 59) == [0, 15, 30, 45]
        assert crontab.parse_cron_field('*', 0, 59) == list(range(0, 60))
        assert crontab.parse_cron_field('0,15,30,45', 0, 59) == [0, 15, 30, 45]
        assert crontab.parse_cron_field('0-5', 0, 59) == [0, 1, 2, 3, 4, 5]
        assert crontab.parse_cron_field('*/15', 0, 59) == [0, 15, 30, 45]
        assert crontab.parse_cron_field('5-10/2', 0, 59) == [5, 7, 9]
        assert crontab.parse_cron_field('1,2,3-5,10-12/2', 0, 59) == [1, 2, 3, 4, 5, 10, 12]
        assert crontab.parse_cron_field('*/10', 0, 59) == [0, 10, 20, 30, 40, 50]
        assert crontab.parse_cron_field('0-59/20', 0, 59) == [0, 20, 40]
        assert crontab.parse_cron_field('0-59/30', 0, 59) == [0, 30]
        assert crontab.parse_cron_field('*/5', 0, 59) == [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

    def test_get_next_run(self):
        now = datetime.now()

        second = randint(0, 59)
        minute = randint(0, 59)
        hour = randint(0, 23)
        day = randint(1, 28)
        month = randint(1, 12)

        cron_expression = f"{second} {minute} {hour} {day} {month} *"
        next_run = crontab.get_next_run(cron_expression)
        assert next_run is not None
        assert next_run > now

        cron_expression = f"{second} {minute} {hour} {day} {month} {randint(0, 6)}"
        next_run = crontab.get_next_run(cron_expression)
        if (next_run is None):
            assert next_run is None

    def dummy_task(self):
        print("Task executed")

    def test_cron_to_timer(self):
        now = datetime.now()
        cron_expression = f"{(now.second + 1) % 60} {now.minute} {now.hour} {now.day} {now.month} {now.weekday()}"
        timer = crontab.cron_to_timer(cron_expression, self.dummy_task)
        assert timer is not None
        assert isinstance(timer, Timer)
        timer.cancel()

        cron_expression = f"{(now.second + 1) % 60} {now.minute} {now.hour} {now.day} {now.month} {randint(0, 6)}"
        timer = crontab.cron_to_timer(cron_expression, self.dummy_task)
        if (timer is None):
            assert timer is None
