#!/usr/bin/env python3
"""Models and database I/O functionality.

Almost all of this is directly copied from the sqlalchemy docs
http://docs.sqlalchemy.org/en/latest/orm/tutorial.html
"""

import os
from datetime import datetime
from typing import Optional

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DatabaseManager:
    """"Simple class to hold the DB I/O handles

    Fields:
        session - handle for commit/rollback/closing
        debug - flag to echo
        _engine - core database interface
    """

    def __init__(self, db_path: Optional[str] = None, *, debug: bool = False):
        self._session = None
        self.debug = debug
        self._engine = None

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = 'sqlite:///messages.db'

    def _get_handles(self):
        """Connects to the database"""
        if not self.db_path:
            raise TypeError("Invalid DB path, assign one")

        self._engine = create_engine(
            self.db_path, convert_unicode=True, echo=self.debug)
        self._session = sessionmaker(bind=self._engine)

    def open_session(self) -> sqlalchemy.orm.session.Session:
        """Opens and returns a session with the database"""
        self._get_handles()
        return self._session()

    def create_db(self, db_path: Optional[str] = None):
        """Creates the database and holds handles to it

        Args:
            db_path: SQLite database path
                needs the full 'sqlite://' part in the name

        """
        self._get_handles()
        Message.__table__.create(self._engine)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    person = Column(String(30))
    message = Column(Text)
    date = Column(DateTime)
    attachment = Column(Boolean)
    attach_is_file = Column(Boolean)
    attachment_name = Column(Text)

    def __init__(self,
                 person: str,
                 message: str,
                 date: datetime,
                 attachment: bool = False,
                 attach_is_file: bool = False,
                 attachment_name: str = ''):

        self.person = person
        self.message = message
        self.date = date
        self.attachment = attachment
        self.attach_is_file = attach_is_file
        self.attachment_name = attachment_name

    def __repr__(self) -> str:
        return "<Message from %s at %s>" % (
            self.person, self.date.strftime("%m/%d/%y %H:%m"))

    def to_dict(self) -> dict:
        return {
            'person': self.person,
            'message': self.message,
            'date': self.date,
            'attachment': self.attachment,
            'attach_is_file': self.attach_is_file,
            'attachment_name': self.attachment_name,
        }


if __name__ == "__main__":
    if os.path.exists('messages.db'):
        print("'messages.db' already exists, please delete and retry")
        exit(1)
    manager = DatabaseManager(debug=True)
    manager.create_db()
