import asyncio
from functools import wraps
import sqlite3
import unittest
import pytest
from aioflask import Flask
from sqlalchemy import Column, Integer, String
from alchemical.aioflask import Alchemical

db = Alchemical()


class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


class User1(db.Model):
    __tablename__ = 'users1'
    __bind_key__ = 'one'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


class User2(db.Model):
    __bind_key__ = 'two'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))

    return wrapper


class TestAioFlask(unittest.TestCase):
    @async_test
    async def test_read_write(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        db.init_app(app)

        await db.drop_all()
        await db.create_all()

        async with db.begin() as session:
            for name in ['mary', 'joe', 'susan']:
                session.add(User(name=name))

        async with db.Session() as session:
            all = (await session.execute(User.select())).scalars().all()
        assert len(all) == 3

        async with db.Session() as session:
            await session.execute(User.update().where(
                User.name == 'joe').values(name='john'))
            names = [u.name for u in (await session.execute(
                User.select())).scalars().all()]
            assert 'joe' not in names
            assert 'john' in names

        async with db.Session() as session:
            await session.execute(User.delete().where(User.name == 'mary'))
            names = [u.name for u in (await session.execute(
                User.select())).scalars().all()]
            assert len(names) == 2
            assert 'mary' not in names

        await db.drop_all()
        await db.create_all()

        async with db.Session() as session:
            all = (await session.execute(User.select())).scalars().all()
        assert len(all) == 0

    @async_test
    async def test_binds(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        app.config['ALCHEMICAL_BINDS'] = \
            {'one': 'sqlite://', 'two': 'sqlite://'}
        db.init_app(app)

        await db.drop_all()
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
            cur.execute('select * from user;')
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
                cur.execute('select * from user;')
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

    @async_test
    async def test_db_session(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        db.init_app(app)

        await db.drop_all()
        await db.create_all()

        with pytest.raises(RuntimeError):
            db.session

        async with app.app_context():
            pass  # ensure teardown does not error when there is no session

        async with app.app_context():
            for name in ['mary', 'joe', 'susan']:
                db.session.add(User(name=name))
            await db.session.commit()

        async with db.Session() as session:
            all = (await session.execute(User.select())).scalars().all()
        assert len(all) == 3

    @async_test
    async def test_db_session_autocommit(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        app.config['ALCHEMICAL_AUTOCOMMIT'] = True
        db.init_app(app)

        await db.drop_all()
        await db.create_all()

        async with app.app_context():
            for name in ['mary', 'joe', 'susan']:
                db.session.add(User(name=name))

        async with db.Session() as session:
            all = (await session.execute(User.select())).scalars().all()
        assert len(all) == 3

    @async_test
    async def test_bad_config(self):
        app = Flask(__name__)
        with pytest.raises(ValueError):
            db.init_app(app)

    @async_test
    async def test_alternate_config(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URI'] = 'sqlite://'
        db.init_app(app)  # should not raise
