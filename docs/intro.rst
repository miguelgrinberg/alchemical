What is Alchemical?
-------------------

Alchemical is a wrapper for SQLAlchemy that simplifies some aspects of
its configuration. It is inspired by the
`Flask-SQLAlchemy <https://flask-sqlalchemy.palletsprojects.com/en/2.x/>`_
extension for Flask.

Alchemical uses the newer 2.0 style query API introduced in SQLAlchemy 1.4,
and can be used with or without the Flask framework. It can also be used
with asynchronous applications based on the ``asyncio`` package.

Examples
--------

The following example creates a SQLite database with a ``user`` table, inserts
a few users, and finally prints the users to the console.

::

    from sqlalchemy import Column, Integer, String
    from alchemical import Alchemical

    db = Alchemical('sqlite:///users.sqlite')


    class User(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String(128))

        def __repr__(self):
            return f'<User {self.name}'

    db.drop_all()
    db.create_all()

    with db.begin() as session:
        for name in ['mary', 'joe', 'susan']:
            session.add(User(name=name))

    with db.Session() as session:
        print(session.scalars(User.select()).all())

The next example implements the same application, but using ``asyncio``::

    import asyncio
    from sqlalchemy import Column, Integer, String
    from alchemical.aio import Alchemical

    db = Alchemical('sqlite:///users.sqlite')


    class User(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String(128))

        def __repr__(self):
            return f'<User {self.name}'


    async def main():
        await db.drop_all()
        await db.create_all()

        async with db.begin() as session:
            for name in ['mary', 'joe', 'susan']:
                session.add(User(name=name))

        async with db.Session() as session:
            print((await session.scalars(User.select())).all())


    asyncio.run(main())
