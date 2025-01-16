#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   context.py
@Time    :   2024/10/23 22:14:07
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Spider Instance Context
'''


import base64
import logging
import importlib.util
import io
import os
import pickle
import sys

from multiprocessing import Event
from queue import Queue
from time import sleep
from threading import Thread, Timer
from typing import Any, Callable, Dict, Iterable, Mapping, Tuple, Type

from database import MySQL, SQLite
from runtime import RuntimeContext as ctx

from .common import SpiderCodes, SpiderShares
from .spider import SpiderWarnings, ISpider


DEFAULT_SPIDER_DIR: str | None = None


class SpiderVirtualIO(io.StringIO):
    def __init__(self, initial_value: str | None = None, newline: str | None = None) -> None:
        super().__init__(initial_value, newline)

    def get_logs(self) -> str:
        curr_seek = self.tell()

        self.seek(0)
        logs = "".join(self.readlines())
        self.seek(curr_seek)

        return logs


class DatabaseLogHandler(logging.Handler):
    def __init__(self, db_insert_func: Callable[[str, str, str], None], virtual_io: SpiderVirtualIO) -> None:
        super().__init__()

        self.db_insert_func = db_insert_func
        self.virtual_io = virtual_io

    def emit(self, record: logging.LogRecord) -> None:
        if (self.formatter is None):
            return

        self.db_insert_func(
            self.formatter.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            record.levelname,
            self.formatter.format(record)
        )
        self.virtual_io.write(f"{self.formatter.format(record)}\n")


class SpiderContext():
    def __init__(self,
                 user_spider_cls: Type['ISpider'],
                 spider_name: str,
                 spider_shares: SpiderShares
                 ) -> None:

        self.spider_threads: Dict[str, Thread] = {}
        self.logger: logging.Logger | None = None
        self.spider_to_master_io = SpiderVirtualIO()

        self.exception_occurred = Event()

        self.queue: Queue[Tuple] = Queue(maxsize=100)

        self.user_spider_cls = user_spider_cls
        self.thread_spider_main: 'ISpider' | None = None

        self.spider_shares = spider_shares

        self.spider_name = spider_name

        if (not self.spider_shares.is_daemon.get()):
            self.watch_dog = Timer(ctx.multiprocess_get_global("Spiders.WATCH_DOG_MAX_TIME"), self.__dog_trigger)

        self.db_data = MySQL(
            ctx.multiprocess_get_global("Spiders.MYSQL_HOST"),
            ctx.multiprocess_get_global("Spiders.MYSQL_PORT"),
            ctx.multiprocess_get_global("Spiders.MYSQL_USER"),
            ctx.multiprocess_get_global("Spiders.MYSQL_PASS")
        )
        self.db_spider = SQLite(self.spider_shares.spider_db_dir.get())

        self.THREAD_MAXIMUM = ctx.multiprocess_get_global("Spiders.THREAD_MAXIMUM")

    def __submit_queue(self) -> bool:
        with self.db_data.transaction() as transaction:
            while not self.queue.empty():
                table_name, data = self.queue.get()
                transaction.insert(table_name, data)

    def _init_db_spider(self) -> None:
        self.db_spider.create_database(self.spider_name)
        self.db_spider.switch_database(self.spider_name)

        self.db_spider.create_table("stores", list({'name': 'name', 'store_data': 'YQ=='}.items()))
        self.db_spider.create_table("logs", list({
            'DATETIME': 'time_str',
            'LEVEL': 'level_str',
            'MESSAGE': 'message_str'
        }.items()))

        logger = ctx.process_get_global("logger")

        self.logger = logger
        self.db_data._logger = logger
        self.db_spider._logger = logger

        self.db_data.create_database(self.spider_name)
        self.db_data.switch_database(self.spider_name)

    def _feed_dog(self) -> None:
        if (not self.spider_shares.is_daemon.get()):
            self.watch_dog.cancel()
            self.watch_dog = Timer(ctx.multiprocess_get_global("Spiders.WATCH_DOG_MAX_TIME"), self.__dog_trigger)
            self.watch_dog.start()

    def __dog_trigger(self) -> None:
        self.spider_shares.is_dog_trigger.set(True)
        self.spider_shares.is_stop_event.set()

    def __copy_logs(self) -> None:
        logs = self.spider_to_master_io.get_logs()
        self.spider_shares.logs.set(logs)

    def start(self) -> None:
        self._init_spider()

        if (not self.spider_shares.is_daemon.get()):
            # Not daemon spider, stop it when it didn't do something
            self.watch_dog.start()

        # Context thread loop here
        main_thread = self.spider_threads[f"spider_<{self.spider_name}>_main"]
        while True:
            if (self.queue.full()):
                # Submit queue to database
                self.__submit_queue()

            if (self.spider_shares.is_logs.get()):
                self.__copy_logs()
                self.spider_shares.is_logs.set(False)

            if (self.spider_shares.is_stop_event.is_set()):
                # Submit last queue
                self.__submit_queue()

                if (self.spider_shares.is_dog_trigger.get()):
                    self.spider_shares.ret_code.set(SpiderCodes.STATUS_DOG_TRIGGER)
                    return

                # Waiting spider main thread exit
                while main_thread.is_alive():
                    sleep(0.5)

                # Kill self thread
                self.spider_shares.ret_code.set(SpiderCodes.STATUS_SUCCESS)
                return

            if (not main_thread.is_alive()):
                # Spider exit Unexpected
                status = SpiderCodes.STATUS_SUCCESS \
                    if not self.exception_occurred.is_set() else SpiderCodes.STATUS_EXIT_UNEXPECTED

                self.spider_shares.ret_code.set(status.value)
                return

            sleep(0.5)    # Surrender CPU control

    def _init_spider(self) -> None:
        self.thread_spider_main = self.user_spider_cls()
        self.thread_spider_main._bind_context(self)
        self.thread_spider_main.logger = self.logger

        thread = Thread(
            target=self.thread_spider_main._run,
            name=f"spider_<{self.spider_name}>_main",
            daemon=True
        )

        self.spider_threads[f"spider_<{self.spider_name}>_main"] = thread

        thread.start()

    def __clean_dead_threads(self) -> None:
        threads_to_remove = []
        for thread_name, thread in self.spider_threads.items():
            if (not thread.is_alive()):
                threads_to_remove.append(thread_name)

        # Delete recorded thread
        for thread_name in threads_to_remove:
            self.spider_threads.pop(thread_name)

    def _add_thread(self,
                    target_func: Callable,
                    thread_name: str | None = None,
                    args: Iterable[Any] = (),
                    kwargs: Mapping[str, Any] | None = None,
                    daemon: bool | None = None) -> Thread | None:

        # Clean dead threads
        self.__clean_dead_threads()

        if (len(self.spider_threads) > self.THREAD_MAXIMUM):
            self.logger.warning(
                SpiderWarnings.ThreadLimitWarning(f"Too many thread allocated, maximum is {self.THREAD_MAXIMUM}.")
            )
            return None

        if (thread_name is not None and thread_name in self.spider_threads):
            self.logger.warning(
                SpiderWarnings.ThreadRepeatWarning(f"Duplicate thread names: {thread_name}.")
            )
            return None

        thread = Thread(target=target_func, name=thread_name, args=args, kwargs=kwargs, daemon=daemon)

        self.spider_threads[thread.name] = thread

        return thread

    def _push_data_to_queue(self, data: Tuple[str, Dict[str, Any]]) -> None:
        self.queue.put(data)

    def _new_table(self,
                   table_name: str,
                   ref_data: Dict[str, Any]) -> bool:

        return self.db_data.create_table(table_name, list(ref_data.items()))

    def _read_stores(self, name: str) -> Dict[str, Any] | None:
        status, results = self.db_spider.select("stores", f"WHERE name={name}")
        if (len(results) != 0):
            return pickle.loads(base64.b64decode(results[0][1]))

        return None

    def _write_stores(self, name: str, store_data: Dict[str, Any]) -> bool:
        status, results = self.db_spider.select("stores", f"WHERE name={name}")
        if (len(results) != 0):
            self.db_spider.delete("stores", f"WHERE name={name}")

        return self.db_spider.insert("stores", {
            'name': name,
            'store_data': str(base64.b64encode(pickle.dumps(store_data)), 'utf-8')
        })


def __import_from_path(work_path: str, entry_relative_path: str, entry_filename: str) -> ISpider | None:
    # Add work directory to sys.path
    sys.path.insert(0, os.path.abspath(work_path))
    sys.path.insert(0, os.path.abspath(os.path.join(work_path, entry_relative_path)))

    entry_fullpath = os.path.join(os.path.join(work_path, entry_relative_path), f"{entry_filename}.py")

    spec = importlib.util.spec_from_file_location(entry_filename, entry_fullpath)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = entry_relative_path

    sys.modules[entry_filename] = module
    spec.loader.exec_module(module)

    sub_classes = ISpider.__subclasses__()

    return sub_classes[0] if (len(sub_classes) == 1) else None


def __create_logger(db_insert_func: Callable[[str, str], None], virtual_io: SpiderVirtualIO):
    logger_formatter = logging.Formatter("[%(asctime)s][%(levelname)s] - %(message)s")

    logger_sqlite = logging.getLogger("spider1")
    logger_sqlite.setLevel(logging.INFO)

    logger_sqlite_handler = DatabaseLogHandler(db_insert_func, virtual_io)
    logger_sqlite_handler.setFormatter(logger_formatter)
    logger_sqlite.addHandler(logger_sqlite_handler)

    ctx.process_set_global("logger", logger_sqlite)


def __init_envs(envs: Dict[str, str]):
    for name, value in envs.items():
        os.environ[name] = str(value)


def context_main(context_infos: Dict[str, str],
                 envs: Dict[str, str],
                 _multiprocess_globals,
                 spider_shares) -> bool:

    ctx._multiprocess_globals = _multiprocess_globals
    ctx.process_set_global("spider_shares", spider_shares)

    __init_envs(envs)

    spider_name = context_infos['container_name']
    entry_file = context_infos['container_entry']

    entry_relative_path, entry_filename = os.path.split(entry_file)

    work_path = os.path.join(
        context_infos['container_root_dir'],
        context_infos['container_id'],
        context_infos['container_name']
    )

    spider_cls = __import_from_path(
        work_path,
        entry_relative_path,
        entry_filename
    )

    if (spider_cls is None):
        return False

    context = SpiderContext(spider_cls, spider_name, spider_shares)

    sys.stdout = context.spider_to_master_io
    __create_logger(
        lambda datetime, level, msg:
            context.db_spider.insert('logs', {'DATETIME': datetime, 'LEVEL': level, 'MESSAGE': msg}),
        context.spider_to_master_io
    )

    context._init_db_spider()
    context.start()

    return True
