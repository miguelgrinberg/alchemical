import os
import re
import shutil
import sqlite3
import subprocess
import unittest


def run_cmd(cmd):
    subprocess.run(cmd, shell=True, check=True)


def configure_alembic(alchemical_db):
    with open('alembic.ini', 'rt') as f:
        alembic_ini = [re.sub(r'[a-z0-9]+:db', alchemical_db, line)
                       for line in f.readlines()]
    with open('alembic.ini', 'wt') as f:
        f.writelines(alembic_ini)


def get_schema(file):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    cursor.execute('SELECT sql FROM sqlite_master '
                   'WHERE type = "table" and name != "alembic_version"')
    schema = cursor.fetchall()
    conn.close()
    return [s[0].replace('\n', '').replace('\t', '') for s in schema]


class TestAlembic(unittest.TestCase):
    def setUp(self):
        os.chdir(os.path.dirname(__file__))
        if os.path.exists('migrations'):
            shutil.rmtree('migrations')
        if os.path.exists('alembic.ini'):
            os.remove('alembic.ini')
        if os.path.exists('users.sqlite'):
            os.remove('users.sqlite')
        if os.path.exists('groups.sqlite'):
            os.remove('groups.sqlite')

    def tearDown(self):
        shutil.rmtree('migrations')
        os.remove('alembic.ini')
        os.remove('users.sqlite')
        os.remove('groups.sqlite')

    def test_alembic(self):
        # create the migration repository
        run_cmd('python -m alchemical.alembic.cli init migrations')
        assert os.path.exists('migrations')
        assert os.path.exists('alembic.ini')

        # create the first revision
        configure_alembic('app1:db')
        run_cmd('alembic revision --autogenerate -m "first revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE user '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE groups '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # downgrade
        run_cmd('alembic downgrade -1')
        assert get_schema('users.sqlite') == []
        assert get_schema('groups.sqlite') == []

        # upgrade
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE user '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE groups '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # create a second revision
        configure_alembic('app2:db')
        run_cmd('alembic revision --autogenerate -m "second revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE "user" '
            '(id INTEGER NOT NULL, name VARCHAR(64), email VARCHAR(64), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE "groups" '
            '(id INTEGER NOT NULL, name VARCHAR(64), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # create a third revision
        configure_alembic('app1:db')
        run_cmd('alembic revision --autogenerate -m "third revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE "user" '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE "groups" '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

    def test_alembic_async(self):
        # create the migration repository
        run_cmd('python -m alchemical.alembic.cli init migrations')
        assert os.path.exists('migrations')
        assert os.path.exists('alembic.ini')

        # create the first revision
        configure_alembic('aioapp1:db')
        run_cmd('alembic revision --autogenerate -m "first revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE user '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE groups '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # downgrade
        run_cmd('alembic downgrade -1')
        assert get_schema('users.sqlite') == []
        assert get_schema('groups.sqlite') == []

        # upgrade
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE user '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE groups '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # create a second revision
        configure_alembic('aioapp2:db')
        run_cmd('alembic revision --autogenerate -m "second revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE "user" '
            '(id INTEGER NOT NULL, name VARCHAR(64), email VARCHAR(64), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE "groups" '
            '(id INTEGER NOT NULL, name VARCHAR(64), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]

        # create a third revision
        configure_alembic('aioapp1:db')
        run_cmd('alembic revision --autogenerate -m "third revision"')
        run_cmd('alembic upgrade head')
        assert get_schema('users.sqlite') == [
            'CREATE TABLE "user" '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_user PRIMARY KEY (id))'
        ]
        assert get_schema('groups.sqlite') == [
            'CREATE TABLE "groups" '
            '(id INTEGER NOT NULL, name VARCHAR(128), '
            'CONSTRAINT pk_groups PRIMARY KEY (id))'
        ]
