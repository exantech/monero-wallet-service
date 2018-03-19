from aiohttp import web
import aiohttp
import aioredis
import ujson

import logging
logging.basicConfig(level=logging.INFO)

from .base import objects
from models import Wallet, MultisigInfo
from .auth import authentication, wallet_required


async def setup_stream(request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'application/x-json-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    return stream


async def wait_for_trigger(channel):
    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe(channel)
    subscriber = subscriber[0]

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        break

    return sub


async def write_stream(stream, data):
    data = ujson.dumps(data)
    data = b"%s\n" % bytes(data, 'ascii')
    await stream.write(data)


async def write_and_close(stream, data, channel, sub=None):
    await write_stream(stream, data)
    await stream.write_eof()

    # using old state here
    if sub is not None:
        await sub.unsubscribe(channel)


@authentication
@wallet_required
async def WalletInfoStream(session, wallet, request):
    stream = await setup_stream(request)
    channel = 'stream:wallet_info:%s' % wallet.id
    data = {
        'status': wallet.status,
        'changed_keys': await objects.count(wallet.changed_keys),
        'joined': await objects.count(wallet.multisig_infos),
        'participants': wallet.participants,
        'signers': wallet.signers,
    }
    await write_stream(stream, data)

    if wallet.status != 'ready':
        sub = await aioredis.create_redis('redis://localhost')
        subscriber = await sub.subscribe(channel)
        subscriber = subscriber[0]
        while await subscriber.wait_message():
            msg = await subscriber.get()
            data['status'] = msg
            data['changed_keys'] = await objects.count(wallet.changed_keys)
            data['joined'] = await objects.count(wallet.multisig_infos)
            await write_stream(stream, data)

            if msg == b'ready':
                break

        sub.unsubscribe(channel)
    return stream


@authentication
@wallet_required
async def MultisigInfoStream(session, wallet, request):
    stream = await setup_stream(request)
    sub = None
    if wallet.is_new:
        sub = await wait_for_trigger('stream:multisig_info:%s' % wallet.id)

    multisig_infos = await objects.execute(
        MultisigInfo.select().where((MultisigInfo.wallet == wallet) & (MultisigInfo.level == 0))
    )
    data = {"multisig_infos": [{"multisig_info": x.info} for x in multisig_infos]}

    await write_and_close(stream, data, 'stream:multisig_info:%s' % wallet.id, sub)

    return stream


@authentication
@wallet_required
async def ExtraMultisigInfoStream(session, wallet, request):
    stream = setup_stream(request)

    if wallet.is_new or wallet.is_fulfilled:
        sub = await aioredis.create_redis('redis://localhost')
        subscriber = await sub.subscribe('stream:extra_multisig_info:%s' % wallet.id)
        subscriber = subscriber[0]

        while (await subscriber.wait_message()):
            msg = await subscriber.get()
            break

    multisig_infos = await objects.execute(
        MultisigInfo.select().where((MultisigInfo.wallet == wallet) & (MultisigInfo.level == 1))
    )
    data = {"extra_multisig_infos": [{"extra_multisig_info": x.info} for x in multisig_infos]}
    await write_and_close(stream, data, 'stream:multisig_info:%s' % wallet.id, sub)

    # using old state here
    if wallet.is_new or wallet.is_fulfilled:
        await sub.unsubscribe('stream:extra_multisig_info:%s' % wallet.id)

    return stream
