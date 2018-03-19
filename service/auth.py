from functools import wraps
from collections import namedtuple
from aiohttp import web
import ujson
import re

from models import Wallet, MultisigInfo
from .base import objects
from api.base58 import decode
import aioredis
import cryptonote

Session = namedtuple('Session', ["public_key", "id"])


async def check_nonce(request, session_id, redis):
    nonce = request.headers.get("x-nonce", "")
    try:
        nonce = int(nonce)
        last_nonce = int(await redis.hget("session_nonce", session_id))

        if last_nonce and nonce <= last_nonce:
            raise
        redis.hset("session_nonce", session_id, nonce)
    except:
        raise web.HTTPBadRequest(reason="nonce is invalid")

    return nonce


def authentication(func):
    @wraps(func)
    async def f(request):
        session_id = request.headers.get("x-session-id", "")
        redis = await aioredis.create_redis('redis://localhost')

        nonce = await check_nonce(request, session_id, redis)

        signature = request.headers.get("x-signature", "")

        if not session_id or not signature:
            raise web.HTTPBadRequest(reason="x-session-id and x-signature headers are mandatory")

        session = await redis.hget("m_sessions", session_id)  # FIXME
        if not session:
            session = await redis.hget("sessions", session_id)

        if not session:
            raise web.HTTPBadRequest(reason="invalid or expired session id")

        public_key = session.split(b":")[0].decode('ascii')

        data = b''
        msg = data + session_id.encode("ascii") + bytes(str(nonce), 'ascii')

        if not (signature.startswith('SigV1') or
                signature.startswith('SigPkV1') or
                signature.startswith('SigMultisigPkV1')):
            raise web.HTTPBadRequest(reason="invalid signature header")

        signature = re.sub(r'^(SigV1|SigPkV1|SigMultisigPkV1)', '', signature)
        signature = bytes.fromhex(decode(signature))

        pub_key = bytes.fromhex(public_key)
        if len(signature) != 64 or not cryptonote.check_signature(msg, pub_key, signature):
            raise web.HTTPBadRequest(reason="invalid signature")

        session_data = Session(public_key=public_key, id=session_id)

        return await func(session_data, request)
    return f


def wallet_required(func):
    @wraps(func)
    async def f(session_data, *args, **kwargs):
        """get wallet by session.public_key"""
        pk = session_data.public_key
        try:
            wallet = await objects.get(Wallet.select().where(Wallet.source == pk))
        except Wallet.DoesNotExist:
            try:
                wallet = await objects.get(Wallet.select().join(MultisigInfo).where(MultisigInfo.source == pk))
            except Wallet.DoesNotExist:
                raise web.HTTPBadRequest(reason="No wallet assigned to your key")

        return await func(session_data, wallet, *args, **kwargs)
    return f
