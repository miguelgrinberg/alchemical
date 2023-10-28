import asyncio
import sys
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from alchemical.aio import Alchemical, Model


class User(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


app = FastAPI()
db = Alchemical('sqlite:///app.db')


@app.get('/')
async def index():
    async with db.Session() as session:
        users = await session.scalars(User.select())
        return {'users': [u.name for u in users]}


async def add():
    """Add test user."""
    async with db.begin() as session:
        session.add(User(name='test'))


arg = sys.argv[1] if len(sys.argv) > 1 else None
if arg == 'init':
    asyncio.run(db.create_all())
elif arg == 'add':
    asyncio.run(add())
elif __name__ == '__main__':
    raise RuntimeError('Invalid command')
