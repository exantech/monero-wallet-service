from flask import jsonify, request
import json
from models import Proposal, ProposalDecision
from api import app
from .auth import authentication, wallet_required
from .exceptions import APIError
from .utils import validate_json_params


@app.route("/api/v1/tx_proposals", methods=["GET"])
@authentication
@wallet_required
def ListProposalsEndpoint(session, wallet):
    if request.args.get('signing') == 'true':
        proposals = Proposal.select().where(Proposal.wallet == wallet, Proposal.status == 'signing')
    else:
        proposals = Proposal.select().where(Proposal.wallet == wallet)
    proposals = list(proposals)
    return jsonify([proposal.serialize() for proposal in proposals])


@app.route("/api/v1/tx_proposals", methods=["POST"])
@validate_json_params("destination_address", "description", "signed_transaction", "amount", "fee")
@authentication
@wallet_required
def CreateProposalEndpoint(session, wallet, data):
    pk = session.public_key
    amount = int(data['amount'])
    fee = int(data['fee'])

    if Proposal.select().where(Proposal.wallet == wallet, Proposal.status == 'signing').exists():
        raise APIError("Only one open proposal can exist at the time", status_code=409)

    proposal = Proposal.create(
        wallet=wallet,
        destination_address=data['destination_address'],
        description=data['description'],
        proposal_id=Proposal.generate_unique_id(),
        amount=amount,
        fee=fee,
    )

    # create first transaction approve
    ProposalDecision.create(
        proposal=proposal,
        signed_transaction=data['signed_transaction'],
        source=pk,
        approved=True,
    )

    # send message to all wallet participants
    app.redis.publish("stub:new_tx_proposal", proposal.proposal_id)
    app.redis.publish("stream:new_proposal", json.dumps({
        "wallet_id": wallet.id,
        "public_key": pk,
        "multisig": wallet.multisig_source,
        "proposal_id": proposal.proposal_id}))

    return jsonify({'proposal_id': proposal.proposal_id})


@app.route("/api/v1/tx_proposals/<proposal_id>", methods=["GET"])
@authentication
@wallet_required
def ProposalEndpoint(session, wallet, proposal_id):
    proposal = Proposal.select().where(Proposal.proposal_id == proposal_id, Proposal.wallet == wallet).first()
    if not proposal:
        raise APIError("Proposal not found", status_code=404)
    return jsonify(proposal.serialize())


@app.route("/api/v1/tx_proposals/<proposal_id>/decision", methods=["HEAD"])
@authentication
@wallet_required
def ProposalDecisionLock(session, wallet, proposal_id):
    result = app.redis.set("lock:%s" % wallet.source, session.id, ex=25, nx=True)
    if result:
        return jsonify({"status": "ok"})
    else:
        raise APIError("Lock can't be acquired", status_code=409)


@app.route("/api/v1/tx_proposals/<proposal_id>/decision", methods=["POST", "PUT"])
@validate_json_params("approved", "approval_nonce")
@authentication
@wallet_required
def ProposalDecisionEndpoint(session, wallet, data, proposal_id):
    pk = session.public_key

    lock = app.redis.get("lock:%s" % wallet.source)
    if not lock or lock.decode('ascii') != session.id:
        raise APIError("Proposal signing locked for 25 seconds", status_code=409)

    proposal = Proposal.select().where(
        Proposal.proposal_id == proposal_id,
        Proposal.wallet == wallet,
    ).first()
    if not proposal:
        raise APIError("Proposal not found", status_code=404)

    existing_decision = ProposalDecision.select().where(
        ProposalDecision.proposal == proposal,
        ProposalDecision.source == pk,
    ).first()
    if existing_decision:
        existing_decision.delete_instance()
        # raise APIError("Decision already made", status_code=400)

    if bool(data['approved']):
        if 'signed_transaction' not in data:
            raise APIError("Field 'signed_transaction' must be supplied")

        if proposal.approvals != int(data['approval_nonce']):
            raise APIError("Approval nonce must be actual number of approvals", status_code=400)

        signed_transaction = data['signed_transaction']
    else:
        signed_transaction = ""

    ProposalDecision.create(
        proposal=proposal,
        approved=bool(data['approved']),
        signed_transaction=signed_transaction,
        source=pk,
    )

    if proposal.approvals >= wallet.signers:
        proposal.status = 'approved'
        proposal.save()
    if proposal.rejects > (wallet.participants - wallet.signers):
        proposal.status = 'rejected'
        proposal.save()

    # TODO: check number of received decisions
    # if reject_decisions.count() > (wallet.participans - wallet.signers):
    #     reject_proposal
    # if approve_decisions.count() == wallet.signers:
    #     send transaction to monero network
    #     send tx_relay_status notification

    # send message to all wallet participants
    app.redis.publish("stub:tx_proposal_status", proposal.proposal_id)
    app.redis.publish("stream:proposal_status", json.dumps({
        "wallet_id": wallet.id,
        "public_key": pk,
        "multisig": wallet.multisig_source,
        "status": proposal.status,
        "proposal_id": proposal.proposal_id
    }))

    app.redis.delete("lock:%s" % wallet.source)

    return ('', 204)


@app.route("/api/v1/tx_relay_status/<proposal_id>", methods=["POST"])
@validate_json_params("tx_id")
@authentication
@wallet_required
def TxRelayStatusEndpoint(session, wallet, data, proposal_id):
    proposal = Proposal.select().where(Proposal.proposal_id == proposal_id,
                                       Proposal.wallet == wallet).first()
    if not proposal:
        raise APIError("Proposal not found", status_code=404)

    if proposal.status == 'relayed':
        return ('', 208)
    elif proposal.status != 'approved':
        raise APIError("Proposal is not approved", status_code=403)

    proposal.tx_id = ','.join(data['tx_id'])
    proposal.status = 'relayed'
    proposal.save()

    app.redis.publish("stream:proposal_status", json.dumps({
        "wallet_id": wallet.id,
        "public_key": pk,
        "multisig": wallet.multisig_source,
        "status": proposal.status,
        "proposal_id": proposal.proposal_id
    }))

    return jsonify(proposal.serialize())

@app.route("/api/v1/tx_proposals/<proposal_id>", methods=["DELETE"])
@authentication
@wallet_required
def TxProposalDeleteEndpoint(session, wallet, proposal_id):
    proposal = Proposal.select().where(Proposal.proposal_id == proposal_id,
                                       Proposal.wallet == wallet).first()
    if not proposal:
        raise APIError("Proposal not found", status_code=404)

    proposal.status = 'deleted'
    proposal.save()

    app.redis.publish("stream:proposal_status", json.dumps({
        "wallet_id": wallet.id,
        "public_key": pk,
        "multisig": wallet.multisig_source,
        "status": proposal.status,
        "proposal_id": proposal.proposal_id
    }))

    return jsonify(proposal.serialize())
