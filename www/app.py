import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

def index(request):
    #这里有两点需要注意的
    #1.最后必须设定content_type为text/html，否则浏览器会默认以文件下载该body，同时不按html格式解析标签
    #2.如果body内容含有中文，需要指定encode，否则会乱码

    return web.Response(body='<h1>你好！<h1>'.encode('gb2312'),content_type='text/html')

async def init(loop):
    app=web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv=await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

