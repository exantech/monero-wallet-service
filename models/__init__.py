import peewee_async
from .wallet import Wallet, MultisigInfo
from .proposals import Proposal, ProposalDecision
from .outputs import Output


def init_db(db_name):
    try:
        from local_settings import DATABASE
    except ImportError:
        from settings import DATABASE

    db = peewee_async.PostgresqlDatabase(
        database=DATABASE['database'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
    )

    # db = peewee.PostgresqlDatabase(db_name, user='exante', password='111', host='localhost')
    db.set_allow_sync(True)
    db.create_tables([
        Wallet,
        MultisigInfo,
        Proposal,
        ProposalDecision,
    ])
