import datetime
from flask import jsonify
from api import app
from .utils import validate_json_params, generate_random_string


@app.route("/api/v1/open_session", methods=["POST"])
@validate_json_params("public_key")
def OpenSessionEndpoint(data):
    session_id = generate_random_string(24)
    # TODO: check for collisions
    payload = "%s:%s" % (data['public_key'], datetime.datetime.now().timestamp())
    app.redis.hset("sessions", session_id, payload)

    return jsonify({"session_id": session_id})


@app.route("/api/v2/open_session", methods=["POST"])
@validate_json_params("public_key", "user_agent")
def OpenSessionEndpointV2(data):
    session_id = generate_random_string(24)
    # TODO: check for collisions
    payload = "%s:%s" % (data['public_key'], datetime.datetime.now().timestamp())
    app.redis.hset("sessions", session_id, payload)
    app.redis.hset("user_agent", session_id, data['public_key'])

    return jsonify({"session_id": session_id})
