"""
This event is only targeted at sqlite database 

By default PRAGMA foreign_keys is off on sqlite.
    This is needed to enable databases handle cascade deletes
"""
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection): # only SQLite
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
