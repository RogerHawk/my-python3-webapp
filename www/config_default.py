#默认的配置。这里使用py源码的形式配置，其实有点疑问，正常使用文本文件不是更好吗？
#从强化dict的角度考虑，熟悉本章节

#定义一个dict，作为默认配置
configs = {
    #首先是数据库配置
    'db':{
        'host':'127.0.0.1',
        'port':3306,
        'user':'wwwdata',
        'password':'wwwdata',
        'database':'awesome'
    },

    #其次是session配置
    'session':{
        'secret':'AwEsOmE'
    }
}
