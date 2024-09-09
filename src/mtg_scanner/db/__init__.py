import logging
from typing import TypeAlias

import sqlalchemy
import sqlalchemy.dialects
import sqlalchemy.dialects.sqlite
import sqlalchemy.orm

Connection: TypeAlias = sqlalchemy.engine.Connection
OrmSession: TypeAlias = sqlalchemy.orm.Session


def insert(
    table: sqlalchemy.sql._typing._DMLTableArgument,
) -> sqlalchemy.dialects.sqlite.Insert:
    return sqlalchemy.dialects.sqlite.insert(table)


logger = logging.getLogger("DB")
