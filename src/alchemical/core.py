from contextlib import contextmanager
import re
from threading import Lock

import sqlalchemy
import sqlalchemy.event
import sqlalchemy.orm
import sqlalchemy.ext.asyncio
from sqlalchemy.orm.decl_api import DeclarativeMeta


class TableNamer:
    def __get__(self, obj, type):
        if type.__dict__.get('__tablename__') is None and \
                type.__dict__.get('__table__') is None:
            type.__tablename__ = re.sub(
                r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1',
                type.__name__).lower().lstrip("_")
        return getattr(type, '__tablename__', None)


class BaseModel:
    __tablename__ = TableNamer()


class Alchemical:
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

    prefix_map = {'postgres': 'postgresql'}

    def __init__(self, url=None, binds=None, engine_options=None):
        self._include_sqlalchemy()
        self.lock = Lock()
        self.url = None
        self.binds = None
        self.engine_options = {}
        self.engines = None
        self.table_binds = None
        if url:
            self.initialize(url, binds=binds, engine_options=engine_options)

    def initialize(self, url, binds=None, engine_options=None):
        """Initialize the database instance.

        :param url: the database URL.
        :param binds: a dictionary with additional databases to manage with
                      this instance. The keys are the names, and the values are
                      the database URLs. A model is then assigned to a specific
                      bind with the `__bind_key__` class attribute.
        :param engine_options: a dictionary with additional engine options to
                               pass to SQLAlchemy.

        This method must be used when the instance is created without
        arguments.
        """
        self.url = url or self.url
        self.binds = binds or self.binds
        self.engine_options = engine_options or self.engine_options

    def _include_sqlalchemy(self):
        class Meta(DeclarativeMeta):
            def __init__(cls, name, bases, d):
                bind_key = d.pop('__bind_key__', None)
                super().__init__(name, bases, d)
                if bind_key and hasattr(cls, '__table__'):
                    cls.__table__.info['bind_key'] = bind_key

        for module in sqlalchemy, sqlalchemy.orm:
            for key in module.__all__:
                if not hasattr(self, key):
                    setattr(self, key, getattr(module, key))
        for key in dir(sqlalchemy.ext.asyncio):
            if (key == 'create_async_engine' or key[0].isupper()) and \
                    not hasattr(self, key):
                setattr(self, key, getattr(sqlalchemy.ext.asyncio, key))
        self.event = sqlalchemy.event
        self.Model = sqlalchemy.orm.declarative_base(cls=BaseModel,
                                                     metaclass=Meta)

    def _create_engines(self):
        options = (self.engine_options if not callable(self.engine_options)
                   else self.engine_options(None))
        options.setdefault('future', True)
        self.engines = {None: self._create_engine(
            self._fix_url(self.url), **options)}
        self.table_binds = {}
        for bind, url in (self.binds or {}).items():
            options = (self.engine_options if not callable(self.engine_options)
                       else self.engine_options(bind))
            options.setdefault('future', True)
            self.engines[bind] = self._create_engine(
                self._fix_url(url), **options)
            for table in self.get_tables_for_bind(bind):
                self.table_binds[table] = self.engines[bind]

    def _fix_url(self, url):
        for prefix, updated_prefix in self.prefix_map.items():
            if url.startswith(f'{prefix}://'):
                url = f'{updated_prefix}://' + url[len(prefix) + 3:]
                break
        return url

    def _create_engine(self, url, *args, **kwargs):
        return self.create_engine(url, *args, **kwargs)

    @property
    def metadata(self):
        return self.Model.metadata

    def get_engine(self, bind=None):
        if self.engines is None:
            with self.lock:
                if self.engines is None:
                    self._create_engines()
        return self.engines[bind]

    def bind_names(self):
        return [bind for bind in self.engines if bind is not None]

    def _get_tables_for_bind(self, bind=None):
        result = []
        for table in self.metadata.tables.values():
            if table.info.get("bind_key") == bind:
                result.append(table)
        return result

    def create_all(self):
        """Create the database tables.

        Only tables that do not already exist are created. Existing tables are
        not modified.
        """
        tables = self._get_tables_for_bind(None)
        self.Model.metadata.create_all(self.get_engine(), tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            self.Model.metadata.create_all(self.get_engine(bind),
                                           tables=tables)

    def drop_all(self):
        """Drop all the database tables.

        Note that this is a destructive operation; data stored in the
        database will be deleted when this method is called.
        """
        tables = self._get_tables_for_bind(None)
        self.Model.metadata.drop_all(self.get_engine(), tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            self.Model.metadata.drop_all(self.get_engine(bind), tables=tables)

    def session(self):
        """Return a database session.

        The recommended way to use the SQLAlchemy session is as a context
        manager::

            with db.session() as session:
                # work with the session here

        The context manager automatically closes the session at the end. If
        the session is handled without a context manager, ``session.close()``
        must be called when the it isn't needed anymore.
        """
        return self.Session(bind=self.get_engine(), binds=self.table_binds,
                            future=True)

    @contextmanager
    def begin(self):
        """Context manager for a database transaction.

        Upon entering the context manager block, a new session is created and
        a transaction started on it. If any errors occur inside the context
        manager block, then the database session will be rolled back. If no
        errors occur, the session is committed. In both cases the session is
        then closed.

        Example usage::

            with db.begin() as session:
                # work with the session here
                # a commit (on success) or rollback (on error) is automatic
        """
        with self.session() as session:
            with session.begin():
                yield session
