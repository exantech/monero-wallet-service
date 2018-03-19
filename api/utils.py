import os
import binascii
from functools import wraps

import ujson
from flask import request

from .exceptions import APIError


def validate_json_params(*fields):
    def internal(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json(force=True)
            try:
                for field in fields:
                    if field not in data: raise Exception("Field '%s' must be supplied" % field)

            except Exception as e:
                raise APIError(str(e))

            return func(data, *args, **kwargs)

        return wrapper

    return internal


def generate_random_string(length=36):
    return binascii.b2a_hex(os.urandom(length)).decode('ascii')
