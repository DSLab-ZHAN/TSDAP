#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   spider.pyi
@Time    :   2024/10/25 14:21:57
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Interface of spider
'''


import logging

from abc import ABC, abstractmethod
from threading import Thread
from typing import Any, Callable, Dict, Iterable, Mapping


class ISpider(ABC):
    """Every spider has only one class that
    needs to inherit and implement abstract functions,
    which will serve as the entry point for the spider.
    """
    def __init__(self) -> None:
        self.logger: logging.Logger
        """Spider's Log Recorder
        """
        ...

    def alloc_thread(self,
                     target_func: Callable,
                     thread_name: str | None = None,
                     args: Iterable[Any] = (),
                     kwargs: Mapping[str, Any] | None = None
                     ) -> Thread | None:
        """To apply for a thread.

        Args:
            target_func (Callable): Thread's function
            thread_name (str | None, optional): Thread's name. Defaults to None.
            args (Iterable[Any], optional): Parameters of thread tasks. Defaults to ().
            kwargs (Mapping[str, Any] | None, optional): Parameters of thread tasks. Defaults to None.

        Returns:
            Thread | None: Thread instance object
        """
        ...

    def new_table(self,
                  table_name: str,
                  ref_data: Dict[str, Any]
                  ) -> bool:
        """To create a new table.

        Args:
            table_name (str): Table's name
            ref_data (Dict[str, Any]): The column names in the table
                and the corresponding data types in the columns need to be passed
                with a complete set of data to indicate the data type.

                E.g: {'column_name': value}

        Returns:
            bool: Is successful
        """
        ...

    def write_data(self,
                   table_name: str,
                   data: Dict[str, Any]
                   ) -> None:
        """Write data to appointed table.

        Args:
            table_name (str): Table's name
            data (Dict[str, Any]): The data to be written
        """
        ...

    def read_stores(self,
                    name: str
                    ) -> Dict[str, Any] | None:
        """Some variables or data that need to be persistently stored, but are not datasets.
        This function will read it.

        Args:
            name (str): Variables name

        Returns:
            Dict[str, Any] | None: If read successfully then return it else return `None`
        """
        ...

    def write_stores(self,
                     name: str,
                     store_data: Dict[str, Any]
                     ) -> bool:
        """Some variables or data that need to be persistently stored, but are not datasets.
        This function will write it.

        Args:
            name (str): Variables name
            store_data (Dict[str, Any]): Variables dictionary

        Returns:
            bool: Is the writing successful
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """The entrance function of the spider must be rewritten.
        """
        ...

    @abstractmethod
    def unload(self) -> None:
        """The uninstallation function of a spider,
        which will be executed when the platform wants to stop a spider,
        is used to uninstall some resources and save some running data of the spider.
        """
        ...


class SpiderWarnings:
    class ThreadLimitWarning(Warning):
        def __init__(self, *args: object) -> None:
            ...

    class ThreadRepeatWarning(Warning):
        def __init__(self, *args: object) -> None:
            ...
