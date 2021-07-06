from contextlib import asynccontextmanager
from .core import Alchemical


class AsyncAlchemical(Alchemical):
    """Create a database instance.

    :param url: the database URL.
    :param binds: a dictionary with additional databases to manage with this
                  instance. The keys are the names, and the values are the
                  database URLs. A model is then assigned to a specific bind
                  with the `__bind_key__` class attribute.
    :param engine_options: a dictionary with additional engine options to
                           pass to SQLAlchemy.

    The database instances can be initialized without arguments, in which case
    the :func:`Alchemical.initialize` method must be called later to perform
    the initialization.
    """

    prefix_map = {
        'sqlite': 'sqlite+aiosqlite',
        'mysql': 'mysql+aiomysql',
        'postgres': 'postgresql+asyncpg',
        'postgresql': 'postgresql+asyncpg'
    }

    def initialize(self, url, binds=None, engine_options=None):
        return super().initialize(url, binds=binds,
                                  engine_options=engine_options)

    def _create_engine(self, url, *args, **kwargs):
        return self.create_async_engine(url, *args, **kwargs)

    async def create_all(self):
        tables = self._get_tables_for_bind(None)
        async with self.get_engine().begin() as conn:
            await conn.run_sync(self.Model.metadata.create_all, tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            async with self.get_engine(bind).begin() as conn:
                await conn.run_sync(self.Model.metadata.create_all,
                                    tables=tables)

    async def drop_all(self):
        tables = self._get_tables_for_bind(None)
        async with self.get_engine().begin() as conn:
            await conn.run_sync(self.Model.metadata.drop_all, tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            async with self.get_engine(bind).begin() as conn:
                await conn.run_sync(self.Model.metadata.drop_all,
                                    tables=tables)

    def session(self):
        """Return a database session.

        The recommended way to use the SQLAlchemy session is as a context
        manager::

            async with db.session() as session:
                # work with the session here

        The context manager automatically closes the session at the end. If
        the session is handled without a context manager, ``session.close()``
        must be called when the it isn't needed anymore.
        """
        return self.AsyncSession(bind=self.get_engine(),
                                 binds=self.table_binds, future=True)

    @asynccontextmanager
    async def begin(self):
        """Context manager for a database transaction.

        Upon entering the context manager block, a new session is created and
        a transaction started on it. If any errors occur inside the context
        manager block, then the database session will be rolled back. If no
        errors occur, the session is committed. In both cases the session is
        then closed.

        Example usage::

            async with db.begin() as session:
                # work with the session here
                # a commit (on success) or rollback (on error) is automatic
        """
        async with self.session() as session:
            async with session.begin():
                yield session
