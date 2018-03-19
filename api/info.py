from flask import request, jsonify
from api import app
from .auth import authentication, wallet_required
from .exceptions import APIError
from .nonce import get_nonce
from models import MultisigInfo, Proposal, ProposalDecision, Wallet


@app.route("/api/v1/info/wallet", methods=["GET"])
@authentication
@wallet_required
def WalletInfoEndpoint(session, wallet):
    data = {
        'status': wallet.status,
        'changed_keys': wallet.changed_keys.count(),
        'joined': wallet.multisig_infos.count(),
        'participants': wallet.participants,
        'signers': wallet.signers,
    }

    return jsonify(data)

@app.route("/api/v1/info/scheme", methods=["GET"])
def BasicWalletInfoEndpoint():
    invite_code = request.args.get('invite_code')
    try:
        wallet = Wallet.get(invite_code=invite_code)
    except Wallet.DoesNotExist:
        raise APIError("Wallet not found", status_code=404)

    return get_wallet_scheme(wallet)


@app.route("/api/v1/info/wallet_scheme", methods=["GET"])
def ExistsWalletInfoEndpoint():
    pk = request.args.get('public_key')
    wallet = Wallet.select().join(MultisigInfo).where(
        (Wallet.source == pk) |
        (Wallet.multisig_source == pk) |
        (MultisigInfo.source == pk) |
        (MultisigInfo.multisig_source == pk)
    ).first()

    if not wallet:
        raise APIError("Wallet not found", status_code=404)

    return get_wallet_scheme(wallet)


@app.route("/api/v1/info/multisig", methods=["GET"])
@authentication
@wallet_required
def MultisigInfoEndpoint(session, wallet):
    multisigs = MultisigInfo.select().where(
        (MultisigInfo.wallet == wallet) &
        (MultisigInfo.level == 0)
    )
    data = {"multisig_infos": [{"multisig_info": x.info} for x in multisigs]}

    return jsonify(data)


@app.route("/api/v1/info/extra_multisig", methods=["GET"])
@authentication
@wallet_required
def ExtraMultisigInfoDataEndpoint(session, wallet, level=1):
    return get_extra_multisig_info(wallet, level)


@app.route("/api/v1/info/extra_multisig/<level>", methods=["GET"])
@authentication
@wallet_required
def ExtraMultisigInfoSelectedLevelDataEndpoint(session, wallet, level):
    try:
        level = int(level)
    except ValueError:
        raise APIError("level is invalid", 400)

    return get_extra_multisig_info(wallet, level)


@app.route("/api/v1/info/new_tx_proposal", methods=["GET"])
@authentication
@wallet_required
def NewProposalEndpoint(session, wallet):
    proposals = Proposal.select().join(ProposalDecision).where(
        Proposal.wallet == wallet.id,
        ProposalDecision.source != wallet.source
    )

    return jsonify([proposal.serialize() for proposal in proposals])


@app.route("/api/v1/info/nonce", methods=["GET"])
def nonce_endpoint():
    session_id = request.args.get('session_id')
    if not session_id:
        raise APIError("session_id is mandatory", 400)

    nonce = get_nonce(session_id, app.redis)
    if not nonce:
        raise APIError("nonce is undefined", 500)

    data = {'nonce': nonce}
    return jsonify(data)


def get_extra_multisig_info(wallet, level):
    multisigs = MultisigInfo.select().where(
        (MultisigInfo.wallet == wallet) &
        (MultisigInfo.level == level)
    )
    data = {"extra_multisig_infos": [{"extra_multisig_info": x.info} for x in multisigs]}

    return jsonify(data)


def get_wallet_scheme(wallet):
    data = {
        'name': wallet.name,
        'participants': wallet.participants,
        'signers': wallet.signers,
    }

    return jsonify(data)
