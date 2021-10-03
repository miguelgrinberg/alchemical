import asyncio
import sys
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from alchemical.aio import Alchemical

app = FastAPI()
db = Alchemical('sqlite:///app.db')


class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


@app.get('/')
async def index():
    async with db.Session() as session:
        users = await session.scalars(User.select())
        return {'users': [u.name for u in users]}


async def add():
    """Add test user."""
    async with db.begin() as session:
        session.add(User(name='test'))


if sys.argv[1] == 'init':
    asyncio.run(db.create_all())
elif sys.argv[1] == 'add':
    asyncio.run(add())
else:
    raise RuntimeError('Invalid command')
