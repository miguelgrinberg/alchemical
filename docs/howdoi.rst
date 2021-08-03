How Do I ...
------------

In this section you can find how to do some of the most common database tasks
using Alchemical and SQLAlchemy. All examples assume that an ``Alchemical``
instance has been created and stored in a global variable named ``db``.

... create a database model?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Alchemical`` instance provides a ``db.Model`` class to be used as a base
class for database models::

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(128))

Note how the ``db`` object provides convenient access to SQLAlchemy constructs
such as ``Column``, ``String``, etc. To learn more about how to define database
models, consult the `SQLAlchemy ORM documentation <https://docs.sqlalchemy.org/en/14/orm/index.html>`_.

... create a database session?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended way to work with a database session is to use a context
manager::

    with db.session() as session:
        # work with the session here

If you are using the asynchronous version of Alchemical, create a session as
follows::

    async with db.session() as session:
        # work with the session here

When the session is created in this way, a database transaction is
automatically initiated when required, and the ``session.flush()``,
``session.commit()`` and ``session.rollback()`` methods can be used as
necessary. The session is automatically closed and returned to the session pool
when the context manager block ends.

You can also create a session without the context manager and close it
manually::

    session = db.session()
    # work with the session here
    session.close()

And for the asynchronous version::

    session = db.session()
    # work with the session here
    await session.close()

... start a database transaction?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the previous question for implicitly starting a transaction when one is
needed. To create a session and explicitly start a transaction on it at the
same time, use the ``db.begin()`` method::

    with db.begin() as session:
        # work with the session here

Or for the asynchronous version of Alchemical::

    async with db.begin() as session:
        # work with the session here

The transaction is automatically committed if the context manager block
completes successfully, or rolled back if an error occurs. The session is then
closed.

In cases where a session has already been created, the ``begin()`` method can
be called on it to explicitly start a transaction::

    with session.begin():
        # work with the session here

Or with the asynchronous version::

    async with session.begin():
        # work with the session here

As in the previous example, the transaction is committed on success, or rolled
back on error. The session in this case is not closed.

Calling ``begin()`` on a session object only works if an implicit transaction
hasn't been started on the session yet. For a session that already has an
active transaction, the ``begin_nested()`` method can be used to create a
nested transaction or save point::

    with session.begin_nested():
        # work with the session here

Or with the asynchronous version::

    async with session.begin_nested():
        # work with the session here
    
... save an object to a database table?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a new object to the database, use ``session.add()``::

    # with a transaction's implicit commit
    with db.begin() as session:
        new_user = User(name='mary')
        session.add(new_user)

    # with an explicit commit
    with db.session() as session:
        new_user - User(name='mary')
        session.add(new_user)
        session.commit()

If you are using the asynchronous version of Alchemical::

    # with a transaction's implicit commit
    async with db.begin() as session:
        new_user = User(name='mary')
        session.add(new_user)

    # with an explicit commit
    async with db.session() as session:
        new_user = User(name='mary')
        session.add(new_user)
        await session.commit()

... retrieve an object by its primary key?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``session.get()`` method can be used to retrieve an object by its primary
key::

    # retrieve user with id=2
    with db.begin() as session:
        user = session.get(User, 2)

With the asynchronous version::

    # retrieve user with id=2
    async with db.begin() as session:
        user = await session.get(User, 2)

... execute a database query?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``session.execute()`` method::

    # find all users with names starting with "m"
    with db.session() as session:
        for user in session.execute(db.select(User).where(User.name.like('m%'))).scalars():
            print(user.name)

With the asynchronous version the ``session.execute()`` or ``session.stream()``
methods can be used, with the difference that the former buffers all results
in memory while the latter does not::

    # find all users with names starting with "m"
    async with db.session() as session:
        for user in (await session.stream(db.select(User).where(User.name.like('m%')))).scalars():
            print(user.name)

The results from ``session.execute()`` and ``session.stream()`` are returned as
a list of rows, even if only one result per row is requested. The ``scalars()``
method converts each row to a single object for convenience.

... modify an object stored in a database table?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To modify a database object, first retrieve, then modify it within a
transaction::

    # with an implicit commit
    with db.begin() as session:
        user = session.get(User, 2)
        user.name = 'john'

    # with an explicit commit
    with db.session() as session:
        user = session.get(User, 2)
        user.name = 'john'
        session.commit()

With the asynchronous version::

    # with an implicit commit
    async with db.begin() as session:
        user = await session.get(User, 2)
        user.name = 'john'

    # with an explicit commit
    async with db.session() as session:
        user = await session.get(User, 2)
        user.name = 'john'
        await session.commit()

... delete an object from a database table?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove an object from the database, use ``session.delete()`` inside a
transaction::

    # implicit commit
    with db.begin() as session:
        user = session.get(User, 2)
        session.delete(user)

    # explicit commit
    with db.session() as session:
        user = session.get(User, 2)
        session.delete(user)
        session.commit()

If you are using the asynchronous version::

    # implicit commit
    async with db.begin() as session:
        user = await session.get(User, 2)
        await session.delete(user)

    # explicit commit
    async with db.begin() as session:
        user = await session.get(User, 2)
        await session.delete(user)
        await session.commit()

... run an arbitrary SQL statement on the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``session.execute()`` along with ``db.text()``::

    with db.session() as session:
        sql = db.text('select * from user;')
        results = session.execute(sql).all()

With the asynchronous version::

    async with db.session() as session:
        sql = db.text('select * from user;')
        results = (await session.execute(sql)).all()

The asynchronous version also supports streaming the results of a raw SQL
statement::

    async with db.session() as session:
        sql = db.text('select * from user;')
        async for row in await session.stream(sql):
            print(row)
