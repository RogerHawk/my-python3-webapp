#URL处理

import re,time,json,logging,hashlib,base64,asyncio

from coroweb import get,post

from model import User,Comment,Blog,next_id

#使用orm中提供的装饰器get。在aiohttp收到对根/的访问的GET访问请求是，controller调用本index，并返回一个dict
@get('/')
async def index(request):
    #异步方式提取User表里所有的数据，以list方式返回users
    users = await User.findAll()
    #返回dict类型。交由拦截器response_factory处理
    return {
        '__template__':'test.html',
        'users':users
    }
