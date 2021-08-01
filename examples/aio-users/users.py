import asyncio
from alchemical.aio import Alchemical

db = Alchemical('sqlite:///users.sqlite')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.name}>'


async def main():
    await db.drop_all()
    await db.create_all()

    async with db.begin() as session:
        for name in ['mary', 'joe', 'susan']:
            session.add(User(name=name))

    async with db.session() as session:
        print((await session.execute(db.select(User))).scalars().all())


asyncio.run(main())
