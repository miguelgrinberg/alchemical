import asyncio
import unittest
from alchemical import AsyncAlchemical


class TestAio(unittest.TestCase):
    def test_read_write(self):
        async def main():
            db = AsyncAlchemical('sqlite://')

            class User(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                name = db.Column(db.String(128))

            await db.create_all()

            async with db.begin() as session:
                for name in ['mary', 'joe', 'susan']:
                    session.add(User(name=name))

            async with db.session() as session:
                all = (await session.execute(db.select(User))).scalars().all()
            assert len(all) == 3

            await db.drop_all()
            await db.create_all()

            async with db.session() as session:
                all = (await session.execute(db.select(User))).scalars().all()
            assert len(all) == 0

        asyncio.run(main())
