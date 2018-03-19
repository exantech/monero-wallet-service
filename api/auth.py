from functools import wraps
from collections import namedtuple
import re

from flask import request

from api import app
from .exceptions import APIError
from .nonce import check_nonce
from .base58 import decode
from models import Wallet, MultisigInfo
import cryptonote

Session = namedtuple('Session', ["public_key", "id"])


def authentication(func):
    @wraps(func)
    def f(*args, **kwargs):
        session_id = request.headers.get("x-session-id", "")
        signature = request.headers.get("x-signature", "")
        nonce = request.headers.get("x-nonce", "")
        data = request.get_data()

        if not session_id or not signature:
            raise APIError("x-session-id and x-signature headers are mandatory")

        if not check_nonce(nonce, session_id, app.redis):
            raise APIError("nonce is too low or invalid", 410)

        session = app.redis.hget("m_sessions", session_id)  # FIXME
        if not session:
            session = app.redis.hget("sessions", session_id)

        if not session:
            raise APIError("invalid or expired session id", 403)

        public_key = session.split(b":")[0]

        msg = data + session_id.encode("ascii") + bytes(str(nonce), 'ascii')

        if not (signature.startswith('SigV1') or
                signature.startswith('SigPkV1') or
                signature.startswith('SigMultisigPkV1') or
                signature.startswith('MultisigxV1')):
            raise APIError("invalid signature header", 400)

        signature = re.sub(r'^(SigV1|SigPkV1|SigMultisigPkV1|MultisigxV1)', '', signature)
        signature = bytes.fromhex(decode(signature))

        if len(signature) != 64 or not cryptonote.check_signature(msg, bytes.fromhex(public_key.decode('ascii')), signature):
            raise APIError("invalid signature", 403)

        session_data = Session(public_key=public_key.decode('ascii'), id=session_id)

        return func(session_data, *args, **kwargs)
    return f


def wallet_required(func):
    @wraps(func)
    def f(session_data, *args, **kwargs):
        """get wallet by session.public_key"""
        pk = session_data.public_key
        wallet = Wallet.select().join(MultisigInfo).where(
            (Wallet.source == pk) |
            (Wallet.multisig_source == pk) |
            (MultisigInfo.source == pk) |
            (MultisigInfo.multisig_source == pk)
        ).first()

        if not wallet:
            raise APIError("No wallet assigned to your key", status_code=400)
        return func(session_data, wallet, *args, **kwargs)
    return f
