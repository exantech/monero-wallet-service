import peewee
from peewee import SQL

from .base import database
from .wallet import Wallet


class Output(peewee.Model):
    wallet = peewee.ForeignKeyField(Wallet)
    source = peewee.TextField(index=True)
    outputs = peewee.TextField()
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = database
