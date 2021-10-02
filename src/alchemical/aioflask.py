from flask import g
from .aio import Alchemical as BaseAlchemical


class Alchemical(BaseAlchemical):
    """Create an Alchamical instance for an aioflask application.

    The following configuration variables are import from the Flask application
    instance:

    - ``ALCHEMICAL_DATABASE_URL``: the database connection URL.
    - ``ALCHEMICAL_BINDS``: a dictionary with additional databases to manage
                            with this database instance. The keys are the
                            names, and the values are the database URLs. A
                            model is then assigned to a specific bind with the
                            ``__bind_key__`` class attribute.
    - ``ALCHEMICAL_ENGINE_OPTIONS``: a dictionary with SQLAlchemy engine
                                     options.
    - ``ALCHEMICAL_AUTOCOMMIT``: If set to ``True``, the session is
                                 automatically committed at the end of the
                                 request if no errors have occurred.

    :param app: the aioflask application instance. If the application instance
                isn't provided here, the :func:`Alchemical.init_app` method
                must be called later to complete the initialization of the
                extension.
    """
    def __init__(self, app=None):
        super().__init__()
        if app:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Complete initialization of the Alchemical instance.

        :param app: the aioflask application instace.
        """
        database_url = app.config.get('ALCHEMICAL_DATABASE_URL')
        if database_url is None:
            database_url = app.config.get('ALCHEMICAL_DATABASE_URI')

        self.initialize(
            database_url,
            binds=app.config.get('ALCHEMICAL_BINDS'),
            engine_options=app.config.get('ALCHEMICAL_ENGINE_OPTIONS'))

        async def teardown_session(exc):
            if hasattr(g, 'alchemical_session'):
                if exc is None and app.config.get('ALCHEMICAL_AUTOCOMMIT'):
                    await g.alchemical_session.commit()
                await g.alchemical_session.close()
                del g.alchemical_session

        app.teardown_appcontext(teardown_session)

    @property
    def session(self):
        """Context-based database session.

        The session can be accessed as ``db.session``. An application context
        must be active.
        """
        if not hasattr(g, 'alchemical_session'):
            g.alchemical_session = self.Session()
        return g.alchemical_session
