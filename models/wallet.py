import peewee
from peewee import SQL
from playhouse.postgres_ext import ArrayField
from .base import database


WALLET_STATUS_CHOICES = [(x, x) for x in (
    "new",
    "fulfilled",
    "changing_keys",
    "ready",
)]


class Wallet(peewee.Model):
    name = peewee.CharField(null=True)
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    participants = peewee.IntegerField()
    signers = peewee.IntegerField()
    invite_code = peewee.CharField(null=True)
    status = peewee.CharField(choices=WALLET_STATUS_CHOICES, default="new", index=True)
    source = peewee.TextField(index=True)  # creator's pub key
    multisig_source = peewee.TextField(index=True, null=True)
    supported_protocols = ArrayField(peewee.CharField, null=True)
    level = peewee.IntegerField(default=0)  # M - N, 0 for 3/3, 1 for 2/3 and so on

    @property
    def is_ready(self):
        return self.status == "ready"

    @property
    def is_fulfilled(self):
        return self.status == "fulfilled"

    @property
    def is_new(self):
        return self.status == "new"

    @property
    def is_changing_keys(self):
        return self.status == "changing_keys"

    @property
    def changed_keys(self):
        return MultisigInfo.select().where(
            (MultisigInfo.wallet == self) &
            (MultisigInfo.multisig_source.is_null(False))
        )

    @property
    def multisig_infos(self):
        return MultisigInfo.select().where(
            (MultisigInfo.wallet == self) &
            (MultisigInfo.level == 0)
        )

    class Meta:
        database = database


class MultisigInfo(peewee.Model):
    wallet = peewee.ForeignKeyField(Wallet)
    info = peewee.TextField()
    source = peewee.TextField(index=True)
    multisig_source = peewee.TextField(index=True, null=True)
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    level = peewee.IntegerField(default=0)
    device_uid = peewee.TextField(null=True)

    class Meta:
        database = database
