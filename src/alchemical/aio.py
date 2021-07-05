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
    def _create_engine(self, *args, **kwargs):
        return self.create_async_engine(*args, **kwargs)

    def initialize(self, url, binds=None, engine_options=None):
        return super().initialize(url, binds=binds,
                                  engine_options=engine_options)

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
        return self.AsyncSession(bind=self.get_engine(),
                                 binds=self.table_binds, future=True)

    @asynccontextmanager
    async def begin(self):
        async with self.session() as session:
            async with session.begin():
                yield session
