from sqlalchemy import Column, Integer, String
from alchemical import Alchemical

db = Alchemical('sqlite:///users.sqlite')


class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    def __repr__(self):
        return f'<User {self.name}>'


db.drop_all()
db.create_all()

with db.begin() as session:
    for name in ['mary', 'joe', 'susan']:
        session.add(User(name=name))

with db.Session() as session:
    print(session.scalars(User.select()).all())
