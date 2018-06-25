#针对开发环境使用的config_default.py，以及生产环境使用的config_override.py，编写合并代码

import config_default

#定义这个dict的子类Dict的目的是？
#2018.06.25 LXF自己的解释是：Simple dict don't support access d.key style。即固有类dict不支持实例名.key的提取方法。这个Dict就是为了扩展这个方法而已
class Dict(dict):
    #names是一个tuple，values也是一个tuple
    #把dict的内容初始化出来，key来自names，值来自values
    #问题试config_default.py里已经将configs定义为一个默认好的dict了，且赋值了，这里再初始化的意义？ 确实意义不大
    def __init__(self, names=(), values=(), **kw):
        #这里还是python2的写法，python3可以简单写成super().__init__(**kw)
        #父类初始化，就是默认类型dict的初始化。意义需跟踪下
        super(Dict,self).__init__(**kw)
        #zip(names,values)的结果是:[(k1,v1),(k2,v2),(k3,v3)]
        for k,v in zip(names,values):
            self[k]=v

    #根据key，取key对应的值。方法返回该值
    def __getattr__(self,key):
        try:
            #直接返回dict字典key对应的值
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" %key)

    #设置key对应的值
    def __setattr__(self,key,value):
        self[key]=value

#合并配置函数。参数是两个dict
def merge(defaults,override):
    #定义一个dict类型r，作为合并后的结果返回
    r={}
    for k,v in defaults.items():
        if k in override:
            #判断v是否是dict类型，使用isinstance(object,classinfo)判断object实例对象是否是已知类型classinfo
            if isinstance(v, dict):
                #这里用一个迭代的方法很赞。因为参数本身可能是个多重的dict，如defualts的key ‘db'的值就是一个dict。
                r[k]=merge(v,override[k])
            else:
                #最终迭代到赋值,用override[k]的值覆盖default中的同key的值
                r[k]=override[k]
        else:
            #如果key不在override中，使用原defaults中的值
            r[k]=v
    return r

#扩展一个方法。正常dict类的实例d1，取值方法是d[key];这里用一个Dict扩展后，Dict的实例d2,取值方式可以是d2.key
#这个方法实际对dict的理解实际不是很有用，暂时先留着。
def toDict(d):
    D=Dict()
    for k,v in d.items():
        #这里也是一个迭代。当然写法有点意思，if else的一行表达方式：为真的值在前，if判断在中，为假值在后。这么写略有点B格。普通等价如下：
        #if isinstance(v,dict):
        #   D[k]=toDict(v)
        #else
        #   D[k]=v
        D[k]=toDict(v) if isinstance(v,dict) else v
    return D

configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

#正常是configs[key]，这里就是为了能写成config.key
configs = toDict(configs)