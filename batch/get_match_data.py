import oss2
import os
import sys
from config.config import default_config

if __name__ == '__main__':
    config = default_config()
    aliyun_access_key = config.get("aliyun", "aliyun_access_key")
    aliyun_secret = config.get("aliyun", "aliyun_secret")
    auth = oss2.Auth(aliyun_access_key, aliyun_secret)
    # bucket = 'soccer-matches'
    # bucket = oss2.Bucket(auth, 'http://oss-cn-shanghai.aliyuncs.com', bucket)
    bucket = 'soccer-matches-hk'
    bucket = oss2.Bucket(auth, 'http://oss-cn-hongkong.aliyuncs.com', bucket)
    for oss_file in oss2.ObjectIterator(bucket):
        match_json_file = oss_file.key
        path = match_json_file.replace('match.json', '')
        if not os.path.exists(match_json_file):
            if len(sys.argv) > 2 and sys.argv[2] not in match_json_file:
                continue
            print(match_json_file)
            os.makedirs(path, exist_ok=True)
            bucket.get_object_to_file(match_json_file, match_json_file)