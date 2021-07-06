import unittest
from alchemical import Alchemical


class TestCore(unittest.TestCase):
    def test_read_write(self):
        db = Alchemical('sqlite://')

        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128))

        db.create_all()

        with db.begin() as session:
            for name in ['mary', 'joe', 'susan']:
                session.add(User(name=name))

        with db.session() as session:
            all = session.execute(db.select(User)).scalars().all()
        assert len(all) == 3

        db.drop_all()
        db.create_all()

        with db.session() as session:
            all = session.execute(db.select(User)).scalars().all()
        assert len(all) == 0
