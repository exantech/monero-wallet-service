import peewee
from peewee import SQL

from .base import database, objects
from .wallet import Wallet


class PushRegistration(peewee.Model):
    public_key = peewee.TextField()
    device_uid = peewee.TextField()
    endpoint = peewee.TextField()
    token = peewee.TextField(null=True)
    platform = peewee.CharField()
    locale = peewee.CharField()
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = database

        indexes = (
            (('platform', 'device_uid', 'public_key'), True),
        )
