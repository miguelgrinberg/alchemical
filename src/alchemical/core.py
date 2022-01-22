from contextlib import contextmanager
import re
from threading import Lock

from sqlalchemy import create_engine, MetaData, select, update, delete
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm.decl_api import DeclarativeMeta


class TableNamer:  # pragma: no cover
    def __get__(self, obj, type):
        if type.__dict__.get('__tablename__') is None and \
                type.__dict__.get('__table__') is None:
            type.__tablename__ = re.sub(
                r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1',
                type.__name__).lower().lstrip("_")
        return getattr(type, '__tablename__', None)


class BaseModel:
    """This is the base model class from where all models inherit from."""
    __tablename__ = TableNamer()

    @classmethod
    def select(cls):
        """Create a select statement on this model.

        Example::

            User.select().order_by(User.username)
        """
        return select(cls)

    @classmethod
    def update(cls):
        """Create an update statement on this model.

        Example::

            User.select().order_by(User.username)
        """
        return update(cls)

    @classmethod
    def delete(cls):
        """Create a delete statement on this model.

        Example::

            User.delete().where(User.username == 'susan')
        """
        return delete(cls)


class Alchemical:
    """Create a database instance.

    :param url: the database URL.
    :param binds: a dictionary with additional databases to manage with this
                  instance. The keys are the names, and the values are the
                  database URLs. A model is then assigned to a specific bind
                  with the ``__bind_key__`` class attribute.
    :param engine_options: a dictionary with additional engine options to
                           pass to SQLAlchemy.
    :param model_class: a custom declarative base to use as parent class for
                        ``db.Model``.

    The database instances can be initialized without arguments, in which case
    the :func:`Alchemical.initialize` method must be called later to perform
    the initialization.
    """

    prefix_map = {'postgres': 'postgresql'}

    def __init__(self, url=None, binds=None, engine_options=None,
                 model_class=None):
        self._setup_sqlalchemy(model_class)
        self.lock = Lock()
        self.url = None
        self.binds = None
        self.engine_options = {}
        self.engines = None
        self.metadatas = {}
        self.table_binds = None
        if url or binds:
            self.initialize(url, binds=binds, engine_options=engine_options)
        elif engine_options:
            raise ValueError('"url" and/or "binds" must be set')

    def initialize(self, url=None, binds=None, engine_options=None):
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
        if url is None and binds is None:
            raise ValueError('"url" and/or "binds" must be set')
        self.url = url or self.url
        self.binds = binds or self.binds
        self.engine_options = engine_options or self.engine_options
        self.session_class = Session
        self.metadatas[None] = self.Model.metadata

    def _setup_sqlalchemy(self, model_class):
        metaclass = type(model_class) if model_class else DeclarativeMeta

        class Meta(metaclass):
            def __init__(cls, name, bases, d, **kwargs):
                bind_key = d.pop('__bind_key__', None)
                if bind_key:
                    if bind_key not in self.metadatas:
                        self.metadatas[bind_key] = MetaData()
                    cls.metadata = self.metadatas[bind_key]
                super().__init__(name, bases, d, **kwargs)
                if bind_key and hasattr(cls, '__table__'):
                    cls.__table__.info['bind_key'] = bind_key

        if not model_class:
            self.Model = declarative_base(cls=BaseModel, metaclass=Meta)
        else:
            class_dict = {k: v for k, v in BaseModel.__dict__.items()
                          if not k.startswith('__')}
            class_dict['__abstract__'] = True
            class_dict['__tablename__'] = TableNamer()
            self.Model = Meta('Base', (model_class, ), class_dict)

    def _create_engines(self):
        options = (self.engine_options if not callable(self.engine_options)
                   else self.engine_options(None))
        options.setdefault('future', True)
        self.engines = {}
        if self.url:
            self.engines[None] = self._create_engine(
                self._fix_url(self.url), **options)
        self.table_binds = {}
        for bind, url in (self.binds or {}).items():
            options = (self.engine_options if not callable(self.engine_options)
                       else self.engine_options(bind))
            options.setdefault('future', True)
            self.engines[bind] = self._create_engine(
                self._fix_url(url), **options)
            for table in self.metadatas[bind].tables.values():
                self.table_binds[table] = self.engines[bind]

    def _fix_url(self, url):
        for prefix, updated_prefix in self.prefix_map.items():
            if url.startswith(f'{prefix}://'):
                url = f'{updated_prefix}://' + url[len(prefix) + 3:]
                break
        return url

    def _create_engine(self, url, *args, **kwargs):
        return create_engine(url, *args, **kwargs)

    @property
    def metadata(self):
        # Only for compatibility with Flask-SQLAlchemy.
        # The self.metadatas dictionary indexed by bind should be preferred.
        if self.binds is None or len(self.binds) == 0:
            return self.Model.metadata

        # Flask-SQLAlchemy puts all the binds in a single metadata instance
        m = MetaData()
        for metadata in self.metadatas.values():
            for table in metadata.tables.values():
                table.to_metadata(m)
        return m

    def get_engine(self, bind=None):
        """Return the SQLAlchemy engine object.

        :param bind: when binds are used, this argument selects which of the
                     binds to return an engine for.
        """
        if self.engines is None:
            with self.lock:
                if self.engines is None:  # pragma: no cover
                    self._create_engines()
        return self.engines.get(bind)

    def bind_names(self):
        return [bind for bind in self.engines if bind is not None]

    def create_all(self):
        """Create the database tables.

        Only tables that do not already exist are created. Existing tables are
        not modified.
        """
        engine = self.get_engine()
        if engine:
            self.metadatas[None].create_all(engine)
        for bind in self.binds or {}:
            self.metadatas[bind].create_all(self.get_engine(bind))

    def drop_all(self):
        """Drop all the database tables.

        Note that this is a destructive operation; data stored in the
        database will be deleted when this method is called.
        """
        engine = self.get_engine()
        if engine:
            self.metadatas[None].drop_all(engine)
        for bind in self.binds or {}:
            self.metadatas[bind].drop_all(self.get_engine(bind))

    def Session(self):
        """Return a database session.

        The recommended way to use the SQLAlchemy session is as a context
        manager::

            with db.Session() as session:
                # work with the session here

        The context manager automatically closes the session at the end. A
        session can also be created without a context manager::

            session = db.Session()

        When the session is created in this way, ``session.close()`` must be
        called when the session isn't needed anymore.
        """
        return self.session_class(
            bind=self.get_engine(), binds=self.table_binds, future=True)

    @contextmanager
    def begin(self):
        """Context manager for a database transaction.

        Upon entering the context manager block, a new session is created and
        a transaction started on it. If any errors occur inside the context
        manager block, then the transation is rolled back. If no errors occur,
        the transaction is committed. In both cases the session is then closed.

        Example usage::

            with db.begin() as session:
                # work with the session here
                # a commit (on success) or rollback (on error) is automatic
        """
        with self.Session() as session:
            with session.begin():
                yield session
