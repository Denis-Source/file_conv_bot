from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime


class User(declarative_base()):
    """
    ORM User class to store registered users
    Database consists of following fields:
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    is_admin = Column(Boolean)
    stats = Column(Integer)
    date_registered = Column(DateTime)
    last_filepath = Column(String)

    def inc_stats(self):
        """
        Increments user stat attribute
        :return:
        """
        self.stats += 1

    def set_privileges(self, is_admin):
        """
        Sets admin attribute
        :param is_admin:
        :return:
        """
        self.is_admin = is_admin

    def set_filepath(self, new_filepath):
        """
        Sets last filepath attribute to track file history
        :param new_filepath:
        :return:
        """
        self.last_filepath = new_filepath
