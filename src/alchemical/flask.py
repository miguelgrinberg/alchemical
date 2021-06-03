from .core import Alchemical as BaseAlchemical


class Alchemical(BaseAlchemical):
    def __init__(self, app=None):
        super().__init__()
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.initialize(app.config['ALCHEMICAL_DATABASE_URI'],
                        binds=app.config.get('ALCHEMICAL_BINDS'))
