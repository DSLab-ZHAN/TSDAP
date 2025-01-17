#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   spider.py
@Time    :   2024/10/22 00:26:40
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Spider Common Interface
'''

import logging
import sys

from abc import ABC, abstractmethod
from functools import wraps
from threading import Thread
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from . import SpiderContext


def spider_stop_checkpoint(func):
    @wraps(func)
    def wrapper(self: 'ISpider', *args, **kwargs):
        ret = func(self, *args, **kwargs)

        # Check if spider needs to exit
        if (self.context.spider_shares.is_stop_event.is_set()):
            self.unload()
            sys.exit()

        # Feed watch dog
        self.context._feed_dog()

        return ret

    return wrapper


class ISpider(ABC):
    def __init__(self) -> None:
        super(ISpider, self).__init__()

        self.context: Optional['SpiderContext'] = None
        self.logger: Optional[logging.Logger] = None

    @spider_stop_checkpoint
    def alloc_thread(self,
                     target_func: Callable,
                     thread_name: Optional[str] = None,
                     args: Iterable[Any] = (),
                     kwargs: Optional[Mapping[str, Any]] = None
                     ) -> Optional[Thread]:

        return self.context._add_thread(
            self._thread_task,
            thread_name,
            args=(target_func,) + tuple(args),
            kwargs=kwargs,
            daemon=True
        )

    @spider_stop_checkpoint
    def new_table(self,
                  table_name: str,
                  ref_data: Dict[str, Any]
                  ) -> bool:

        return self.context._new_table(table_name, ref_data)

    @spider_stop_checkpoint
    def write_data(self,
                   table_name: str,
                   data: Dict[str, Any]
                   ) -> None:

        self.context._push_data_to_queue((table_name, data))

    def read_stores(self, name: str) -> Optional[Dict[str, Any]]:
        return self.context._read_stores(name)

    def write_stores(self, name: str, store_data: Dict[str, Any]) -> bool:
        return self.context._write_stores(name, store_data)

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def unload(self) -> None:
        pass

    def _bind_context(self, context: 'SpiderContext'):
        self.context = context

    def _run(self) -> None:
        try:
            self.run()

        except Exception:
            self.context.logger.error("!!!Spider Exception!!!", exc_info=True)
            self.context.exception_occurred.set()

    def _thread_task(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)

        except Exception:
            self.context.logger.error("!!!Spider Exception!!!", exc_info=True)
            self.context.exception_occurred.set()


class SpiderWarnings():
    class ThreadLimitWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class ThreadRepeatWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
