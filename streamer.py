from aiohttp import web

from service.core import main, loop

if __name__ == "__main__":
    app = loop.run_until_complete(main())
    web.run_app(app, host="127.0.0.1", port=8036)
