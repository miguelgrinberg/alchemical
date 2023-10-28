import asyncio
from sqlalchemy import Column, Integer, String
from alchemical.aio import Alchemical, Model


class User(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    def __repr__(self):
        return f'<User {self.name}>'


db = Alchemical('sqlite:///users.sqlite')


async def main():
    await db.drop_all()
    await db.create_all()

    async with db.begin() as session:
        for name in ['mary', 'joe', 'susan']:
            session.add(User(name=name))

    async with db.Session() as session:
        print((await session.scalars(User.select())).all())


asyncio.run(main())
