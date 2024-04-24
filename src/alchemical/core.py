from contextlib import contextmanager
import re
from threading import Lock

from sqlalchemy import create_engine, MetaData, select, update, delete
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DEFAULT_NAMING_CONVENTION = {
  "ix": "ix_%(column_0_label)s",
  "uq": "uq_%(table_name)s_%(column_0_name)s",
  "ck": "ck_%(table_name)s_%(constraint_name)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s"
}


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
    __metadatas__ = {}
    __tablename__ = TableNamer()

    def __init_subclass__(cls, **kwargs):
        bind_key = getattr(cls, '__bind_key__', None)
        if bind_key is not None:
            if bind_key not in cls.__metadatas__:
                cls.__metadatas__[bind_key] = MetaData()
            cls.metadata = cls.__metadatas__[bind_key]
        elif None not in cls.__metadatas__ and \
                getattr(cls, 'metadata', None) is not None:
            cls.__metadatas__[None] = cls.metadata
        super().__init_subclass__(**kwargs)

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


class Model(BaseModel, DeclarativeBase):
    __abstract__ = True


class BaseAlchemical:
    def __init__(self, url=None, binds=None, engine_options=None,
                 session_options=None, model_class=None,
                 naming_convention=None):
        self.engine_options = engine_options or {}
        self.session_options = session_options or {}
        self.naming_convention = DEFAULT_NAMING_CONVENTION \
            if naming_convention is None else naming_convention

        self.lock = Lock()
        self.url = None
        self.binds = None
        self.session_class = None
        self.engines = None
        self.table_binds = None
        self.Model = self._get_declarative_base(model_class)

        if url or binds:
            self.initialize(url, binds=binds)

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
        if url is None and binds is None:
            raise ValueError('"url" and/or "binds" must be set')

        self.url = url or self.url
        self.binds = binds or self.binds
        self.engine_options = engine_options or self.engine_options
        self.session_options = session_options or self.session_options
        self.session_class = None
        self.engines = None
        self.table_binds = None

    def _get_declarative_base(self, model_class):
        if model_class is None:
            return Model

        if not issubclass(model_class, BaseModel):
            # if the given model class does not have the Alchemical additions
            # we create a subclass of it with them
            class AlchemicalModel(BaseModel, model_class):
                __abstract__ = True

            return AlchemicalModel
        return model_class

    def _create_engines(self):
        options = (self.engine_options if not callable(self.engine_options)
                   else self.engine_options(None))
        options.setdefault('future', True)
        for metadata in self.metadatas.values():
            metadata.naming_convention = self.naming_convention
        self.engines = {}
        if self.url:
            self.engines[None] = self._create_engine(
                self._fix_url(self.url), **options)
        self.table_binds = {}
        for bind_key, url in (self.binds or {}).items():
            options = (self.engine_options if not callable(self.engine_options)
                       else self.engine_options(bind_key))
            options.setdefault('future', True)
            self.engines[bind_key] = self._create_engine(
                self._fix_url(url), **options)
            for table in self.Model.__metadatas__[bind_key].tables.values():
                self.table_binds[table] = self.engines[bind_key]

    def _fix_url(self, url):
        for prefix, updated_prefix in self.prefix_map.items():
            if url.startswith(f'{prefix}://'):
                url = f'{updated_prefix}://' + url[len(prefix) + 3:]
                break
        return url

    @property
    def metadatas(self):
        return self.Model.__metadatas__

    def get_engine(self, bind=None):
        """Return the SQLAlchemy engine object.

        :param bind: when binds are used, this argument selects which of the
                     binds to return an engine for.
        """
        if self.engines is None or self.engines.get(bind) is None:
            with self.lock:
                if self.engines is None or \
                        self.engines.get(bind) is None:  # pragma: no cover
                    self._create_engines()
        return self.engines.get(bind)

    def bind_names(self):
        return [bind for bind in self.engines if bind is not None]

    def is_async(self):
        """Return True if this database instance is asynchronous."""
        return False


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

    prefix_map = {'postgres': 'postgresql'}

    def _create_engine(self, url, *args, **kwargs):
        return create_engine(url, *args, **kwargs)

    def create_all(self):
        """Create the database tables.

        Only tables that do not already exist are created. Existing tables are
        not modified.
        """
        engine = self.get_engine()
        if engine:
            self.metadatas[None].create_all(engine)
        for bind_key in self.binds or {}:
            self.metadatas[bind_key].create_all(self.get_engine(bind_key))

    def drop_all(self):
        """Drop all the database tables.

        Note that this is a destructive operation; data stored in the
        database will be deleted when this method is called.
        """
        engine = self.get_engine()
        if engine:
            self.metadatas[None].drop_all(engine)
        for bind_key in self.binds or {}:
            self.metadatas[bind_key].drop_all(self.get_engine(bind_key))

    @property
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
        if self.session_class is None:
            options = {'future': True}
            options.update(self.session_options)
            self.session_class = sessionmaker(
                bind=self.get_engine(), binds=self.table_binds, **options)
        return self.session_class

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
