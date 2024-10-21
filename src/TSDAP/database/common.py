#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   common.py
@Time    :   2024/10/12 21:51:01
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Database Common Interface
'''


import re
import warnings

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import IntEnum
from functools import wraps
from typing import Any, Callable, Dict, List, Tuple, Type

from ..utils.RWLock import WritePriorityReadWriteLock


def covert_to_sql_type(value: Any) -> str:
    if (isinstance(value, bool)):
        return "BOOLEAN"

    elif (isinstance(value, int)):
        return "INTEGER"

    elif (isinstance(value, float)):
        return "FLOAT"

    elif (isinstance(value, Decimal)):
        return "Decimal"

    elif (isinstance(value, str)):
        if (re.match(r"\b(?:(?:\d{4}\W\d{2}\W\d{2})|(?:\d{4}\d{2}\d{2}))\b", value)):
            return "DATE"

        if (re.match(r"\b(?:(\d{4})([^A-Za-z0-9\s])(\d{2})\2(\d{2}))[T\s]([01]\d|2[0-3]):[0-5]\d:[0-5]\d\b", value)):
            return "DATETIME"

        if (str(value).__len__() > 250):
            return "TEXT"

        return "VARCHAR(255)"

    elif (isinstance(value, bytes)):
        return "BLOB"

    elif (value is None):
        raise ValueError("Value cannot be None")

    else:
        raise TypeError(f"Unsupported value type: {type(value).__name__}")


def check_database_exists(func):
    @wraps(func)
    def wrapper(self: IDBCommon, *args, **kwargs):
        if self._database_exists_func is None:
            raise ValueError("database_exists_func must be registered, use `_register_database_exists_func` to register it.")   # pragma: no cover # noqa E501

        database_name = args[0]
        is_exists = self._database_exists_func(database_name)

        operations = {
            "switch_database": {
                "condition": not is_exists,
                "action": lambda: warnings.warn(
                    DBWarnings.DBNotExistsWarning(f"The `{database_name}` database not exists.")
                ),
                "result": False
            },
            "drop_database": {
                "condition": not is_exists,
                "action": lambda: (_ for _ in ()).throw(
                    DBExceptions.DBNotExistsError(f"The `{database_name}` database not exists.")
                )
            },
            "create_database": {
                "condition": is_exists,
                "action": lambda: warnings.warn(
                    DBWarnings.DBExistsWarning(f"The `{database_name}` database exists.")
                ),
                "result": True
            }
        }

        operation = operations.get(func.__name__)

        if operation and operation["condition"]:
            operation["action"]()
            return operation.get("result", None)

        return func(self, *args, **kwargs)

    return wrapper


def check_database_selected(func):
    @wraps(func)
    def wrapper(self: IDBCommon, *args, **kwargs):
        if self._curr_database_name is None:
            raise DBExceptions.DBNotSelectError("Not switched to database.")

        return func(self, *args, **kwargs)

    return wrapper


def check_table_exists(func):
    @wraps(func)
    def wrapper(self: IDBCommon, *args, **kwargs):
        if self._table_exists_func is None:
            raise ValueError("_table_exists_func must be registered, use `_register_table_exists_func` to register it.")    # pragma: no cover # noqa E501

        table_name = args[0]
        is_exists = self._table_exists_func(table_name)

        operations = {
            # When `func.__name__` overlaps with the custom function name below,
            # it will be overwritten by the function dictionary below
            func.__name__: {
                "condition": not is_exists,
                "action": lambda: (_ for _ in ()).throw(
                    DBExceptions.TBNotExistsError(f"The '{table_name}' table does not exist in `{self._curr_database_name}`.")
                )
            },
            "create_table": {
                "condition": is_exists,

                # In table building operations, returning True is necessary
                # to ensure that the caller's subsequent code is not affected,
                # regardless of whether the table already exists.
                # When the table already exists, only one warning needs to be thrown
                "action": lambda: warnings.warn(
                    DBWarnings.TBExistsWarning(f"The '{table_name}' table exists in `{self._curr_database_name}`.")
                ),

                "result": True
            }
        }

        operation = operations.get(func.__name__)

        if operation and operation["condition"]:
            operation["action"]()
            return operation.get("result", None)

        return func(self, *args, **kwargs)

    return wrapper


def check_data_field_type(func):
    @wraps(func)
    def wrapper(self: IDBCommon, *args, **kwargs):
        # Check datatype
        status, err_pairs = self._check_datatype_correct(args[0], args[1])
        if (not status):
            warnings.warn(DBWarnings.TypeMismatchedWarning(f"Error pairs info: {err_pairs}"))
            return status

        status = func(self, *args, **kwargs)
        if (status):
            # Add mapping table to quick check next data
            self._append_table_datatype_to_map(args[0], args[1])

        return status

    return wrapper


class IDBCommon(ABC):
    """ The interface of database. You can inherit and implement interface functions,\n
        then you can call the implemented database in the platform code.
    """
    def __init__(self) -> None:
        super(IDBCommon, self).__init__()

        self._curr_database_name: str = None

        self._type_map_for_tables: Dict[str, Dict] = {}
        self.__type_map_for_tables_lock = WritePriorityReadWriteLock()

        self._database_exists_func: Callable[[], bool] = None
        self._table_exists_func: Callable[[], bool] = None

    def __get_data_type(
            self,
            data: Dict[str, Any]) -> Dict[str, Type]:     # pragma: no cover

        data_type_map = {}

        for key, value in data.items():
            if isinstance(value, dict):
                # If the value is a nested dict, recursively process it.
                data_type_map[key] = self.__get_data_type(value)

            elif isinstance(value, list):
                # If the value is a list, check the first element of the list to infer the type.
                if value and isinstance(value[0], dict):
                    # If the elements in the list are dictionaries, recursively process the content in the dictionary.
                    data_type_map[key] = [self.__get_data_type[value[0]]]
                else:
                    data_type_map[key] = [type(value[0])] if value else type(None)

            else:
                # Basic data type
                data_type_map[key] = type(value)

        return data_type_map

    def __compare_data_type_maps(
            self,
            data: Dict[str, Any],
            type_map: Dict[str, Type]) -> Tuple[bool, List]:   # pragma: no cover

        err_pairs = []
        pos = ""

        def check(data, type_map, pos):
            if (isinstance(data, dict) and isinstance(type_map, dict)):
                for key in data.keys():
                    new_pos = f"{pos}.{key}" if pos else key
                    if key in type_map.keys():
                        check(data[key], type_map[key], new_pos)
                    else:
                        err_pairs.append({
                            'pos': new_pos,
                            'datatype': type(data[key]).__name__,
                            'except': 'NoneType'
                        })

            elif (isinstance(data, list) and isinstance(type_map, list) and len(type_map) > 0):
                list_item_type = type_map[0]
                for i, item in enumerate(data):
                    new_pos = f"{pos}.{i}" if pos else str(i)
                    check(item, list_item_type, new_pos)

            else:
                if not isinstance(data, type_map):
                    err_pairs.append({
                        'pos': pos,
                        'datatype': type(data).__name__,
                        'expection': type_map.__name__
                    })

        check(data, type_map, pos)

        status = False if len(err_pairs) else True

        return (status, err_pairs)

    def _check_datatype_correct(self,
                                table_name: str,
                                data: Dict[str, Type]) -> Tuple[bool, List]:

        self.__type_map_for_tables_lock.acquire_read()

        correct_table_type = self._type_map_for_tables[table_name] \
            if table_name in self._type_map_for_tables.keys() else None

        self.__type_map_for_tables_lock.release_read()

        # For the first submission, there is no corresponding type in the type mapping table,
        # and it is necessary to return True to obtain the corresponding type table.
        return self.__compare_data_type_maps(data, correct_table_type) \
            if correct_table_type is not None else [True, None]

    def _append_table_datatype_to_map(
            self,
            table_name: str,
            data: Dict[str, Any]) -> None:

        self.__type_map_for_tables_lock.acquire_write()

        self._type_map_for_tables[table_name] = self.__get_data_type(data)

        self.__type_map_for_tables_lock.release_write()

    def _register_database_exists_func(self, func: Callable[[], bool]):
        self._database_exists_func = func

    def _register_table_exists_func(self, func: Callable[[], bool]):
        self._table_exists_func = func

    @abstractmethod
    # pragma: no cover
    def create_database(self, database_name: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def switch_database(self, database_name: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def drop_database(self, database_name: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def create_table(self, table_name: str, column_infos: List[Tuple[str, Any]]) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def drop_table(self, table_name: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def delete(self, table_name: str, condition: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def select(self, table_name: str, condition: str = None) -> Any:
        pass

    @abstractmethod
    # pragma: no cover
    def update(self, table_name: str, data: Dict[str, Any], condition: str) -> bool:
        pass

    @abstractmethod
    # pragma: no cover
    def execute(self, sql: str, data: Tuple = None) -> Any:
        pass


class DBExceptions:     # pragma: no cover
    class DBExistsError(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class DBNotExistsError(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class DBNotSelectError(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class TBExistsError(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class TBNotExistsError(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)


class DBWarnings:       # pragma: no cover
    class DBExistsWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class DBNotExistsWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class TBExistsWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class TBNotExistsWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class TypeMismatchedWarning(Warning):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)


class RetIndices(IntEnum):
    STATUS = 0
    ERROR_CODE = 1
    COLUMN_NAME = 2
    RESULT = 3
    ERROR_MSG = 4