#使用异步aiohttp编写MVC的Controller
#使用jinja2作为Model的模板引擎
#使用已经自行封装好的orm进行数据库操作
#对照：app_mvc简单应用中,Controller使用的是flask框架里的Flask，Model使用的也是flask框架里的render_temple
import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment,FileSystemLoader

import orm
from coroweb import add_routes,add_static

#初始化jinja2的各类参数。jinja2本身实际默认了很多参数，LXF设计这个init，应该是想改变一些参数。具体的差别需要实践来检验
def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    #1.options负责存储jinja2核心组件Environment的共享变量
    options = dict(
        autoescape = kw.get('autoescape',True),                             #XML/HTML自动转义，默认本来是false。就是在渲染模板时自动把变量中<>&等字符转换为&lt;&gt;&amp;
        block_start_string = kw.get('block_start_string','{%'),             #块开始标记符，缺省是'{%'
        block_end_string = kw.get('block_end_string','{%'),                 #块结束标记符，缺省是'%}'
        variable_start_string = kw.get('variable_start_string','{{'),       #变量开始标记符，缺省是'{{'。这个很用用，在View的**.html中用此传参数，如{{ username }}
        variable_end_string = kw.get('variable_end_string','}}'),           #变量结束标记符，缺省是'{{'。这个很用用，在View的**.html中用此传参数，如{{ username }}
        auto_reload = kw.get('auto_reload', True)                           #如果设为True，jinja会在使用Template时检查模板文件的状态，如果模板有修改， 则重新加载模板。如果对性能要求较高，可以将此值设为False
    )
    #2.设置模板所在路径。这里强制忽略kw的传入，强制设置为None，然后再赋值？
    #默认是访问的url **/path，然后就在template下设置一个path的模板
    path = kw.get('path',None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path: %s' %path)
    #3.加载模板，并过滤元组?
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name] = f
    #明确web应用的模板来自env
    app['__templating__'] = env

#这个异步函数的处理有点疑问
async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request:%s %s' %(request.method, request.path))
        return(await handler(request))
    return logger

async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startwith('applicaiton/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' %str(request.__data__))
            elif request.content_type.startwith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request json: %s' %str(request.__data__))
        return (await handler(request))
    return parse_data

#关键的一个异步处理函数：web.Response内容的处理
async def response_factory(app, handler):
    async def response(request):
        logging.info('response handler')
        #获取request，赋值给r
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type='application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startwith('redirect:'):
                return web.HTTPFound(r[9:])     #r[9:]取r第9位之后的部分
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type='text/html;charset=utf-8'
            return resp

        #重要的一步，处理各类报文提交请求，如登录等
        #如果request的数据是dict对象。参考coroweb.py，上传的content-type可能是application/json，也可以能是application/x-www-form-urlencoded
        if isinstance(r, dict):
            #模板采用设定的模板. init_jinja中已定义
            template = r.get('__template__')
            if template is None:
                #如果模板未定义，则返回指定的响应值
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                #如果模板存在，则返回指定的模板
                #这里还是有一个疑问的，这里只是提取了View，但是Model的值从哪里传过去的呢？
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html'
                return resp

        #这里为什么要判断>=100和<600呢
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        #如果request是一个tuple格式且元组等于2。为什么这么判断呢？
        if isinstance(r,tuple) and len(r) == 2:
            t,m=r
            if isinstance(t,int) and t >= 100 and t < 600:
                return web.Response(t,str(m))
        
        #default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain'                    #返回数据以纯文本形式进行编码，其中不包含任何控件或格式字符
        return resp
    return response

#一个日期时间的过滤器
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

#aiohttp的主控
async def init(loop):
    #这里直接代码指定，有点弱吧。应用只能和数据库部署在同一台服务器上了
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='www', password='www', db='awesome')
    #使用2个拦截器来处理web服务请求，一个日志工厂，一个响应处理工厂
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    #初始化jinja2模板。这里非关键参数实际上只传送了一个过滤器，即其他参数都使用init_jinja2的默认值。如果想改变，这里可以传参数进去
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    #加载各应用路由
    add_routes(app, 'handlers')
    #加载静态文件
    add_static(app)
    #启动服务
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv 

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

            





