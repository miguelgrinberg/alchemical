Basic Usage
-----------

The ``Alchemical`` class is a thin wrapper around SQLAlchemy that simplifies
working with one or more databases.

Connecting to a Database
~~~~~~~~~~~~~~~~~~~~~~~~

To connect to a database, create an instance of the ``Alchemical`` class and
pass the database URL as the first argument::

    db = Alchemical('sqlite:///data.sqlite')

The URLs that you can use here are those supported by SQLAlchemy. See
`Database URLs <https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls>`_
in the SQLAlchemy documentation for details on the supported databases and
their URLs.

The ``Alchemical`` class accepts an optional ``engine_options`` argument, with
a dictionary of options that is passed directly to SQLAlchemy's
``create_engine()`` function as keyword arguments. See
`create_engine() <https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine>`_
in the SQLAlchemy documentation to learn what options are supported. As an
example, here is how to log all SQL statements::

    db = Alchemical('sqlite:///data.sqlite', engine_options={'echo': True})

Defining Database Models
~~~~~~~~~~~~~~~~~~~~~~~~

When working with Alchemical, models are created according to SQLAlchemy's
rules, using ``db.Model`` as the base class::

    from sqlalchemy import Column, Integer, String, ForeignKey
    from alchemical import Alchemical

    db = Alchemical('sqlite:///data.sqlite')

    class User(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        nickname = Column(String)

See `Declarative Mapping <https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping>`_
in the SQLAlchemy documentation.

Alchemical automatically names each database table with the name of its
corresponding  model class converted to snake case. To override the automatic
naming, a ``__tablename__`` attribute can be added to the model class::

    class User(db.Model):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        nickname = Column(String)

Creating and Destroying Database Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alchemical can create all the tables referenced by models with a single call::

    db.create_all()

Note that this only creates tables that do not currently exist in the database.
To make updates to existing tables matching changes made to their corresponding
model class, a database migration framework such as
`Alembic <https://alembic.sqlalchemy.org/en/latest/>`_ must be used.

Alchemical provides a second function that destroys (drops, in SQL jargon) all
the tables::

    db.drop_all()

Obtaining a Database Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A database session class is provided as ``db.Session``, which can be used as
a context-manager to open and close database sessions::

    with db.Session() as session:
        session.add(some_object)
        session.add(some_other_object)
        session.commit()

See `Basics of Using a Session <https://docs.sqlalchemy.org/en/14/orm/session_basics.html#basics-of-using-a-session>`_
in the SQLAlchemy documentation for more information.

Creating Database Queries
~~~~~~~~~~~~~~~~~~~~~~~~~

Alchemical uses the 2.x query model introduced in SQLAlchemy 1.4. Queries are
generally started with the ``select()`` function::

    from sqlalchemy import select

    query = select(User).where(User.name == 'mary')

Since the ``select()`` is so common, Alchemical provides a shortcut to it::

    query = User.select().where(User.name == 'mary')

See the `ORM Querying Guide <https://docs.sqlalchemy.org/en/14/orm/queryguide.html>`_
in the SQLAlchemy documentation for details on all the constructs that can be
used to create queries.

Once a query object is created, it must be executed inside a database session.
There are three main methods to execute a database query:

- ``session.scalars(query)``: Returns an iterable with a single result per row.
- ``session.scalar(query)``: Returns the first result from the first row.
- ``session.execute(query)``: Returns an iterable with a tuple of results per row.

Using Multiple Databases
~~~~~~~~~~~~~~~~~~~~~~~~

Alchemical makes it easy to manage multiple databases from a single database
instance through the use of "binds". The following example shows how to
connect to Postgres and in-memory SQLite databases::

    db = Alchemical(binds={
        'users': 'postgresql://user:password@localhost/mydb',
        'cache': 'sqlite:///',
    })

When using binds, each model class must indicate which of the binds it belongs
to with the ``__bind_key__`` attribute::

    class User(db.Model):
        __bind_key__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        nickname = Column(String)

It is also possible to combine the use of a main database and binds. The
following example connects to a MySQL database as the main database, plus
the Postgres and SQLite databases of the previous example::

    db = Alchemical('mysqldb://user:password@localhost/db', binds={
        'users': 'postgresql://user:password@localhost/mydb',
        'cache': 'sqlite:///',
    })

When combining a main database with binds, any database models that do not
have a ``__bind_key__`` attribute are assigned to the main database.

Using Pydantic Models
~~~~~~~~~~~~~~~~~~~~~

Alchemical supports the use of model classes based on
`Pydantic <https://pydantic-docs.helpmanual.io/>`_ with the
`SQLModel <https://sqlmodel.tiangolo.com/>`_ package. To take advantage of
this option, pass ``model_class=SQLModel`` when constructing the ``Alchemical``
instance::

    from typing import Optional
    from sqlmodel import Field, SQLModel
    from alchemical import Alchemical

    db = Alchemical('sqlite:///users.sqlite', model_class=SQLModel)

    class User(db.Model, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field(max_length=128)

Using with Web Frameworks
-------------------------

Alchemical is framework agnostic, so it should integrate well with most web
frameworks, without any additional work. This section describes specific
integrations that go beyond the basic usage.

Using with Flask
~~~~~~~~~~~~~~~~

Alchemical has full support for Flask with its own Flask extension. To use it,
import the ``Alchemical`` class from the ``alchemical.flask`` package::

    from alchemical.flask import Alchemical

The Alchemical Flask extension imports its configuration from Flask's
``config`` object. The following configuration options are supported:

- ``ALCHEMICAL_DATABASE_URL``: the database connection URL.
- ``ALCHEMICAL_BINDS``: a dictionary with database binds.
- ``ALCHEMOCAL_ENGINE_OPTIONS``: optionl engine options to pass to SQLAlchemy.
- ``ALCHEMICAL_AUTOCOMMIT``: If set to ``True``, database sessions are auto-committed when the request ends (the default is ``False``).

Example::

    app = Flask(__name__)
    app.config['ALCHEMICAL_DATABASE_URL'] = 'sqlite:///app.db'

    db = Alchemical(app)

When using the Flask extension, a database session is automatically created the
first time ``db.session`` is referenced during the handling of a request. This
is a pattern that will be familiar to users of the Flask-SQLAlchemy extension.
A session that is allocated in this way is automatically closed when the
request ends. If the ``ALCHEMICAL_AUTOCOMMIT`` option is set to ``True``, the
session is committed before it is closed.

The ``db.session`` is entirely optional. The ``db.Session`` class and its
context manager can be used in a Flask application if preferred.

Database Migrations with Flask-Migrate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using the Alchemical Flask extension, use of
`Flask-Migrate <https://flask-migrate.readthedocs.io/en/latest/>`_ to manage
database migrations with Alembic is fully supported.

Refer to the Flask-Migrate documentation for instructions. While many of the
Flask-Migrate examples use the Flask-SQLAlchemy extension, Alchemical can be
used in its place.

Asyncio Support
---------------

SQLAlchemy 1.4 has full support for the asyncio package. Alchemical provides
an async-enabled database instance that can be imported from
``alchemical.aio``::

    from alchemical.aio import Alchemical

When using the async version of the ``Alchemical`` class many of the methods
and context-managers are async and need to be awaited, but other than this
there are no differences.

Using with FastAPI
~~~~~~~~~~~~~~~~~~

The async version of Alchemical can be used with the
`FastAPI <https://fastapi.tiangolo.com/>`_ framework, without any changes or
a dedicated extension.

Example::

    from fastapi import FastAPI
    from sqlalchemy import Column, Integer, String
    from alchemical.aio import Alchemical

    app = FastAPI()
    db = Alchemical('sqlite:///app.db')

    class User(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String(128))

    @app.get('/')
    async def index():
        async with db.Session() as session:
            users = await session.scalars(User.select())
            return {'users': [u.name for u in users]}
