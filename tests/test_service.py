from aiohttp import web
from service.core import cleanup_bg_tasks, setup_routes
import aioredis


async def _get_test_streamer(loop):
    streamer = web.Application(loop=loop)
    streamer['redis'] = await aioredis.create_redis('redis://localhost')
    streamer.on_cleanup.append(cleanup_bg_tasks)

    setup_routes(streamer)

    return streamer


async def test_streamer(aiohttp_client, loop):
    app = await _get_test_streamer(loop)
    client = await aiohttp_client(app)

    headers = {
        'X-Nonce': '1',
        'X-Session-Id': '79f8e6071bba3272728a63eab8e668682019a71bd66b61b0',
        'X-Signature': '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f',
    }
    stream = await client.get('/api/v1/stream/new_tx_proposal', headers=headers)
    assert stream.status == 200

    text = await stream.text()
    assert False