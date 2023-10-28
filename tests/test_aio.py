import asyncio
import sqlite3
import unittest
import pytest
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, clear_mappers
from alchemical.aio import Alchemical, Model


def async_test(f):
    def wrapper(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))

    return wrapper


class TestAio(unittest.TestCase):
    def setUp(self):
        Model.__metadatas__.clear()
        clear_mappers()

    @async_test
    async def test_read_write(self):
        db = Alchemical('sqlite://')
        assert db.is_async()

        class User(db.Model):
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        await db.create_all()
        assert db.metadatas[None] == User.metadata

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
        db = Alchemical(
            'sqlite://', binds={'one': 'sqlite://', 'two': 'sqlite://'},
            engine_options={'pool': None})

        class User(db.Model):
            __tablename__ = 'users'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        class User1(db.Model):
            __tablename__ = 'users'
            __bind_key__ = 'one'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        class User2(db.Model):
            __bind_key__ = 'two'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
            addresses = relationship('Address', back_populates='user')

        class Address(db.Model):
            __bind_key__ = 'two'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
            user_id: Mapped[int] = mapped_column(ForeignKey('user2.id'))
            user = relationship('User2', back_populates='addresses')

        await db.create_all()
        assert db.bind_names() == ['one', 'two']
        assert db.metadatas[None].tables.keys() == {'users'}
        assert db.metadatas['one'].tables.keys() == {'users'}
        assert db.metadatas['two'].tables.keys() == {'user2', 'address'}

        async with db.begin() as session:
            user = User(name='main')
            user1 = User1(name='one')
            user2 = User2(name='two')
            user3 = User2(name='three')
            address1 = Address(name='address1')
            address2 = Address(name='address2')
            address1.user = user3
            address2.user = user3
            session.add_all([user, user1, user2, user3, address1, address2])

        def check(session):
            conn = db.get_engine().pool.connect()
            cur = conn.cursor()
            cur.execute('select * from users;')
            assert cur.fetchall() == [(1, 'main')]
            conn.close()

            conn = db.get_engine(bind='one').pool.connect()
            cur = conn.cursor()
            cur.execute('select * from users;')
            assert cur.fetchall() == [(1, 'one')]
            conn.close()

            conn = db.get_engine(bind='two').pool.connect()
            cur = conn.cursor()
            cur.execute('select * from user2;')
            assert cur.fetchall() == [(1, 'two'), (2, 'three')]

            cur.execute('select * from address;')
            assert cur.fetchall() == [(1, 'address1', 2), (2, 'address2', 2)]
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
                cur.execute('select * from users;')
            conn.close()

            conn = db.get_engine(bind='two').pool.connect()
            cur = conn.cursor()
            with pytest.raises(sqlite3.OperationalError):
                cur.execute('select * from user2;')
            with pytest.raises(sqlite3.OperationalError):
                cur.execute('select * from address;')
            conn.close()

        async with db.Session() as session:
            await session.run_sync(check_empty)

    @async_test
    async def test_binds_without_url(self):
        db = Alchemical(binds={'one': 'sqlite://', 'two': 'sqlite://'})

        class User1(db.Model):
            __tablename__ = 'users'
            __bind_key__ = 'one'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        class User2(db.Model):
            __bind_key__ = 'two'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
            addresses = relationship('Address', back_populates='user')

        class Address(db.Model):
            __bind_key__ = 'two'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
            user_id: Mapped[int] = mapped_column(ForeignKey('user2.id'))
            user = relationship('User2', back_populates='addresses')

        await db.create_all()
        assert db.bind_names() == ['one', 'two']
        assert None not in db.metadatas
        assert db.metadatas['one'].tables.keys() == {'users'}
        assert db.metadatas['two'].tables.keys() == {'user2', 'address'}
        assert db.get_engine() is None
        await db.drop_all()

    def test_two_phase(self):
        db = Alchemical(engine_options={'foo': 'bar'},
                        session_options={'bar': 'foo'})
        db.initialize('sqlite://', engine_options={'foo': 'baz'},
                      session_options={'baz': 'foo'})
        assert db.engine_options == {'foo': 'baz'}
        assert db.session_options == {'baz': 'foo'}
