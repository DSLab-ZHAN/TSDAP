#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_sqlite.py
@Time    :   2024/11/04 13:38:46
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Test file of sqlite
'''


import sqlite3
import json
import pytest
from typing import Dict
from _pytest.logging import LogCaptureFixture
from TSDAP.database import DBExceptions, SQLite
from decimal import Decimal
import random


TEST_DB_NAME = "test_db"
TEST_TABLE_NAME = "test_table"


@pytest.fixture(scope='class')
def connect_sqlite(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("temp")
    db = SQLite(
        root_dir=tmp_path
    )
    db2 = SQLite(
        root_dir=tmp_path
    )

    correct_data = json.load(open("tests/database/data/correct.json"))
    error_data = json.load(open("tests/database/data/error.json"))

    yield db, correct_data, error_data, db2

    db.db.close()


class TestDBSQLite():
    def test_create_database(self, connect_sqlite, caplog: LogCaptureFixture):
        db: SQLite
        db = connect_sqlite[0]

        # Normal create database
        assert db.create_database(TEST_DB_NAME)

        # Try create repeat database
        caplog.clear()
        with caplog.at_level("WARNING"):
            assert db.create_database(TEST_DB_NAME)
        assert len(caplog.record_tuples) == 1 and f"The `{TEST_DB_NAME}` database exists." == caplog.record_tuples[0][2]

    def test_switch_database(self, connect_sqlite, caplog: LogCaptureFixture):
        db: SQLite
        db2: SQLite
        db = connect_sqlite[0]
        db2 = connect_sqlite[3]

        # Normal switch
        assert db.switch_database(TEST_DB_NAME)

        # Try switch not exists database
        caplog.clear()
        with caplog.at_level("WARNING"):
            assert not db.switch_database("what_can_i_say")

        assert len(caplog.record_tuples) == 1 and "The `what_can_i_say` database not exists." == caplog.record_tuples[0][2]

        # Create raw database and switch to it
        assert db.create_database("raw_db")
        assert db.switch_database("raw_db")
        assert db2.switch_database("raw_db")

        # Create new database and switch to it
        assert db.create_database("new_db")
        assert db.switch_database("new_db")

        assert db.switch_database("raw_db")
        assert db.switch_database("new_db")

    def test_create_table(self, connect_sqlite, caplog: LogCaptureFixture):
        db: SQLite
        correct_data: Dict

        db, correct_data, _, _ = connect_sqlite

        # Clean selected database then try
        db._curr_database_name = None
        with pytest.raises(DBExceptions.DBNotSelectError) as e:
            assert not db.create_table(TEST_TABLE_NAME, [("c", 1)])

        assert "Not switched to database." == str(e.value)

        # Create duplicate tables
        caplog.clear()
        assert db.switch_database(TEST_DB_NAME)
        assert db.create_table(TEST_TABLE_NAME, [("c", 1)])
        with caplog.at_level("WARNING"):
            assert db.create_table(TEST_TABLE_NAME, [("c", 1)])

        assert len(caplog.record_tuples) == 1 \
            and f"The '{TEST_TABLE_NAME}' table exists in `{db._curr_database_name}`." == caplog.record_tuples[0][2]

        # Use `test_data` to test it
        assert db.switch_database(TEST_DB_NAME)
        for table_name, table_values in correct_data.items():
            column_list = list(table_values[0].items())

            assert db.create_table(table_name, column_list)

        # Create unusual datatype table
        unusual_data = {
            'c1': Decimal(0.5),
            'c2': "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",   # noqa E501
            'c3': True,
            'c4': b"Hello, World!"
        }
        assert db.create_table("Unusual", tuple(unusual_data.items()))

        # Try create unsupported datatype
        with pytest.raises(ValueError) as e:
            assert not db.create_table("U1", [('None', None)])

        assert str(e.value) == "Value cannot be None"

        with pytest.raises(TypeError) as e:
            assert not db.create_table("U2", [('U', type)])

        assert str(e.value) == f"Unsupported value type: {type(type).__name__}"

    def test_insert(self, connect_sqlite, caplog: LogCaptureFixture):
        db: SQLite
        correct_data: Dict

        db, correct_data, _, _ = connect_sqlite

        # Insert correct data
        for table_name, table_values in correct_data.items():
            for table_value in table_values:
                assert db.insert(table_name, table_value)

        # Insert correct data by long event
        with db.transaction() as transaction:
            for table_name, table_values in correct_data.items():
                for table_value in table_values:
                    assert transaction.insert(table_name, table_value)

    def test_delete(self, connect_sqlite):
        db: SQLite

        db, _, _, _ = connect_sqlite

        # Delete non-existent data
        with pytest.raises(sqlite3.OperationalError):
            assert not db.delete(TEST_TABLE_NAME, "WHERE foo='foofoo'")

        # Delete exists data
        random_data = random.randint(0, 100)
        assert db.insert(TEST_TABLE_NAME, {'c': random_data})
        assert db.delete(TEST_TABLE_NAME, f"WHERE `c` = {random_data}")

    def test_select(self, connect_sqlite):
        db: SQLite
        correct_data: Dict

        db, correct_data, _, _ = connect_sqlite

        for table_name, table_values in correct_data.items():
            column_names, results = db.select(table_name)
            assert column_names == tuple(table_values[0].keys())
            assert len(results) == len(table_values) * 2

    def test_update(self, connect_sqlite):
        db: SQLite
        db = connect_sqlite[0]

        # Update non-existent table
        with pytest.raises(DBExceptions.TBNotExistsError) as e:
            assert not db.update("foofoo", {'c': 1}, "WHERE foo='foofoo'")

        assert str(e.value) == f"The 'foofoo' table does not exist in `{db._curr_database_name}`."

        # Update non-existent data
        with pytest.raises(sqlite3.OperationalError):
            assert not db.update(TEST_TABLE_NAME, {'c': 1}, "WHERE `foo`='foofoo'")

        # Update exists data
        random_data = random.randint(0, 100)
        assert db.insert(TEST_TABLE_NAME, {'c': 1})
        assert db.update(TEST_TABLE_NAME, {'c': random_data}, "WHERE `c` = 1")
        assert db.select(TEST_TABLE_NAME, f"WHERE `c` = {random_data}")[1][0][0] == random_data

    def test_drop_table(self, connect_sqlite):
        db: SQLite
        db = connect_sqlite[0]

        assert db.switch_database(TEST_DB_NAME)

        # Drop non-existent table
        with pytest.raises(DBExceptions.TBNotExistsError) as e:
            assert not db.drop_table("foofoo")

        assert str(e.value) == f"The 'foofoo' table does not exist in `{db._curr_database_name}`."

        # Drop exists table
        assert db.drop_table(TEST_TABLE_NAME)

    def test_drop_database(self, connect_sqlite):
        db: SQLite
        db = connect_sqlite[0]

        # Drop non-existent database
        with pytest.raises(DBExceptions.DBNotExistsError) as e:
            assert not db.drop_database("foofoo")

        assert str(e.value) == "The `foofoo` database not exists."

        # Drop exists database
        assert db.create_database("ABC")
        assert db.drop_database("ABC")
