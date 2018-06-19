#同样用异步的方式访问数据库，这里采用mysql，因为有协程异步包aiomysql可以直接调用
import asyncio, logging; logging.basicConfig(level=logging.INFO)
import aiomysql

#定义日志方法，这里不需要异步，同步方法
def log(sql, args=()):
    logging.info('SQL:%s' %sql)

#协程态方法封装：创建数据库连接池
async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host','localhost'),
        port=kw.get('port',3306),
        password=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','gb2312'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )

#协程态方法封装：DML语句之select 
async def select(sql, args, size==None):
    log(sql, args)
    global __pool
    with ( await __pool ) as conn:
        #这里还是用游标来操作啊
        cur = await conn.cursor(aiomysql.DictCursor)
        #SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
        #注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击
        await cur.execute(sql.replace('?','%s'), args or ())
        #fetch游标 这个概念古老但是常效哦 
        #如果传入size参数，就通过fetchmany()获取最多指定数量的记录，否则，通过fetchall()获取所有记录。
        if size:            #如果不是None
            rs=await cur.fetchmany(size)
        else:
            rs=await cur.fetchall()
        await cur.close()
        logging.info('rows returned by select:%s' %len(rs))

#协程态方法封装: DML语句之update，insert，delete
async def execute(sql, args):
    log(sql)
    with (await __pool) as conn:
        try: 
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args)
            #execute()函数和select()函数所不同的是，cursor对象不返回结果集，而是通过rowcount返回结果数。
            rowaffected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return rowaffected





