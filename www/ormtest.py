import asyncio
import orm
from model import User,Blog,Comment

#这里需要用异步方式定义test方法，然后内部才可以使用await
async def test(loop):
    await orm.create_pool(loop=loop,user='wwwdata', password='wwwdata', db='awesome')

    u=User(name='Test',email='test@example.com',passwd='1234567890',image='about:blank')

    await u.save()
    await orm.destory_pool()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()