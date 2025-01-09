# Database Platform API Documentation
In database platform API, it provides some common operation functions for different database. The database platform API is a high-level API that provides some simplified interfaces for Time Series Prediction Platform calling.

Tips:
 - If you want to add different databases, you only need to inherit the common abstract class and implement its methods as required


# API List
- [create_database](#create_database)
- [switch_database](#switch_database)
- [drop_database](#drop_database)
- [create_table](#create_table)
- [drop_table](#drop_table)
- [insert](#insert)
- [delete](#delete)
- [select](#select)
- [update](#update)
- [execute](#execute)


# create_database
```python
def create_database(self, database_name: str) -> bool:
    ...
```
## Description
Create a database with the specified name.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
database_name | str | The name of the database to create. | True
## Returns
bool: True if the database is created successfully, otherwise False.
## Warnings
- `DBWarnings.DBExistsWarning` : If the database already exists, it will raise a `DBWarnings.DBExistsWarning` warning.
## Exceptions
- `None`
## Example
```python
create_database('test')
```

<br><br>
<br><br>
<br><br>
<br><br>

# switch_database
```python
def switch_database(self, database_name: str) -> bool:
    ...
```
## Description
Switch to the specified database.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
database_name | str | The name of the database to switch to. | True
## Returns
bool: True if the database is switched successfully, otherwise False.
## Warnings
- `DBWarnings.DBNotExistsWarning` : If the database does not exist, it will raise a `DBWarnings.DBNotExistsWarning` warning.
## Exceptions
- `None`
## Example
```python
switch_database('test')
```

<br><br>
<br><br>
<br><br>
<br><br>

# create_table
```python
def drop_database(self, database_name: str) -> bool:
    ...
```
## Description
Drop the specified database.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
database_name | str | The name of the database to drop. | True
## Returns
bool: True if the database is dropped successfully, otherwise False.
## Warnings
- `None`
## Exceptions
- `DBExceptions.DBNotExistsError` : If the database does not exist, it will raise a `DBExceptions.DBNotExistsError` exception.
## Example
```python
drop_database('test')
```

<br><br>
<br><br>
<br><br>
<br><br>

# create_table
```python
def create_table(self, table_name: str, column_infos: List[Tuple[str, Any]]) -> bool:
    ...
```
## Description
Create a table with the specified name and columns.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to create. | True
column_infos | List[Tuple] | The columns of the table. Each column is a tuple with the column name and a set of example data to determine the field type. | True
## Returns
bool: True if the table is created successfully, otherwise False.
## Warnings
- `DBWarnings.TBExistsWarning` : If the table already exists, it will raise a `DBWarnings.TBExistsWarning` warning.
## Exceptions
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
- `ValueError` : If the value of a certain item in the example data is None, it will raise a `ValueError` exception.
- `TypeError` : If the type of a certain item in the example data is not supported, it will raise a `TypeError` exception.
## Example
```python
# Create a table with two columns: id and name
# the type of id is int, and the type of name is str
# the example data of id is 1, and the example data of name is 'test'

create_table('test', [('id', 1), ('name', 'test')])
```

<br><br>
<br><br>
<br><br>
<br><br>

# drop_table
```python
def drop_table(self, table_name: str) -> bool:
    ...
```
## Description
Drop the specified table.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to drop. | True
## Returns
bool: True if the table is dropped successfully, otherwise False.
## Warnings
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
## Exceptions
- `DBExceptions.TBNotExistsError` : If the table does not exist, it will raise a `DBExceptions.TBNotExistsError` exception.
## Example
```python
drop_table('test')
```

<br><br>
<br><br>
<br><br>
<br><br>

# insert
```python
def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
    ...
```
## Description
Insert data into the specified table.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to insert data into. | True
data | Dict | The data to insert. The key is the column name and the value is the data to insert. | True
## Returns
bool: True if the data is inserted successfully, otherwise False.
## Warnings
- `DBWarnings.TypeMismatchedWarning` : If the type of the data does not match the type of the column, it will raise a `DBWarnings.TypeMismatchedWarning` warning.
## Exceptions
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
- `DBExceptions.TBNotExistsError` : If the table does not exist, it will raise a `DBExceptions.TBNotExistsError` exception.
## Example
```python
# Insert data into the table 'test'
# The data to insert is {'id': 1, 'name': 'test'}

insert('test', {'id': 1, 'name': 'test'})
```

<br><br>
<br><br>
<br><br>
<br><br>

# delete
```python
def delete(self, table_name: str, condition: str) -> bool:
    ...
```
## Description
Delete data from the specified table which meets the condition.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to delete data from. | True
condition | str | The condition to delete data which must add `WHERE` | True
## Returns
bool: True if the data is deleted successfully, otherwise False.
## Warnings
- `None`
## Exceptions
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
- `DBExceptions.TBNotExistsError` : If the table does not exist, it will raise a `DBExceptions.TBNotExistsError` exception.
## Example
```python
# Delete data from the table 'test'
# The condition is 'id=1'

delete('test', 'WHERE id=1')
```

<br><br>
<br><br>
<br><br>
<br><br>

# select
```python
def select(self, table_name: str, condition: str = None) -> Tuple[Tuple, List]:
    ...
```
## Description
Select data from the specified table which meets the condition.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to select data from. | True
condition | str | The condition to select data which must add `WHERE` | False
## Returns
Tuple: The first element is the column names of the table, and the second element is the data selected list.
## Warnings
- `None`
## Exceptions
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
- `DBExceptions.TBNotExistsError` : If the table does not exist, it will raise a `DBExceptions.TBNotExistsError` exception.
## Example
```python
# Select data from the table 'test'

select('test')  # It will return all data in the table 'test'
```

<br><br>
<br><br>
<br><br>
<br><br>

# update
```python
def update(self, table_name: str, data: Dict[str, Any], condition: str) -> bool:
    ...
```
## Description
Update data in the specified table which meets the condition.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
table_name | str | The name of the table to update data in. | True
data | Dict | The data to update. The key is the column name and the value is the data to update. | True
condition | str | The condition to update data which must add `WHERE` | True
## Returns
bool: True if the data is updated successfully, otherwise False.
## Warnings
- `DBWarnings.TypeMismatchedWarning` : If the type of the data does not match the type of the column, it will raise a `DBWarnings.TypeMismatchedWarning` warning.
## Exceptions
- `DBExceptions.DBNotSelectError` : If the database is not selected, it will raise a `DBExceptions.DBNotSelectError` exception.
- `DBExceptions.TBNotExistsError` : If the table does not exist, it will raise a `DBExceptions.TBNotExistsError` exception.
## Example
```python
# Update data in the table 'test'
# The data to update is {'name': 'test1'}
# The condition is 'id=1'

update('test', {'name': 'test1'}, 'WHERE id=1')
```

<br><br>
<br><br>
<br><br>
<br><br>

# execute
```python
def execute(self, sql: str, data: Tuple = None) -> Tuple:
    ...
```
## Description
Execute the specified SQL statement. WARNING: This method is not recommended for use, because it may cause SQL injection and other security issues.
## Parameters
Name | Type | Description | required
--- | --- | --- | ---
sql | str | The SQL statement to execute. | True
data | Tuple | The data to execute. | False
## Returns
Tuple: The result of the SQL statement.
 - status: The status of the SQL statement. True means success, False means failure.
 - err_code: The error code of the SQL statement. If the `status` is False, it will return the error code.
 - column_names: The column names of the result set.
 - data: The data of the result set.
 - err_msg: The error message of the SQL statement. If the `status` is False, it will return the error message.
## Warnings
- `**Any Warning**` : If the SQL statement has any warning, it will raise a warning.
## Exceptions
- `**Any Exception**` : If the SQL statement has any exception, it will raise an exception.
## Example
```python
# Execute the SQL statement 'SELECT * FROM test'

execute('SELECT * FROM test')
```
