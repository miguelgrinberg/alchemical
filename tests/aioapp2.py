from sqlalchemy import Column, Integer, String
from alchemical.aio import Alchemical

db = Alchemical('sqlite:///users.sqlite', binds={
    'groups': 'sqlite:///groups.sqlite'
})


class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    email = Column(String(64))


class Group(db.Model):
    __bind_key__ = 'groups'
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
