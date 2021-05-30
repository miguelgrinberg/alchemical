from contextlib import contextmanager
import re
from threading import Lock

import sqlalchemy
import sqlalchemy.event
import sqlalchemy.orm
from sqlalchemy.orm.decl_api import DeclarativeMeta

try:
    from greenlet import getcurrent as _ident_func
except ImportError:
    from threading import get_ident as _ident_func


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
                    self.event = sqlalchemy.event
                    self.Model = sqlalchemy.orm.declarative_base(
            cls=BaseModel, metaclass=Meta)

    def _create_engines(self):
        options = (self.engine_options
            if not callable(self.engine_options)
            else self.engine_options(None))
        options.setdefault('future', True)
        self.engines = {None: self.create_engine(self.url, **options)}
        self.table_binds = {}
        for bind, url in (self.binds or {}).items():
            options = (self.engine_options
                if not callable(self.engine_options)
                else self.engine_options(bind))
            options.setdefault('future', True)
            self.engines[bind] = self.create_engine(url, **options)
            for table in self.get_tables_for_bind(bind):
                self.table_binds[table] = self.engines[bind]

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
        tables = self._get_tables_for_bind(None)
        self.Model.metadata.create_all(self.get_engine(), tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            self.Model.metadata.create_all(self.get_engine(bind),
                                           tables=tables)

    def drop_all(self):
        tables = self._get_tables_for_bind(None)
        self.Model.metadata.drop_all(self.get_engine(), tables=tables)
        for bind in self.binds or {}:
            tables = self._get_tables_for_bind(bind)
            self.Model.metadata.drop_all(self.get_engine(bind), tables=tables)

    def session(self):
        return self.Session(bind=self.get_engine(), binds=self.table_binds,
                            future=True)

    @contextmanager
    def begin(self):
        with self.session() as session:
            with session.begin():
                yield session
