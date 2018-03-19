import os
import datetime

from flask import Flask, request, send_from_directory, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from .wallets import CreateWalletEndpoint, JoinWalletEndpoint
from .keys import ChangePublicKeyEndpoint
from .info import WalletInfoEndpoint
from .proposals import CreateProposalEndpoint, ListProposalsEndpoint
from .outputs import OutputsEndpoint, OutputsListEndpoint
from .session import OpenSessionEndpoint
from api import app
from .auth import authentication
from .utils import validate_json_params, generate_random_string
from .push import PushRegisterEndpoint

import logging
logging.basicConfig(level=logging.INFO)


@app.route("/")
def IndexEndpoint():
    return """<h1>Monero Wallet Service</h1>
API is described at <a href="/api/doc">Swagger API docs</a>
(<a href="/api/doc_classic">Classic Swagger UI</a>)"""


@app.route("/test_auth", methods=["POST"])
@validate_json_params("payload")
@authentication
def test_auth(session, data):
    pk = session.public_key
    ii = session.id
    return ('pk:%s, id: %s, data:%s' % (pk, ii, data), 200)


### SWAGGER SETUP

@app.route("/api/doc/swagger.yaml")
def swagger():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(root_dir, "swagger.yaml", as_attachment=False)


@app.route("/api/doc_classic/")
@app.route("/api/doc_classic/<path:path>")
def swagger_index(path=None):
    if not path or path == '/':
        path = 'index.html'
    root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return send_from_directory(root_dir, "swagger/%s" % path, as_attachment=False)


SWAGGER_URL = '/api/doc'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/api/doc/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


    # app.router.add_route('POST', "/api/v1/extra_multisig_info", ExtraMultisigInfoEndpoint)
    # app.router.add_route('POST', "/api/v1/outputs", OutputsEndpoint)


    # # tx endpoints
    # app.router.add_route('POST', "/api/v1/tx_proposals", TxProposalNewEndpoint)
    # app.router.add_route('GET', "/api/v1/tx_proposals", TxProposalListEndpoint)
    # app.router.add_route('GET', "/api/v1/tx_proposals/{proposal_id}", ProposalInfoEndpoint)
    # app.router.add_route('PUT', "/api/v1/tx_proposals/{proposal_id}/decision", ProposalDecisionEndpoint)
