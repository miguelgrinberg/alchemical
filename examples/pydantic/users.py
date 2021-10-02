from typing import Optional

from sqlmodel import Field, SQLModel
from alchemical import Alchemical

db = Alchemical('sqlite:///users.sqlite', model_class=SQLModel)


class User(db.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=128)

    def __repr__(self):
        return f'<User {self.name}>'


db.drop_all()
db.create_all()

with db.begin() as session:
    for name in ['mary', 'joe', 'susan']:
        session.add(User(name=name))

with db.Session() as session:
    print(session.scalars(User.select()).all())
