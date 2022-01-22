import sqlite3
import unittest
from flask import Flask
import pytest
from sqlalchemy import Column, Integer, String
from alchemical.flask import Alchemical

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


class TestFlask(unittest.TestCase):
    def test_read_write(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        db.init_app(app)

        db.drop_all()
        db.create_all()

        with db.begin() as session:
            for name in ['mary', 'joe', 'susan']:
                session.add(User(name=name))

        with db.Session() as session:
            all = session.execute(User.select()).scalars().all()
        assert len(all) == 3

        with db.Session() as session:
            session.execute(User.update().where(User.name == 'joe').values(
                name='john'))
            names = [u.name for u in session.execute(
                User.select()).scalars().all()]
            assert 'joe' not in names
            assert 'john' in names

        with db.Session() as session:
            session.execute(User.delete().where(User.name == 'mary'))
            names = [u.name for u in session.execute(
                User.select()).scalars().all()]
            assert len(names) == 2
            assert 'mary' not in names

        db.drop_all()
        db.create_all()

        with db.Session() as session:
            all = session.execute(User.select()).scalars().all()
        assert len(all) == 0

    def test_binds(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        app.config['ALCHEMICAL_BINDS'] = \
            {'one': 'sqlite://', 'two': 'sqlite://'}
        db.init_app(app)

        db.drop_all()
        db.create_all()
        assert db.bind_names() == ['one', 'two']

        with db.begin() as session:
            user = User(name='main')
            user1 = User1(name='one')
            user2 = User2(name='two')
            session.add_all([user, user1, user2])

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

        db.drop_all()

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

    def test_db_session(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        db.init_app(app)

        db.drop_all()
        db.create_all()

        with pytest.raises(RuntimeError):
            db.session

        with app.app_context():
            pass  # ensure teardown does not error when there is no session

        with app.app_context():
            for name in ['mary', 'joe', 'susan']:
                db.session.add(User(name=name))
            db.session.commit()

        with db.Session() as session:
            all = session.execute(User.select()).scalars().all()
        assert len(all) == 3

    def test_db_session_autocommit(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite://'
        app.config['ALCHEMICAL_AUTOCOMMIT'] = True
        db.init_app(app)

        db.drop_all()
        db.create_all()

        with app.app_context():
            for name in ['mary', 'joe', 'susan']:
                db.session.add(User(name=name))

        with db.Session() as session:
            all = session.execute(User.select()).scalars().all()
        assert len(all) == 3

    def test_bad_config(self):
        app = Flask(__name__)
        with pytest.raises(ValueError):
            db.init_app(app)

    def test_alternate_config(self):
        app = Flask(__name__)
        app.config['ALCHEMICAL_DATABASE_URI'] = 'sqlite://'
        db.init_app(app)  # should not raise
