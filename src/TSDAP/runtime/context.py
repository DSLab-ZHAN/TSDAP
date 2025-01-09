#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   context.py
@Time    :   2024/10/25 14:42:12
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   TSDAP Runtime Container
'''


from multiprocessing import Manager
from typing import Any, Callable, Type


class RuntimeContext():
    _process_instances = {}
    _process_creators = {}

    _process_globals = {}

    _multiprocess_manager = None
    _multiprocess_globals = None

    @classmethod
    def initialize(cls):
        if cls._multiprocess_manager is None:
            cls._multiprocess_manager = Manager()
            cls._multiprocess_globals = cls._multiprocess_manager.dict()

    @classmethod
    def process_register_creator(cls, key: str, creator: Type[object]) -> None:
        cls._process_creators[key] = creator

    @classmethod
    def process_get_instance(cls, key: str) -> Callable:
        if key not in cls._process_instances and key in cls._process_creators:
            cls._process_instances[key] = cls._process_creators[key]()
        if key not in cls._process_instances:
            raise ValueError(f"Instance or creator for '{key}' is not registered.")
        return cls._process_instances[key]

    @classmethod
    def process_del_instance(cls, key: str) -> None:
        if key in cls._process_instances:
            del cls._process_instances[key]

    @classmethod
    def process_set_global(cls, key: str, value: Any) -> None:
        cls._process_globals[key] = value

    @classmethod
    def process_get_global(cls, key: Any) -> Any:
        return cls._process_globals.get(key, None)

    @classmethod
    def multiprocess_set_global(cls, key: str, value: Any) -> None:
        cls._multiprocess_globals[key] = value

    @classmethod
    def multiprocess_get_global(cls, key: str) -> Any:
        return cls._multiprocess_globals.get(key, None)

    @classmethod
    def unload(cls) -> None:
        pass
