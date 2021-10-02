from flask import Flask
from sqlalchemy import Column, Integer, String
from alchemical.flask import Alchemical
from flask_migrate import Migrate

app = Flask(__name__)
app.config['ALCHEMICAL_DATABASE_URI'] = 'sqlite:///app1.db'
app.config['ALCHEMICAL_BINDS'] = {
    "db1": "sqlite:///app2.db",
}

db = Alchemical(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


class Group(db.Model):
    __bind_key__ = 'db1'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


@app.route('/')
def index():
    with db.Session() as session:
        users = session.scalars(User.select())
        groups = session.scalars(Group.select())
        return ('Users: ' + ', '.join([u.name for u in users]) +
                '<br>Groups: ' + ', '.join([g.name for g in groups]))


@app.cli.command()
def add():
    """Add test users."""
    with db.begin() as session:
        session.add(User(name='test'))
        session.add(Group(name='group'))
