from sqlalchemy import Column, Integer, String
from alchemical import Alchemical, Model

class User(Model):
    __bind_key__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    def __repr__(self):
        return f'<User {self.name}>'


class Group(Model):
    __bind_key__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    def __repr__(self):
        return f'<Group {self.name}>'


db = Alchemical(binds={
    'users': 'sqlite:///users.sqlite',
    'groups': 'sqlite:///groups.sqlite'
})
db.drop_all()
db.create_all()

with db.begin() as session:
    for name in ['mary', 'joe', 'susan']:
        session.add(User(name=name))
    for group in ['admins', 'moderators', 'users']:
        session.add(Group(name=group))

with db.Session() as session:
    print(session.scalars(User.select()).all())
    print(session.scalars(Group.select()).all())
