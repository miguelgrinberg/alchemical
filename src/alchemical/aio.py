from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker  # only in 2.0+
from sqlalchemy.util.concurrency import greenlet_spawn
from .core import BaseAlchemical, Alchemical as SyncAlchemical, \
    Model  # noqa: F401


class Alchemical(BaseAlchemical):
    """Create a database instance.

    :param url: the database URL.
    :param binds: a dictionary with additional databases to manage with this
                  instance. The keys are the names, and the values are the
                  database URLs. A model is then assigned to a specific bind
                  with the ``__bind_key__`` class attribute.
    :param engine_options: a dictionary with additional engine options to
                           pass to SQLAlchemy.
    :param session_options: a dictionary with additional session options to
                            use when creating sessions.
    :param model_class: a custom declarative base class to use instead of the
                        default one. This class, extended with Alchemical
                        functionality, can be accessed as ``db.Model``.
    :param naming_convention: a dictionary with naming conventions to pass to
                              SQLAlchemy. The naming convention recommended in
                              the SQLAlchemy documentation is used by default.
                              Pass an empty dictionary to disable naming
                              conventions.

    The database instances can be initialized in two phases, in which case the
    :func:`Alchemical.initialize` method must be called later to complete the
    initialization. Note that the `model_class` and `naming_convention`
    arguments can only be passed in this first phase, while the remaining
    arguments can be passed in either phase.
    """

    prefix_map = {
        'sqlite': 'sqlite+aiosqlite',
        'mysql': 'mysql+aiomysql',
        'postgres': 'postgresql+asyncpg',
        'postgresql': 'postgresql+asyncpg'
    }

    def __init__(self, url=None, binds=None, engine_options=None,
                 session_options=None, model_class=None,
                 naming_convention=None):
        super().__init__(url=url, binds=binds, engine_options=engine_options,
                         session_options=session_options,
                         model_class=model_class,
                         naming_convention=naming_convention)
        self._sync = None

    def initialize(self, url=None, binds=None, engine_options=None,
                   session_options=None):
        """Initialize the database instance.

        :param url: the database URL.
        :param binds: a dictionary with additional databases to manage with
                      this instance. The keys are the names, and the values are
                      the database URLs. A model is then assigned to a specific
                      bind with the `__bind_key__` class attribute.
        :param engine_options: a dictionary with additional engine options to
                               pass to SQLAlchemy.
        :param session_options: a dictionary with additional session options to
                                use when creating sessions.

        This method must be called explicitly to complete the initialization of
        the instance the two-phase initialization method is used.
        """
        super().initialize(url, binds=binds, engine_options=engine_options,
                           session_options=session_options)
        self._sync = None

    def _create_engine(self, url, *args, **kwargs):
        return create_async_engine(url, *args, **kwargs)

    async def create_all(self):
        """Create the database tables.

        Only tables that do not already exist are created. Existing tables are
        not modified.

        Note: this method is a coroutine.
        """
        def sync_create_all(sync_db):
            sync_db.create_all()

        await self.run_sync(sync_create_all)

    async def drop_all(self):
        """Drop all the database tables.

        Note that this is a destructive operation; data stored in the
        database will be deleted when this method is called.

        Note: this method is a coroutine.
        """
        def sync_drop_all(sync_db):
            sync_db.drop_all()

        await self.run_sync(sync_drop_all)

    @property
    def Session(self):
        """Return a database session.

        The recommended way to use the SQLAlchemy session is as a context
        manager::

            async with db.Session() as session:
                # work with the session here

        The context manager automatically closes the session at the end. A
        session can also be created without a context manager::

            session = db.Session()

        When the session is created in this way, ``await session.close()`` must
        be called when the session isn't needed anymore.
        """
        if self.session_class is None:
            options = {'future': True, 'expire_on_commit': False}
            options.update(self.session_options)
            self.session_class = async_sessionmaker(
                bind=self.get_engine(), binds=self.table_binds, **options)
        return self.session_class

    @asynccontextmanager
    async def begin(self):
        """Context manager for a database transaction.

        Upon entering the context manager block, a new session is created and
        a transaction started on it. If any errors occur inside the context
        manager block, then the transaction is rolled back. If no errors occur,
        the transaction is committed. In both cases the session is then closed.

        Example usage::

            async with db.begin() as session:
                # work with the session here
                # a commit (on success) or rollback (on error) is automatic
        """
        async with self.Session() as session:
            async with session.begin():
                yield session

    async def run_sync(self, f, *args, **kwargs):  # pragma: no cover
        """Run a function using a synchronous version of this object.

        This method can be used to start a synchronous function under the
        SQLALchemy sync/async compatibility layer based on greenlets. The
        function receives a sync version of the Alchemical object as first
        argument.

        Applications would not normally need to use this method directly, as it
        is used internally to support some operations that do not currently
        have an awaitable interface. For more information, search for
        ``run_sync`` in the SQLAlchemy documentation.

        Note: this method is a coroutine.
        """
        if self._sync is None:
            self._sync = SyncAlchemical(url=self.url, binds=self.binds,
                                        engine_options=self.engine_options,
                                        model_class=self.Model)
            self.get_engine()  # this makes sure engines are created
            self._sync.engines = {bind: engine.sync_engine
                                  for bind, engine in self.engines.items()}
            self._sync.table_binds = {
                table: engine.sync_engine
                for table, engine in self.table_binds.items()}

        return await greenlet_spawn(f, self._sync, *args, **kwargs)

    def is_async(self):
        """Return True if this database instance is asynchronous."""
        return True
