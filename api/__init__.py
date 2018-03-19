from flask import Flask, jsonify
import redis

from .exceptions import APIError


app = Flask(__name__, static_url_path='')
app.redis = redis.StrictRedis(host="localhost")

@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

import api.views