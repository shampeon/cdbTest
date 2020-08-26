#!/usr/bin/env python
"""Example of using Cockroach DB with SQLAlchemy."""

import uuid
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from cockroachdb.sqlalchemy import run_transaction


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
