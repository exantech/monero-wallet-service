from flask import request
import json

from models import Wallet, MultisigInfo
from api import app
from .utils import validate_json_params
from .exceptions import APIError
from .auth import authentication, wallet_required


@app.route("/api/v1/change_public_key", methods=["POST"])
@validate_json_params("public_key")
@authentication
@wallet_required
def ChangePublicKeyEndpoint(session, wallet, data):
    """Set multisig key instead of regular"""
    key = data['public_key']
    pk = session.public_key

    if wallet.status == "ready":
        changed_key = app.redis.hget("m_sessions", session.id)
        if changed_key is None:
            app.redis.hset("m_sessions", session.id, key)
        return ('', 200)

    # wallet = Wallet.get((Wallet.source == pk) | (Wallet.multisig_source == pk))
    if wallet.status not in ("changing_keys", "fulfilled"):
        raise APIError("Wallet is not ready for key change")

    # update wallet source if there is initiator key change request
    if wallet.source == pk:
        wallet.multisig_source = key
        wallet.save()

    # update multisig info source for this wallet and current session
    q = (MultisigInfo.update(multisig_source=key).where(
        (MultisigInfo.source == pk) &
        (MultisigInfo.wallet == wallet) &
        (MultisigInfo.level == 0)
    ))
    q.execute()

    changed_keys = MultisigInfo.select().where((MultisigInfo.wallet == wallet) &
                                               (MultisigInfo.level == 0) &
                                               (MultisigInfo.multisig_source.is_null(False))
                                               ).count()
    if changed_keys == wallet.participants:
        wallet.status = 'ready'
        wallet.save()

    app.redis.publish("stream:wallet_info:%s" % wallet.id, wallet.status)
    data = {
        'wallet_id': wallet.id,
        'public_key': pk,
        'status': wallet.status,
        'changed_keys': len(wallet.changed_keys),
        'joined': len(wallet.multisig_infos),
        'participants': wallet.participants,
        'signers': wallet.signers,
    }

    print (data)
    app.redis.publish("stream:wallet_info", json.dumps(data))

    # replace key in session
    app.redis.hset("m_sessions", session.id, key)

    return ('', 204)
