#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   dockerstyle.py
@Time    :   2024/10/31 04:47:32
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Generate some docker stylistic items
'''


import random
import time

from datetime import datetime


def generate_unique_docker_style_name():
    adjectives = [
        "agile", "brave", "calm", "daring", "eager", "fierce",
        "gentle", "happy", "jolly", "keen", "lazy", "mighty",
        "noble", "quick", "rustic", "sly", "tiny", "witty"
    ]

    animals = [
        "antelope", "bear", "cat", "dog", "elephant", "fox",
        "giraffe", "hawk", "iguana", "jellyfish", "kangaroo",
        "lion", "monkey", "octopus", "penguin", "quokka", "rabbit",
        "tiger", "unicorn", "vulture", "wolf", "zebra"
    ]

    adjective = random.choice(adjectives)
    animal = random.choice(animals)

    # 添加时间戳或随机数来确保唯一性
    unique_suffix = int(time.time() * 1000)  # 毫秒时间戳
    return f"{adjective}-{animal}-{unique_suffix}"


def human_readable_time_difference(past_time: datetime):
    now = datetime.now()
    diff = now - past_time

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    months = days / 30.44  # 平均每月天数
    years = months / 12

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif minutes < 60:
        return f"{int(minutes)} minutes ago"
    elif hours < 24:
        return f"{int(hours)} hours ago"
    elif days < 30:
        return f"{int(days)} days ago"
    elif months < 12:
        return f"{int(months)} months ago"
    else:
        return f"{int(years)} years ago"
