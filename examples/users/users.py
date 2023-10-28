from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from alchemical import Alchemical, Model


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))

    def __repr__(self):
        return f'<User {self.name}>'


db = Alchemical('sqlite:///users.sqlite')
db.drop_all()
db.create_all()

with db.begin() as session:
    for name in ['mary', 'joe', 'susan']:
        session.add(User(name=name))

with db.Session() as session:
    print(session.scalars(User.select()).all())
