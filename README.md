# Creating a Python CRUD application with SQL Alchemy and Cockroach DB

In this short tutorial you will create a simple Python application that stores items in a shopping list. The application demonstrates how to perform CRUD operations on a Cockroach DB table. CRUD stands for (C)reate, (R)ead, (U)pdate, and (D)elete, a set of operations commonly found in applications that store data in database tables.

At the conclusion of this tutorial you will:
* Start a local Cockroach DB cluster.
* Create a new database in your local Cockroach DB cluster using SQL.
* Create a Python application that performs CRUD operations using your Cockroach DB database.

## Before you get started

You should be familiar with:
* The basics of how databases work.
* How to use a command-line interface.
* How to install software on your machine.
* How to read simple code examples written in Python.

You will need:
* A local Cockroach DB cluster.
* A Python 3 environment.
* Permissions to install software on your machine.

**Tip:** We recommend using a Python virtual environment. [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) allow you to run multiple different Python virtual environments on the same machine. They can both be installed using [pyenv-installer](https://github.com/pyenv/pyenv-installer).

### Installing a local Cockroach DB cluster

Follow the [installation instructions for your platform](https://www.cockroachlabs.com/docs/v20.1/install-cockroachdb.html) to install Cockroach DB as a local-binary single node cluster.

**Note:** This tutorial doesn't describe how to use Cockroach DB clusters running in Kubernetes or Docker environments.

## Step 1. Starting your Cockroach DB cluster

Use the following command to start your local Cockroach DB cluster:

```
cockroach start-single-node --insecure --background
```

## Step 2. Setting up your Cockroach DB database

Start the built-in SQL shell:

```
cockroach sql --insecure
```

In the SQL shell create a new database named `chores`:

```
CREATE DATABASE chores;
```

Exit the SQL shell:

```
\q
```

A Cockroach DB database is a collection of related tables. Each table in Cockroach DB is part of a database. When you run the application later, it will create a table named `shopping_lists` within the `chores` database.

## Step 3. Setting up your Python environment

The Python application you're create uses the [SQLAlchemy](https://www.sqlalchemy.org/) object relational mapper (ORM) to map Python objects to database table data. You need to install SQLAlchemy and the Cockroach DB libraries needed to connect to your local Cockroach DB cluster.

In a terminal install the dependencies using `pip`:

```
pip install cockroachdb SQLAlchemy psycopg2-binary sqlalchemy-cockroachdb
```

## Step 4. Creating your Python application

Now you'll create the Python application. The application consists of:
* The import statements.
* The SQLAlchemy configuration settings and ORM mapping class.
* Methods to create, read, update, and delete data in the Cockroach DB table.

In a text or code editor, open a new file and save it with the name `shoppinglist.py`.

### Step 4.1. Add the import statements

At the beginning of `shoppinglist.py` add the following code to import the required Python modules and libraries:

```
#!/usr/bin/env python
"""Example of using Cockroach DB with SQLAlchemy."""

import uuid
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from cockroachdb.sqlalchemy import run_transaction
```

### Step 4.2. Add the SQLAlchemy configuration settings and mapping class

Configure SQLAlchemy to connect to your Cockroach DB cluster and add a `ShoppingListItem` class that maps to a table in the `chores` database.

Below the import statements add the following code:

```
Base = declarative_base()


class ShoppingListItem(Base):
    """Mapping class for shopping list item table rows."""
    # set the table name
    __tablename__ = 'shopping_lists'
    # use a composite primary key
    username = Column(String, primary_key=True)
    item_id = Column(UUID(as_uuid=True), primary_key=True)
    # automatically set the time to when the item is added
    added = Column(DateTime(timezone=True), server_default=func.now())
    item = Column(String)
    quantity = Column(Integer)
    # defaults to False as the item has just been added
    bought = Column(Boolean, default=False)


# we are not using security in this example
connect_args = {'sslmode': 'disable'}

# connect to the chores database running locally
engine = create_engine(
    'cockroachdb://root@localhost:26257/chores',
    connect_args=connect_args,
    echo=True                   # Log SQL queries to stdout
)

# automatically create the database table based on the ShoppingListItem class
Base.metadata.create_all(engine)
```

The `ShoppingListItem` class defines how SQLAlchemy maps the data in a database table to the attributes within the class. The `__tablename__` attribute is used by SQLAlchemy to define the table name in the Cockroach DB database. `ShoppingListItem` has attributes that map to table columns using the SQLAlchemy `Column` object. A SQLAlchemy `Column` defines the column name, column type, and any additional configuration for the column.

In `ShoppingListItem` the `username` and `item_id` columns make up a composite primary key. The class attributes all have types set in the `Column` definition: `String`, `UUID`, `DateTime`, `Integer`, and `Boolean`. These types are mapped by SQLAlchemy to the correct corresponding types in the Cockroach DB table. For example, a `String` class attribute maps to the Cockroach DB `VARCHAR` type in the underlying table, and `DateTime` maps to `TIMESTAMP`.

When you run the application, SQLAlchemy reads these definitions and automatically creates the following table within the `chores` database if it doesn't already exist:

```
CREATE TABLE shopping_lists (
	username VARCHAR NOT NULL,
	item_id UUID NOT NULL,
	added TIMESTAMP WITH TIME ZONE DEFAULT now(),
	item VARCHAR,
	quantity INTEGER,
	bought BOOLEAN,
	PRIMARY KEY (username, item_id)
)
```

### Step 4.3. Add the CRUD methods

Below the code you added in the previous step, add the following code:

```
def create_shopping_list(session):
    """Create a shopping list row."""
    apples = ShoppingListItem(
        username="alice",
        item_id=uuid.uuid4(),
        item="Gala apples",
        quantity=3
    )
    session.add(apples)
    print("\n*** Added shopping list item. ***")
    print(apples.username, apples.item_id, apples.item, apples.quantity)
    print("\n")


# call the create function
run_transaction(sessionmaker(bind=engine), create_shopping_list)


def read_shopping_list(session):
    """Read the rows in the shopping list table."""

    # there is only one row, so we can retrieve the first result
    apples = session.query(ShoppingListItem).filter_by(
        username='alice').first()
    print("\n*** Retrieved a row from shopping_lists. ***")
    print(apples.username, apples.item_id, apples.item, apples.added,
          apples.quantity, apples.bought)
    print("\n")


# call the read function
run_transaction(sessionmaker(bind=engine), read_shopping_list)


def update_shopping_list(session):
    """Update, or modify, the contents of a row in the shopping list table."""

    apples = session.query(ShoppingListItem).filter_by(
        username='alice').first()
    # modify the shopping list item, which triggers an update
    apples.bought = True

    # show the modified shopping list item
    print("\n*** Modified a shopping list item. ***")
    print(apples.username, apples.item_id, apples.item, apples.added,
          apples.quantity, apples.bought)
    print("\n")


# call the update function
run_transaction(sessionmaker(bind=engine), update_shopping_list)


def delete_shopping_list(session):
    """Delete a shopping list row."""

    apples = session.query(ShoppingListItem).filter_by(
        username='alice').first()
    # delete the shopping list item
    session.delete(apples)

    # show that there's no more rows in the table
    print("\n*** Deleted a row in shopping_lists. Rows in shopping_lists: ***",
          session.query(ShoppingListItem).filter_by(username='alice').count(),
          "\n")


# call the delete function
run_transaction(sessionmaker(bind=engine), delete_shopping_list)

```

These methods define the CRUD behavior of the application. The `create_shopping_list` creates a new shopping list item in Cockroach DB, `read_shopping_list` retrieves the newly created row, `update_shopping_list` modifies one of the columns, and `delete_shopping_list` removes the row from the table.

All the CRUD methods use a SQLAlchemy `session` parameter that represents a connection to your Cockroach DB cluster. SQLAlchemy sessions use instances of mapping classes to perform queries and database operations on the connected database. For example the following snippet from `create_shopping_list` creates a new row in `shopping_lists` by passing an instance of `ShoppingListItem` to `session.add()`:

```
apples = ShoppingListItem(
    username="alice",
    item_id=uuid.uuid4(),
    item="Gala apples",
    quantity=3
)
session.add(apples)
```

When you run the application each CRUD method is called using the `run_transaction` method. `run_transaction` creates a SQLAlchemy session that connects to your local Cockroach DB cluster and runs the SQLAlchemy operations within a Cockroach DB transaction. Transactions ensure that all database operations complete successfully before making any changes to the database tables. If any database operation within a transaction fails all the database operations will be rolled back, and the data in your database remains unchanged.

### Step 4.4. Save your application

Save the changes to `shoppinglist.py` in your editor.

## Step 5. Running your Python application

In a terminal go to the directory where you saved `shoppinglist.py` and run the application with the following command:

```
python shoppinglist.py
```

The output of the application will display in your terminal. You will see logging messages from SQLAlchemy and Cockroach DB. You will also see the results of each CRUD method in messages surrounded by three asterisks (`***`).

The full output from your application should look like the following:

```
2020-08-26 12:38:32,439 INFO sqlalchemy.engine.base.Engine select current_schema()
2020-08-26 12:38:32,439 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,442 INFO sqlalchemy.engine.base.Engine SELECT CAST('test plain returns' AS VARCHAR(60)) AS anon_1
2020-08-26 12:38:32,442 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,443 INFO sqlalchemy.engine.base.Engine SELECT CAST('test unicode returns' AS VARCHAR(60)) AS anon_1
2020-08-26 12:38:32,443 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,443 INFO sqlalchemy.engine.base.Engine select version()
2020-08-26 12:38:32,443 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,444 INFO sqlalchemy.engine.base.Engine SELECT table_name FROM information_schema.tables WHERE table_schema=%s
2020-08-26 12:38:32,444 INFO sqlalchemy.engine.base.Engine ('public',)
2020-08-26 12:38:32,446 INFO sqlalchemy.engine.base.Engine
CREATE TABLE shopping_lists (
	username VARCHAR NOT NULL,
	item_id UUID NOT NULL,
	added TIMESTAMP WITH TIME ZONE DEFAULT now(),
	item VARCHAR,
	quantity INTEGER,
	bought BOOLEAN,
	PRIMARY KEY (username, item_id)
)


2020-08-26 12:38:32,446 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,449 INFO sqlalchemy.engine.base.Engine COMMIT
2020-08-26 12:38:32,451 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2020-08-26 12:38:32,451 INFO sqlalchemy.engine.base.Engine SAVEPOINT cockroach_restart
2020-08-26 12:38:32,451 INFO sqlalchemy.engine.base.Engine {}

*** Added shopping list item. ***
alice 05752acb-1e94-4c35-ad38-66b9434c586d Gala apples 3


2020-08-26 12:38:32,453 INFO sqlalchemy.engine.base.Engine INSERT INTO shopping_lists (username, item_id, item, quantity, bought) VALUES (%(username)s, %(item_id)s, %(item)s, %(quantity)s, %(bought)s)
2020-08-26 12:38:32,453 INFO sqlalchemy.engine.base.Engine {'username': 'alice', 'item_id': UUID('05752acb-1e94-4c35-ad38-66b9434c586d'), 'item': 'Gala apples', 'quantity': 3, 'bought': False}
2020-08-26 12:38:32,463 INFO sqlalchemy.engine.base.Engine RELEASE SAVEPOINT cockroach_restart
2020-08-26 12:38:32,463 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,464 INFO sqlalchemy.engine.base.Engine COMMIT
2020-08-26 12:38:32,464 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2020-08-26 12:38:32,465 INFO sqlalchemy.engine.base.Engine SAVEPOINT cockroach_restart
2020-08-26 12:38:32,465 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,466 INFO sqlalchemy.engine.base.Engine SELECT shopping_lists.username AS shopping_lists_username, shopping_lists.item_id AS shopping_lists_item_id, shopping_lists.added AS shopping_lists_added, shopping_lists.item AS shopping_lists_item, shopping_lists.quantity AS shopping_lists_quantity, shopping_lists.bought AS shopping_lists_bought
FROM shopping_lists
WHERE shopping_lists.username = %(username_1)s
 LIMIT %(param_1)s
2020-08-26 12:38:32,466 INFO sqlalchemy.engine.base.Engine {'username_1': 'alice', 'param_1': 1}

*** Retrieved a row from shopping_lists. ***
alice 05752acb-1e94-4c35-ad38-66b9434c586d Gala apples 2020-08-26 19:38:32.451721+00:00 3 False


2020-08-26 12:38:32,467 INFO sqlalchemy.engine.base.Engine RELEASE SAVEPOINT cockroach_restart
2020-08-26 12:38:32,467 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,468 INFO sqlalchemy.engine.base.Engine COMMIT
2020-08-26 12:38:32,468 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2020-08-26 12:38:32,468 INFO sqlalchemy.engine.base.Engine SAVEPOINT cockroach_restart
2020-08-26 12:38:32,468 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,469 INFO sqlalchemy.engine.base.Engine SELECT shopping_lists.username AS shopping_lists_username, shopping_lists.item_id AS shopping_lists_item_id, shopping_lists.added AS shopping_lists_added, shopping_lists.item AS shopping_lists_item, shopping_lists.quantity AS shopping_lists_quantity, shopping_lists.bought AS shopping_lists_bought
FROM shopping_lists
WHERE shopping_lists.username = %(username_1)s
 LIMIT %(param_1)s
2020-08-26 12:38:32,469 INFO sqlalchemy.engine.base.Engine {'username_1': 'alice', 'param_1': 1}

*** Modified a shopping list item. ***
alice 05752acb-1e94-4c35-ad38-66b9434c586d Gala apples 2020-08-26 19:38:32.451721+00:00 3 True


2020-08-26 12:38:32,470 INFO sqlalchemy.engine.base.Engine UPDATE shopping_lists SET bought=%(bought)s WHERE shopping_lists.username = %(shopping_lists_username)s AND shopping_lists.item_id = %(shopping_lists_item_id)s
2020-08-26 12:38:32,470 INFO sqlalchemy.engine.base.Engine {'bought': True, 'shopping_lists_username': 'alice', 'shopping_lists_item_id': UUID('05752acb-1e94-4c35-ad38-66b9434c586d')}
2020-08-26 12:38:32,471 INFO sqlalchemy.engine.base.Engine RELEASE SAVEPOINT cockroach_restart
2020-08-26 12:38:32,471 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,472 INFO sqlalchemy.engine.base.Engine COMMIT
2020-08-26 12:38:32,473 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2020-08-26 12:38:32,473 INFO sqlalchemy.engine.base.Engine SAVEPOINT cockroach_restart
2020-08-26 12:38:32,473 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,474 INFO sqlalchemy.engine.base.Engine SELECT shopping_lists.username AS shopping_lists_username, shopping_lists.item_id AS shopping_lists_item_id, shopping_lists.added AS shopping_lists_added, shopping_lists.item AS shopping_lists_item, shopping_lists.quantity AS shopping_lists_quantity, shopping_lists.bought AS shopping_lists_bought
FROM shopping_lists
WHERE shopping_lists.username = %(username_1)s
 LIMIT %(param_1)s
2020-08-26 12:38:32,474 INFO sqlalchemy.engine.base.Engine {'username_1': 'alice', 'param_1': 1}
2020-08-26 12:38:32,477 INFO sqlalchemy.engine.base.Engine DELETE FROM shopping_lists WHERE shopping_lists.username = %(username)s AND shopping_lists.item_id = %(item_id)s
2020-08-26 12:38:32,477 INFO sqlalchemy.engine.base.Engine {'username': 'alice', 'item_id': UUID('05752acb-1e94-4c35-ad38-66b9434c586d')}
2020-08-26 12:38:32,479 INFO sqlalchemy.engine.base.Engine SELECT count(*) AS count_1
FROM (SELECT shopping_lists.username AS shopping_lists_username, shopping_lists.item_id AS shopping_lists_item_id, shopping_lists.added AS shopping_lists_added, shopping_lists.item AS shopping_lists_item, shopping_lists.quantity AS shopping_lists_quantity, shopping_lists.bought AS shopping_lists_bought
FROM shopping_lists
WHERE shopping_lists.username = %(username_1)s) AS anon_1
2020-08-26 12:38:32,479 INFO sqlalchemy.engine.base.Engine {'username_1': 'alice'}

*** Deleted a row in shopping_lists. Rows in shopping_lists: *** 0

2020-08-26 12:38:32,480 INFO sqlalchemy.engine.base.Engine RELEASE SAVEPOINT cockroach_restart
2020-08-26 12:38:32,480 INFO sqlalchemy.engine.base.Engine {}
2020-08-26 12:38:32,481 INFO sqlalchemy.engine.base.Engine COMMIT
```

## Step 6. Stop your Cockroach DB cluster

In a terminal stop your Cockroach DB cluster with the following command:

```
cockroach quit --insecure --host=localhost:2625
```
