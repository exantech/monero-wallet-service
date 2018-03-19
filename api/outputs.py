import json
from flask import jsonify, request
from .auth import authentication, wallet_required
from .utils import validate_json_params
from api import app
from models import Output
import datetime


@app.route("/api/v1/outputs", methods=["POST"])
@validate_json_params("outputs")
@authentication
@wallet_required
def OutputsEndpoint(session, wallet, data):
    existing = Output.select().where(
        (Output.wallet == wallet) &
        (Output.source == session.public_key)).first()

    if existing:
        existing.outputs = data['outputs']
        existing.timestamp = datetime.datetime.now()
        existing.save()

    else:
        Output.create(
            wallet=wallet,
            source=session.public_key,
            outputs=data['outputs']
        )
    app.redis.hset('wallet_outputs_update', wallet.id, datetime.datetime.now().timestamp())
    return ('', 201)


@app.route("/api/v1/outputs", methods=["GET"])
@authentication
@wallet_required
def OutputsListEndpoint(session, wallet):
    try:
        last_update_timestamp = app.redis.hget('wallet_outputs_update', wallet.id) or 0.0
        if float(request.environ.get('HTTP_IF_MODIFIED_SINCE')) >= float(last_update_timestamp):
            return ('', 304)
    except:
        pass
    outputs = Output.select().where(Output.wallet == wallet)
    data = {
        'outputs': [out.outputs for out in outputs]
    }
    return jsonify(data)
