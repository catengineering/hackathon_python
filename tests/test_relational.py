# encoding: utf-8

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import random

from .common import test
from vendor import (
    create_relational_database_instance,
    create_relational_database_client,
)

Base = declarative_base()


def make_name():
    """
    First names are the top 10 baby names of 2017 as defined by the SSA at
    https://www.ssa.gov/oact/babynames/ , and the last names are the most
    frequently occurring surnames from the 2010 census, as defined by the
    Census at
    https://www.census.gov/topics/population/genealogy/data/2010_surnames.html
    """

    first_names = ["Liam", "Emma", "Noah", "Olivia", "William", "Ava", "James",
                   "Isabella", "Logan", "Sophia", "Benjamin", "Mia", "Mason",
                   "Charlotte", "Elijah", "Amelia", "Oliver", "Evelyn", "Jacob",
                   "Abigail"]

    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martínez"]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return (first_name.lower(), " ".join([first_name, last_name]))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    fullname = Column(String(128))

NUM_OF_INSERT = 10

@test
def test_relational_instance(resource_group_name):
    with create_relational_database_instance(resource_group_name) as handle:
        engine = create_relational_database_client(handle)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        session = Session()
        for _ in range(0, NUM_OF_INSERT):
            name, fullname = make_name()
            user = User(name=name, fullname=fullname)
            session.add(user)

        assert len(session.query(User).all()) == NUM_OF_INSERT, \
                "users in the database should be %d" % NUM_OF_INSERT

        session.rollback()
        assert len(session.query(User).all()) == 0, \
                "users in the database should be 0"

        session = Session()
        for _ in range(0, NUM_OF_INSERT):
            name, fullname = make_name()
            user = User(name=name, fullname=fullname)
            session.add(user)
        session.commit()

        assert len(session.query(User).all()) == NUM_OF_INSERT, \
                "users in the database should be %d" % NUM_OF_INSERT

        session.close()
