from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass
from alchemical import Alchemical, Model


class User(MappedAsDataclass, Model):
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(128))


db = Alchemical('sqlite:///users.sqlite')
db.drop_all()
db.create_all()

with db.begin() as session:
    for name in ['mary', 'joe', 'susan']:
        session.add(User(name=name))

with db.Session() as session:
    print(session.scalars(User.select()).all())
