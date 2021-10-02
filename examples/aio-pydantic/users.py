import asyncio
from typing import Optional

from sqlmodel import Field, SQLModel
from alchemical.aio import Alchemical

db = Alchemical('sqlite:///users.sqlite', model_class=SQLModel)


class User(db.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=128)

    def __repr__(self):
        return f'<User {self.name}>'


async def main():
    await db.drop_all()
    await db.create_all()

    async with db.begin() as session:
        for name in ['mary', 'joe', 'susan']:
            session.add(User(name=name))

    async with db.Session() as session:
        print((await session.scalars(User.select())).all())


asyncio.run(main())
