import configparser
import functools
import os


@functools.lru_cache()
def default_config():
    conf = configparser.ConfigParser()
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf.read(root_path+'/config/brchat.conf')
    return conf


if __name__ == '__main__':
    conf = configparser.ConfigParser()
    conf.read('./brchat.conf')
    conf.add_section(section='aliyun')
    conf.set("aliyun", "aliyun_access_key", "LTAI5tFq4yY1PkaM1xvHw8Ve")
    conf.set("aliyun", "aliyun_secret", "NkCZDBFKpuqc8tNchEtEAME9aPW3Kb")
    conf.write(open('./brchat.conf', 'w'))
