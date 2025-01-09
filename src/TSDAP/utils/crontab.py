#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   crontab.py
@Time    :   2024/10/28 01:01:26
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Decode cron expression
'''


from datetime import datetime, timedelta
from itertools import product
from threading import Timer
from typing import Any, Callable, Iterable, List, Mapping, Optional, Union


def parse_cron_field(field: str, min_val: int, max_val: int) -> List:
    values = set()

    # `*` express any value
    if (field == '*'):
        return list(range(min_val, max_val + 1))

    # `,` express many values
    for part in field.split(','):
        # `/` express step value
        if '/' in part:
            base, step = part.split('/')
            step = int(step)

            if base == '*':
                base_range = range(min_val, max_val + 1)
            elif '-' in base:  # 处理范围格式如 '5-10'
                start, end = map(int, base.split('-'))
                base_range = range(start, end + 1)
            else:
                base_range = range(int(base), max_val + 1)

            values.update(base_range[::step])

        # `-` express range
        elif '-' in part:
            start, end = map(int, part.split('-'))
            values.update(range(start, end + 1))

        # Single value
        else:
            values.add(int(part))

    return sorted(values)


def get_next_run(cron_expression: str) -> Union[datetime, None]:
    now = datetime.now()
    second_field, minute_field, hour_field, \
        day_field, month_field, weekday_field = cron_expression.split()

    seconds = parse_cron_field(second_field, 0, 59)
    minutes = parse_cron_field(minute_field, 0, 59)
    hours = parse_cron_field(hour_field, 0, 23)
    days = parse_cron_field(day_field, 1, 31)
    months = parse_cron_field(month_field, 1, 12)
    weekdays = parse_cron_field(weekday_field, 0, 6)  # 0=Sunday | 6=Saturday

    # Search next match time
    for day_offset in range(0, 365):
        potential_time = now + timedelta(days=day_offset)

        # Check Month, Day, Week
        if (
            potential_time.month in months
            and potential_time.day in days
            and ((potential_time.weekday() + 1) % 7) in weekdays
        ):

            for hour, minute, second in product(hours, minutes, seconds):
                next_time = potential_time.replace(hour=hour, minute=minute, second=second, microsecond=0)
                if (next_time > now):
                    return next_time

    return None


def cron_to_timer(cron_expression: str,
                  task: Callable,
                  args: Optional[Iterable[Any]] = None,
                  kwargs: Optional[Mapping[str, Any]] = None) -> Union[Timer, None]:

    next_run = get_next_run(cron_expression)
    if (next_run is None):
        # Log or print
        print("Cannot analysis cron expression.")
        return None

    sec_delay = (next_run - datetime.now()).total_seconds()
    timer = Timer(sec_delay, task, args=args, kwargs=kwargs)

    return timer
