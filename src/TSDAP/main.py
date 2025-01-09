#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   main.py
@Time    :   2024/10/25 14:58:17
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   TSDAP Entrypoint
'''


import json
import multiprocessing
import os

from typing import Any, Dict

from console import MainConsole
from runtime import RuntimeContext as ctx
from spider import SpiderManager


def init_context():
    ctx.initialize()
    ctx.process_set_global("ROOT_ABSPATH", os.path.dirname(__file__))


def init_platforms():
    ctx.process_register_creator("SpiderManager", SpiderManager)


def load_configs():
    root_abspath = ctx.process_get_global("ROOT_ABSPATH")

    with open(os.path.join(root_abspath, "configs", "settings.json")) as fp:
        configs: Dict[str, Dict[str, Any]] = json.load(fp)

    runtimes = configs["Runtimes"]
    spiders = configs["Spiders"]

    for key, value in runtimes.items():
        ctx.process_set_global(f"Runtimes.{key}", value)

    for key, value in spiders.items():
        ctx.multiprocess_set_global(f"Spiders.{key}", value)


def init_envs():
    DB_ROOT_DIR = ctx.process_get_global("Runtimes.DB_ROOT_DIR")
    os.makedirs(os.path.join(DB_ROOT_DIR, "spider"), exist_ok=True)

    os.makedirs(ctx.multiprocess_get_global("Spiders.PACKAGE_ROOT_DIR"), exist_ok=True)
    os.makedirs(ctx.multiprocess_get_global("Spiders.CONTAINER_ROOT_DIR"), exist_ok=True)


def main():
    init_context()
    init_platforms()
    load_configs()
    init_envs()

    console = MainConsole()
    console.cmdloop()


if __name__ == "__main__":
    if os.name == 'nt':
        multiprocessing.freeze_support()

    main()
