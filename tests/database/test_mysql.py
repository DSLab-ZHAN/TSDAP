#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_mysql.py
@Time    :   2024/10/17 23:28:30
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Test file of mysql
'''


import json
import pytest

from typing import Dict

from TSDAP.database import DBExceptions, DBWarnings, MySQL


TEST_DB_NAME = "test_db"
TEST_TABLE_NAME = "test_table"


@pytest.fixture(scope='class')
def connect_mysql():
    db = MySQL(
        'localhost',
        3306,
        'root',
        'password'
    )

    correct_data = json.load(open("tests/database/data/correct.json"))
    error_data = json.load(open("tests/database/data/error.json"))

    yield db, correct_data, error_data

    db.db.close()


class TestDBMySQL():
    def test_create_database(self, connect_mysql):
        db: MySQL
        db = connect_mysql[0]

        # Normal create database
        assert db.create_database(TEST_DB_NAME)

        # Try create repeat database
        with pytest.warns(DBWarnings.DBExistsWarning) as records:
            assert db.create_database(TEST_DB_NAME)
        assert len(records) == 1 and f"The `{TEST_DB_NAME}` database exists." == records[0].message.args[0]

    def test_switch_database(self, connect_mysql):
        db: MySQL
        db = connect_mysql[0]

        # Normal switch
        assert db.switch_database(TEST_DB_NAME)

        # Try switch not exists database
        with pytest.warns(DBWarnings.DBNotExistsWarning) as records:
            assert not db.switch_database("what_can_i_say")

        assert len(records) == 1 and "The `what_can_i_say` database not exists." == records[0].message.args[0]

    def test_create_table(self, connect_mysql):
        db: MySQL
        correct_data: Dict
        error_data: Dict

        db, correct_data, error_data = connect_mysql

        # Clean selected database then try
        db._curr_database_name = None
        with pytest.raises(DBExceptions.DBNotSelectError) as e:
            assert not db.create_table(TEST_TABLE_NAME, [("c", 1)])

        assert "Not switched to database." == str(e.value)

        # Create duplicate tables
        assert db.switch_database(TEST_DB_NAME)
        assert db.create_table(TEST_TABLE_NAME, [("c", 1)])
        with pytest.warns(DBWarnings.TBExistsWarning) as records:
            # This must be true, please refer to the comments returned
            # by the `check_table_exists` function in 'common.py' to understand the reason.
            assert db.create_table(TEST_TABLE_NAME, [("c", 1)])

        assert len(records) == 1 and f"The '{TEST_TABLE_NAME}' table exists in `{db._curr_database_name}`."

        # Use `test_data` to test it
        assert db.switch_database(TEST_DB_NAME)
        for table_name, table_values in correct_data.items():
            column_list = list(table_values[0].items())

            assert db.create_table(table_name, column_list)

        # Create unusual datatype table
        from decimal import Decimal
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

    def test_insert(self, connect_mysql):
        db: MySQL
        correct_data: Dict
        error_data: Dict

        db, correct_data, error_data = connect_mysql

        # Insert mismatched data type
        with pytest.warns(DBWarnings.TypeMismatchedWarning) as records:
            count = 0
            for table_name, table_values in error_data.items():
                for table_value in table_values:
                    assert not db.insert(table_name, table_value)
                    count += 1

        assert len(records) == count

        # Insert correct data
        for table_name, table_values in correct_data.items():
            for table_value in table_values:
                assert db.insert(table_name, table_value)

        # Insert mismatched data type
        with pytest.warns(DBWarnings.TypeMismatchedWarning) as records:
            for table_name, table_values in error_data.items():
                for table_value in table_values:
                    assert not db.insert(table_name, table_value)

        assert len(records) == count

    def test_delete(self, connect_mysql):
        db: MySQL
        correct_data: Dict
        error_data: Dict

        db, correct_data, error_data = connect_mysql

        # Delete non-existent data
        assert not db.delete(TEST_TABLE_NAME, "WHERE foo=foofoo")

        # Delete exists data
        import random
        random_data = random.randint(0, 100)
        assert db.insert(TEST_TABLE_NAME, {'c': random_data})
        assert db.delete(TEST_TABLE_NAME, f"WHERE `c` = {random_data}")

    def test_select(self, connect_mysql):
        db: MySQL
        correct_data: Dict
        error_data: Dict

        db, correct_data, error_data = connect_mysql

        for table_name, table_values in correct_data.items():
            column_names, results = db.select(table_name)
            assert column_names == tuple(table_values[0].keys())
            assert len(results) == len(table_values)

    def test_update(self, connect_mysql):
        db: MySQL
        db = connect_mysql[0]

        # Update non-existent table
        with pytest.raises(DBExceptions.TBNotExistsError) as e:
            assert not db.update("foofoo", {'c': 1}, "WHERE foo=foofoo")

        assert str(e.value) == f"The 'foofoo' table does not exist in `{db._curr_database_name}`."

        # Update non-existent data
        assert not db.update(TEST_TABLE_NAME, {'c': 1}, "WHERE foo=foofoo")

        # Update exists data
        import random
        random_data = random.randint(0, 100)
        assert db.insert(TEST_TABLE_NAME, {'c': 1})
        assert db.update(TEST_TABLE_NAME, {'c': random_data}, "WHERE `c` = 1")
        assert db.select(TEST_TABLE_NAME, f"WHERE `c` = {random_data}")[1][0][0] == random_data

    def test_drop_table(self, connect_mysql):
        db: MySQL
        db = connect_mysql[0]

        # Drop non-existent table
        with pytest.raises(DBExceptions.TBNotExistsError) as e:
            assert not db.drop_table("foofoo")

        assert str(e.value) == f"The 'foofoo' table does not exist in `{db._curr_database_name}`."

        # Drop exists table
        assert db.drop_table(TEST_TABLE_NAME)

    def test_drop_database(self, connect_mysql):
        db: MySQL
        db = connect_mysql[0]

        # Drop non-existent database
        with pytest.raises(DBExceptions.DBNotExistsError) as e:
            assert not db.drop_database("foofoo")

        assert str(e.value) == "The `foofoo` database not exists."

        # Drop exists database
        assert db.drop_database(TEST_DB_NAME)
