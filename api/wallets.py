from flask import request, jsonify
import json

from models import Wallet, MultisigInfo
from api import app
from .utils import validate_json_params, generate_random_string
from .exceptions import APIError
from .auth import authentication, wallet_required

def check_wallet_schema(data):
    min_value = 2

    if data['participants'] < min_value or data['signers'] < min_value:
        raise APIError("Participants and signers should be greater or equal than {0}".format(min_value))

    elif data['signers'] > data['participants']:
        raise APIError("Only M/N signing schemas are supported (M <= N)")


@app.route("/api/v1/create_wallet", methods=["POST"])
@validate_json_params("name", "signers", "participants", "multisig_info")
@authentication
def CreateWalletEndpoint(session, data):
    check_wallet_schema(data)
    pk = session.public_key
    invite_code = generate_random_string(48)

    if Wallet.select().where(Wallet.source == pk).exists():
        raise APIError("Shared wallet linked with your key is already exists", 409)

    level = data['participants'] - data['signers']

    device_uid = data.get('device_uid')
    wallet = Wallet.create(
        name=data['name'],
        signers=data['signers'],
        participants=data['participants'],
        invite_code=invite_code,
        level=level,
        source=pk)

    MultisigInfo.create(
        wallet=wallet.id,
        info=data['multisig_info'],
        level=0,
        device_uid=device_uid,
        source=pk)

    return jsonify({"invite_code": wallet.invite_code})


@app.route("/api/v2/create_wallet", methods=["POST"])
@validate_json_params("signers", "participants", "supported_protocols")
@authentication
def CreateWalletEndpointV2(session, data):
    check_wallet_schema(data)
    pk = session.public_key
    invite_code = generate_random_string(48)

    if Wallet.select().where(Wallet.source == pk).exists():
        raise APIError("Shared wallet linked with your key is already exists", 409)

    level = data['participants'] - data['signers']

    wallet = Wallet.create(
        signers=data['signers'],
        participants=data['participants'],
        invite_code=invite_code,
        supported_protocols=','.join(data['supported_protocols']),
        level=level,
        source=pk,
    )

    return jsonify({"invite_code": wallet.invite_code})


@app.route("/api/v1/wallet_invite", methods=["GET"])
@authentication
@wallet_required
def WalletInviteEndpoint(session, wallet):
    return jsonify({"invite_code": wallet.invite_code})


@app.route("/api/v1/join_wallet", methods=["POST"])
@validate_json_params("invite_code", "multisig_info")
@authentication
def JoinWalletEndpoint(session, data):
    pk = session.public_key
    try:
        wallet = Wallet.get(invite_code=data['invite_code'])
    except Wallet.DoesNotExist:
        raise APIError("Wallet not found", status_code=404)

    device_uid = data.get('device_uid')
    if device_uid is not None:
        if MultisigInfo.select().where((MultisigInfo.device_uid == device_uid) &
                                   (MultisigInfo.wallet_id == wallet.id)).exists():
            raise APIError("Already joined", status_code=409)

    if not wallet.is_new:
        try:
            multisig = MultisigInfo.get(source=pk)
        except MultisigInfo.DoesNotExist:
            raise APIError("Wallet is already fulfilled", status_code=409)

        return ('', 200)

    (info, created) = MultisigInfo.get_or_create(
        wallet=wallet.id,
        source=pk,
        level=0,
        device_uid=device_uid,
        defaults={"info": data['multisig_info']})

    if not created:
        info.info = data['multisig_info']
        info.save()

    app.redis.publish("stream:wallet_info:%s" % wallet.id, wallet.status)
    data2 = {
        'wallet_id': wallet.id,
        'public_key': pk,
        'status': wallet.status,
        'changed_keys': len(wallet.changed_keys),
        'joined': len(wallet.multisig_infos),
        'participants': wallet.participants,
        'signers': wallet.signers,
        'event': 'joined'
    }
    app.redis.publish("stream:wallet_info", json.dumps(data2))

    if wallet.multisig_infos.count() >= wallet.participants:
        if wallet.level > 0:
            wallet.status = "fulfilled"
        else:
            wallet.status = "changing_keys"
        wallet.save()

        app.redis.publish("stream:multisig_info:%s" % wallet.id, "complete")
        data2 = {
            "wallet_id": wallet.id,
            "public_key": pk,
            "multisig_infos": [{"multisig_info": x.info} for x in wallet.multisig_infos],
            "event": "completed"
        }
        app.redis.publish("stream:multisig_info", json.dumps(data2))

    return ('', 204)

def LevelEmpty(wallet, level):
    infos_count = MultisigInfo.select().where((MultisigInfo.wallet == wallet) & (MultisigInfo.level == level)).count()
    if infos_count < wallet.participants:
        return True
    else:
        return False

@app.route("/api/v1/extra_multisig_info", methods=["POST"])
@validate_json_params("extra_multisig_info")
@authentication
@wallet_required
def ExtraMultisigInfoEndpoint(session, wallet, data):
    if wallet.is_ready:
        raise APIError("Wallet is ready", status_code=400)

    if not wallet.is_fulfilled:
        raise APIError("Wallet is not fulfilled or changing keys", status_code=400)

    pk = session.public_key
    setup_extra_multisig_info(wallet, None, data['extra_multisig_info'], pk)

    return ('', 204)


@app.route("/api/v1/extra_multisig_info/<level>", methods=["POST"])
@validate_json_params("extra_multisig_info")
@authentication
@wallet_required
def ExtraMultisigInfoSelectedLevelEndpoint(session, wallet, data, level):
    try:
        level = int(level)
    except ValueError:
        raise APIError("level is invalid", 400)

    if wallet.is_ready:
        raise APIError("Wallet is ready", status_code=400)

    if not wallet.is_fulfilled:
        raise APIError("Wallet is not fulfilled or changing keys", status_code=400)

    pk = session.public_key
    setup_extra_multisig_info(wallet, level, data['extra_multisig_info'], pk)


def setup_extra_multisig_info(wallet, fixed_level, extra_multisig_info, pk):
    level = wallet.participants - wallet.signers

    if not fixed_level:
        level_process = level + 1
        for i in range(1, level + 1):
            print(i)
            is_empty = LevelEmpty(wallet, i)
            if is_empty:
                level_process = i
                break
    else:
        level_process = fixed_level

    if level_process == level+1:
        if not wallet.is_changing_keys:
            wallet.status = "changing_keys"
            wallet.save()

            app.redis.publish("stream:extra_multisig_info:%s" % wallet.id, "complete")

            multisig_infos = MultisigInfo.select().where((MultisigInfo.wallet == wallet) & (MultisigInfo.level == level_process))
            data2 = {
                "wallet_id": wallet.id,
                "public_key": pk,
                "extra_multisig_infos": [{"extra_multisig_info": x.info} for x in multisig_infos]
            }
            app.redis.publish("stream:extra_multisig_info", json.dumps(data2))
    else:
        (info, created) = MultisigInfo.get_or_create(
            wallet=wallet.id,
            source=pk,
            level=level_process,
            defaults={"info": extra_multisig_info})

        if not created:
            info.info = extra_multisig_info
            info.save()
