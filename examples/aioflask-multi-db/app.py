from aioflask import Flask
from alchemical.aioflask import Alchemical
from flask_migrate import Migrate

app = Flask(__name__)
app.config['ALCHEMICAL_DATABASE_URI'] = 'sqlite:///app1.db'
app.config['ALCHEMICAL_BINDS'] = {
    "db1": "sqlite:///app2.db",
}

db = Alchemical(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))


class Group(db.Model):
    __bind_key__ = 'db1'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))


@app.cli.command()
async def add():
    """Add test users."""
    async with db.begin() as session:
        session.add(User(name='test'))
        session.add(Group(name='group'))
