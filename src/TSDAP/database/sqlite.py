#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   sqlite.py
@Time    :   2024/10/21 23:43:44
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   SQLite interface implementation
'''


import os
import sqlite3
import threading
import warnings

from typing import Any, Dict, List, Tuple

from .common import \
    IDBCommon, DBWarnings, RetIndices, \
    covert_to_sql_type, check_database_selected, check_data_field_type, \
    check_database_exists, check_table_exists


class Singleton:
    __instances = {}
    __lock = threading.Lock()

    @classmethod
    def set(cls, raw_key, new_key, prop_dict):
        with cls.__lock:
            cls.__instances[new_key] = {
                'count': 1,
                'value': prop_dict
            }
            if (raw_key in cls.__instances):
                cls.__instances[raw_key]['count'] -= 1
                if (cls.__instances[raw_key]['count'] == 0):
                    del cls.__instances[raw_key]

    @classmethod
    def get(cls, raw_key, key):
        instance = None
        with cls.__lock:
            if (raw_key in cls.__instances):
                cls.__instances[raw_key]['count'] -= 1
                if (cls.__instances[raw_key]['count'] == 0):
                    del cls.__instances[raw_key]

            if (key in cls.__instances):
                cls.__instances[key]['count'] += 1
                instance = cls.__instances[key]['value']

        return instance


SQL_DICT = {
    'check_table_exists': "SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'",
    'create_table': "CREATE TABLE IF NOT EXISTS `{table_name}` ({columns})",
    'drop_table': "DROP TABLE IF EXISTS `{table_name}`",

    'insert_data': "INSERT INTO `{table_name}` ({columns}) VALUES ({values})",
    'delete_data': "DELETE FROM `{table_name}` {condition}",
    'update_data': "UPDATE `{table_name}` SET {sets} {condition}",
    'select_data': "SELECT * FROM `{table_name}` {condition}"
}


class SQLite(IDBCommon):
    def __init__(self,
                 root_dir: str
                 ) -> None:

        super().__init__()

        self.is_db_close: bool = True
        self.db: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

        self.lock_exec = threading.Lock()
        self.autocommit: bool = True

        self.root_dir = root_dir

        self._register_database_exists_func(self.__is_database_exists)
        self._register_table_exists_func(self.__is_table_exists)

    def __is_database_exists(self, database_name: str) -> bool:
        file_path = os.path.join(self.root_dir, f"{database_name}.db")

        if (os.path.isfile(file_path)):
            # Exists database file
            return True

        return False

    def __is_table_exists(self, table_name: str) -> bool:
        sql = SQL_DICT['check_table_exists'].format(
            table_name=table_name
        )

        results = self.execute(sql)[RetIndices.RESULT]

        if (len(results) != 0):
            return True

        return False

    @check_database_exists
    def create_database(self, database_name: str) -> bool:
        file_path = os.path.join(self.root_dir, f"{database_name}.db")

        # touch a file
        with open(file_path, 'a'):
            os.utime(file_path, None)

        return True

    @check_database_exists
    def switch_database(self, database_name: str) -> bool:
        raw_key = (self.root_dir, self._curr_database_name)

        # Detach __dict__ quote
        self.__dict__ = self.__dict__.copy()

        prop_dict = Singleton.get(raw_key, (self.root_dir, database_name))
        if (prop_dict is not None):
            self.__dict__ = prop_dict
            self._curr_database_name = database_name
            return True

        file_path = os.path.join(self.root_dir, f"{database_name}.db")

        # Create new database instance
        self.db = sqlite3.connect(file_path, check_same_thread=False)
        self.cursor = self.db.cursor()
        self._curr_database_name = database_name

        # Update instances
        Singleton.set(raw_key, (self.root_dir, database_name), self.__dict__)

        return True

    @check_database_exists
    def drop_database(self, database_name: str) -> bool:
        file_path = os.path.join(self.root_dir, f"{database_name}.db")

        os.remove(file_path)

        return True

    @check_database_selected
    @check_table_exists
    def create_table(self,
                     table_name: str,
                     column_infos: List[Tuple[str | Any]]) -> bool:

        columns = []

        for i, (name, value) in enumerate(column_infos):
            type_str = covert_to_sql_type(value)
            columns.append(f"{name} {type_str}")

        sql = SQL_DICT['create_table'].format(
            table_name=table_name,
            columns=str(",".join(columns))
        )

        return self.execute(sql)[RetIndices.STATUS]

    @check_database_selected
    @check_table_exists
    def drop_table(self, table_name: str) -> bool:
        sql = SQL_DICT['drop_table'].format(
            table_name=table_name
        )

        return self.execute(sql)[RetIndices.STATUS]

    @check_database_selected
    @check_table_exists
    @check_data_field_type
    def insert(self,
               table_name: str,
               data: Dict[str, Any]) -> bool:

        column_names = ",".join(list(data.keys()))
        values = tuple(data.values())
        holders = ",".join(["?" for _ in range(len(values))])

        sql = SQL_DICT['insert_data'].format(
            table_name=table_name,
            columns=column_names,
            values=holders
        )

        exec_ret = self.execute(sql, values)

        return exec_ret[RetIndices.STATUS]

    @check_database_selected
    @check_table_exists
    def delete(self,
               table_name: str,
               condition: str) -> bool:

        sql = SQL_DICT['delete_data'].format(
            table_name=table_name,
            condition=condition
        )

        return self.execute(sql)[RetIndices.STATUS]

    @check_database_selected
    @check_table_exists
    def select(self,
               table_name: str,
               condition: str | None = None) -> Tuple[Tuple, List]:

        sql = SQL_DICT['select_data'].format(
            table_name=table_name,
            condition=condition
        )

        exec_ret = self.execute(sql)

        return (exec_ret[RetIndices.COLUMN_NAME], exec_ret[RetIndices.RESULT])

    @check_database_selected
    @check_table_exists
    @check_data_field_type
    def update(self,
               table_name: str,
               data: Dict[str, Any],
               condition: str) -> bool:

        sets = ",".join(
            f"`{column}`={value}" for column, value in data.items()
        )

        sql = SQL_DICT['update_data'].format(
            table_name=table_name,
            sets=sets,
            condition=condition
        )

        return self.execute(sql)[RetIndices.STATUS]

    def execute(self, sql: str, data: Tuple = ()) -> Tuple:
        with self.lock_exec:
            status = False
            err_code = 0
            err_msg = None

            try:
                self.cursor.execute(sql, data)
                if self.autocommit:
                    self.db.commit()

                status = True

            except Exception as e:
                self.db.rollback()
                err_msg = e.args[0]
                raise e

            column_name = list(zip(*self.cursor.description))[0] if (self.cursor.description is not None) else None

            return (status, err_code, column_name, self.cursor.fetchall(), err_msg)

    def transaction(self):
        class TransactionManager():
            def __init__(self, outer: 'SQLite') -> None:
                self.outer = outer

            def __enter__(self) -> 'SQLite':
                self.outer.autocommit = False

                return self.outer

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    self.outer.db.commit()
                    self.outer.autocommit = True

        return TransactionManager(self)
