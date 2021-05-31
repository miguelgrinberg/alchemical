from contextlib import asynccontextmanager
from .core import Alchemical


class AsyncAlchemical(Alchemical):
    def _create_engine(self, *args, **kwargs):
        return self.create_async_engine(*args, **kwargs)

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
