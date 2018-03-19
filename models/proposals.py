import peewee
from peewee import SQL

from .base import database, objects
from .wallet import Wallet


class Proposal(peewee.Model):
    wallet = peewee.ForeignKeyField(Wallet)
    destination_address = peewee.CharField()
    description = peewee.TextField()
    proposal_id = peewee.CharField()
    amount = peewee.BigIntegerField()
    fee = peewee.IntegerField()
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    tx_id = peewee.TextField(null=True)
    status = peewee.CharField(max_length=10, default="signing")

    class Meta:
        database = database

    def serialize(self):
        return {
            "destination_address": self.destination_address,
            "description": self.description,
            "proposal_id": self.proposal_id,
            "amount": self.amount,
            "fee": self.fee,
            "approvals": self.approve_list,
            "rejects": self.reject_list,
            "status": self.status,
            "last_signed_transaction": self.last_signed_transaction,
            "tx_id": self.tx_id.split(',') if self.tx_id else [],
        }

    def _get_decisions(self, approve):
        return ProposalDecision.select().where(
            ProposalDecision.proposal == self,
            ProposalDecision.approved == approve
        )

    @property
    def approvals(self):
        with objects.allow_sync():
            return self._get_decisions(approve=True).count()

    @property
    def approve_list(self):
        return [decision.source for decision in self._get_decisions(approve=True)]

    @property
    def rejects(self):
        with objects.allow_sync():
            return self._get_decisions(approve=False).count()

    @property
    def reject_list(self):
        return [decision.source for decision in self._get_decisions(approve=False)]

    @property
    def last_signed_transaction(self):
        with objects.allow_sync():
            last_decision = ProposalDecision.select().where(
                ProposalDecision.proposal == self,
                ProposalDecision.approved == True,
            ).order_by(
                ProposalDecision.timestamp.desc()
            ).first()
        if last_decision:
            return last_decision.signed_transaction
        return None

    @classmethod
    def generate_unique_id(cls):
        from api.utils import generate_random_string
        unique_id = generate_random_string()
        while cls.select().where(cls.proposal_id == unique_id).exists():
            unique_id = generate_random_string()
        return unique_id


class ProposalDecision(peewee.Model):
    proposal = peewee.ForeignKeyField(Proposal)
    approved = peewee.BooleanField()
    source = peewee.TextField(index=True)
    signed_transaction = peewee.TextField()
    timestamp = peewee.DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = database
