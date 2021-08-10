import asyncio
import sqlite3
import unittest
import pytest
from alchemical.aio import Alchemical


def async_test(f):
    def wrapper(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))

    return wrapper


class TestAio(unittest.TestCase):
    @async_test
    async def test_read_write(self):
        db = Alchemical('sqlite://')

        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128))

        await db.create_all()

        async with db.begin() as session:
            for name in ['mary', 'joe', 'susan']:
                session.add(User(name=name))

        async with db.Session() as session:
            all = (await session.execute(db.select(User))).scalars().all()
        assert len(all) == 3

        await db.drop_all()
        await db.create_all()

        async with db.Session() as session:
            all = (await session.execute(db.select(User))).scalars().all()
        assert len(all) == 0

    @async_test
    async def test_binds(self):
        db = Alchemical(
            'sqlite://', binds={'one': 'sqlite://', 'two': 'sqlite://'},
            engine_options={'pool': None})

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128))

        class User1(db.Model):
            __tablename__ = 'users1'
            __bind_key__ = 'one'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128))

        class User2(db.Model):
            __bind_key__ = 'two'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128))

        await db.create_all()
        assert db.bind_names() == ['one', 'two']

        async with db.begin() as session:
            user = User(name='main')
            user1 = User1(name='one')
            user2 = User2(name='two')
            session.add_all([user, user1, user2])

        def check(session):
            conn = db.get_engine().pool.connect()
            cur = conn.cursor()
            cur.execute('select * from users;')
            assert cur.fetchall() == [(1, 'main')]
            conn.close()

            conn = db.get_engine(bind='one').pool.connect()
            cur = conn.cursor()
            cur.execute('select * from users1;')
            assert cur.fetchall() == [(1, 'one')]
            conn.close()

            conn = db.get_engine(bind='two').pool.connect()
            cur = conn.cursor()
            cur.execute('select * from user2;')
            assert cur.fetchall() == [(1, 'two')]
            conn.close()

        async with db.Session() as session:
            await session.run_sync(check)

        await db.drop_all()

        def check_empty(session):
            conn = db.get_engine().pool.connect()
            cur = conn.cursor()
            with pytest.raises(sqlite3.OperationalError):
                cur.execute('select * from users;')
            conn.close()

            conn = db.get_engine(bind='one').pool.connect()
            cur = conn.cursor()
            with pytest.raises(sqlite3.OperationalError):
                cur.execute('select * from users1;')
            conn.close()

            conn = db.get_engine(bind='two').pool.connect()
            cur = conn.cursor()
            with pytest.raises(sqlite3.OperationalError):
                cur.execute('select * from user2;')
            conn.close()

        async with db.Session() as session:
            await session.run_sync(check_empty)
