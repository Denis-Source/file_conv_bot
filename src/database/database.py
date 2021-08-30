from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine

from src.database.user import User
from src.logger import Logger

import os.path
import datetime

from config import Config


class UserIsAlreadyRegistered(Exception):
    pass


class NoUserFound(Exception):
    pass


class DataBase(Config):
    """
    Database class to interact with bot database
    Uses sqlite and stores it as db file at database folder
    """
    def __init__(self):
        self.folder = os.path.join(self.BASE_DIR, "database")
        self.path = f"sqlite:///{os.path.join(self.folder, 'database.db')}"
        self.logger = Logger("database")

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            self.logger.info(f"Created database folder at {self.folder}")

        self.engine = create_engine(
            self.path,
            echo=False
        )
        session = sessionmaker()
        session.configure(bind=self.engine)
        User.metadata.create_all(self.engine)
        self.session = session()

    def register_user(self, telegram_id):
        """
        Registers user with telegram_id
        If user is already in database raises exception
        :param telegram_id: int
        :return: None
        :raises: UserIsAlreadyRegistered
        """
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            msg = f"User {telegram_id} is already registered"
            self.logger.debug(msg)
            raise UserIsAlreadyRegistered(msg)
        else:
            self.session.add(
                User(
                    telegram_id=telegram_id,
                    is_admin=False,
                    stats=0,
                    date_registered=datetime.datetime.utcnow(),
                    last_filepath=""
                )
            )
            self.logger.debug(f"User {telegram_id} registered")

    def set_admin(self, telegram_id, is_admin=True):
        """
        Sets admin attribute of user found by telegram_id
        If user is not in database registers him than gives admin
        :param telegram_id: int
        :param is_admin: boo
        :return: None
        """
        # TODO logs warning every time it starts
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            user.set_privileges(is_admin)
            self.session.commit()
        else:
            self.register_user(telegram_id)
            user = query.filter_by(telegram_id=telegram_id).first()
            user.set_privileges(is_admin)
            self.session.commit()

        self.logger.warning(f"User {telegram_id} set to admin")

    def inc_stat(self, telegram_id):
        """
        Increments user stat attribute
        :param telegram_id: int
        :return: None
        :raises: NoUserFound
        """
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            user.inc_stats()
            self.session.commit()
            self.logger.debug(f"User {telegram_id} stat incremented")
        else:
            msg = f"No user with {telegram_id} found"
            self.logger.debug(msg)
            raise NoUserFound(msg)

    def get_authorised(self, telegram_id):
        """
        Checks if user is in database if so returns True
        :param telegram_id: int
        :return: bool
        """
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        self.logger.debug(f"User {telegram_id} found in database")
        if user:
            return True
        else:
            return False

    def get_admin(self, telegram_id):
        """
        Checks if user has admin rights if so returns True
        :param telegram_id: int
        :return: True
        """
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            if user.get_privileges():
                self.logger.debug(f"User {telegram_id} is admin")
                return True
        self.logger.debug(f"User {telegram_id} is not admin")
        return False

    def get_filepath(self, telegram_id):
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            filepath = user.get_last_filepath()
            self.session.commit()
            self.logger.debug(f"User {telegram_id} set  last filepath at {filepath}")
            return filepath
        else:
            msg = f"User {telegram_id} is not registered"
            self.logger.debug(msg)
            raise NoUserFound(msg)

    def set_filepath(self, telegram_id, filepath):
        """
        Sets user last_filepath attribute
        :param telegram_id: int
        :param filepath: str
        :return: None
        :raises: NoUserFound
        """
        query = self.session.query(User)
        user = query.filter_by(telegram_id=telegram_id).first()
        if user:
            user.set_last_filepath(filepath)
            self.session.commit()
            self.logger.debug(f"User {telegram_id} set  last filepath at {filepath}")
        else:
            msg = f"User {telegram_id} is not registered"
            self.logger.debug(msg)
            raise NoUserFound(msg)


