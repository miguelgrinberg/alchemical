from flask import Flask
from sqlalchemy import Column, Integer, String
from alchemical.flask import Alchemical, Model
from flask_migrate import Migrate

class User(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


app = Flask(__name__)
app.config['ALCHEMICAL_DATABASE_URI'] = 'sqlite:///app.db'
db = Alchemical(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    with db.Session() as session:
        users = session.scalars(User.select())
        return 'Users: ' + ', '.join([u.name for u in users])


@app.cli.command()
def add():
    """Add test user."""
    with db.begin() as session:
        session.add(User(name='test'))
