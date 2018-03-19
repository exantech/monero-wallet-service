import asyncio
import random
import aioredis
from aiohttp import web
import json

from .base import objects, loop
from .streaming import MultisigInfoStream, ExtraMultisigInfoStream, WalletInfoStream
from .auth import authentication, wallet_required
from models import Proposal

async def ExtraMultisigInfoEndpoint(request):
    return web.HTTPNoContent()

async def OutputsEndpoint(request):
    return web.HTTPNoContent()

async def TxProposalNewEndpoint(request):
    return

async def ProposalDecisionEndpoint(request):
    proposal_id = request.match_info['proposal_id']

    return web.HttpNoContent()


async def ProposalInfoEndpoint(request):
    return web.json_response({"signed_transaction": "0x7312bade63781821bf"})


async def TxProposalListEndpoint(request):
    return web.json_response([{"amount": 1000,
                                   "fee": 3,
                                   "approvals": ["0xe25198d9d00511a4ffe661841a9be9ba",],
                                   "rejects": [],
                                   "proposal_id": 1488,
                                   "destination_address": "44CP9CbAPymKYCZSn6Yesa8nnQvSQvxSC7td5uGho2iybPZnVjPbqs72ptJZ6XfUBp3KwMCreeh9HK8nAbsDFuXA4Yn3K61",
                                   "description": "donation",
                                   "status": "signing"}])


# ---------
# STREAMING
# ---------

async def OutputsRequestStream(request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe('stub:outputs_request')
    subscriber = subscriber[0]

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        if msg is None:
            break
        await stream.write(b"data: %s\r\n\r\n" % bytes(msg))

    await stream.write_eof()
    await sub.unsubscribe('stub:outputs_request')

    return stream


async def OutputsStream(request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe('stub:outputs')
    subscriber = subscriber[0]

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        if msg is None:
            break
        await stream.write(b"data: %s\r\n\r\n" % bytes(msg))

    await stream.write_eof()
    await sub.unsubscribe('stub:outputs')

    return stream


async def TxProposalStatusStream(request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe('stub:tx_proposal_status')
    subscriber = subscriber[0]

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        if msg is None:
            break
        await stream.write(b"data: %s\r\n\r\n" % bytes(msg))

    await stream.write_eof()
    await sub.unsubscribe('stub:tx_proposal_status')

    return stream


async def TxRelayStatusStream(request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe('stub:tx_relay_status')
    subscriber = subscriber[0]

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        if msg is None:
            break
        await stream.write(b"data: %s\r\n\r\n" % bytes(msg))

    await stream.write_eof()
    await sub.unsubscribe('stub:tx_relay_status')

    return stream


@authentication
@wallet_required
async def NewTxProposalStream(session, wallet, request):
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)
    sub = await aioredis.create_redis('redis://localhost')
    subscriber = await sub.subscribe('stub:new_tx_proposal')
    subscriber = subscriber[0]
    pk = session.public_key

    while (await subscriber.wait_message()):
        msg = await subscriber.get()
        if wallet is None:
            break
        if msg is None:
            continue

        try:
            proposal = await objects.get(
                Proposal.select().where(Proposal.proposal_id == msg, Proposal.wallet == wallet.id)
            )
        except Proposal.DoesNotExist:
            continue
        proposal_json = '%s\r\n' % json.dumps(proposal.serialize())
        await stream.write(
            bytes(proposal_json, 'utf-8')
            # b"data: %s\r\n\r\n" % bytes(msg)
        )

    await stream.write_eof()
    await sub.unsubscribe('stub:new_tx_proposal')

    return stream


def setup_routes(streamer):
    # streaming
    streamer.router.add_route('GET', "/api/v1/stream/extra_multisig_info", ExtraMultisigInfoStream)
    streamer.router.add_route('GET', "/api/v1/stream/outputs_request", OutputsRequestStream)
    streamer.router.add_route('GET', "/api/v1/stream/outputs", OutputsStream)
    streamer.router.add_route('GET', "/api/v1/stream/tx_proposal_status", TxProposalStatusStream)
    streamer.router.add_route('GET', "/api/v1/stream/tx_relay_status", TxRelayStatusStream)
    streamer.router.add_route('GET', "/api/v1/stream/multisig_info", MultisigInfoStream)
    streamer.router.add_route('GET', "/api/v1/stream/wallet_info", WalletInfoStream)
    streamer.router.add_route('GET', "/api/v1/stream/new_tx_proposal", NewTxProposalStream)


async def cleanup_bg_tasks(app):
    await app['redis'].quit()


async def main():
    streamer = web.Application()
    streamer['redis'] = await aioredis.create_redis('redis://localhost')
    streamer.on_cleanup.append(cleanup_bg_tasks)

    setup_routes(streamer)

    return streamer
