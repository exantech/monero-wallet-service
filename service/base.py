import asyncio

import aioredis
import peeweedbevolve
import peewee
import peewee_async

import logging
logging.basicConfig(level=logging.INFO)

from models.base import database

loop = asyncio.get_event_loop()
objects = peewee_async.Manager(database)

loop.set_debug(True)

database.set_allow_sync(False)
