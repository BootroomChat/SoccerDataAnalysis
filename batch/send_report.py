import os
import sys
import oss2

# from xt_util import write_json, load_json
# from xt_run import match_pathes, calculate_path, rm_dir
from config.config import default_config

if __name__ == '__main__':
    config = default_config()
    aliyun_access_key = config.get("aliyun", "aliyun_access_key")
    aliyun_secret = config.get("aliyun_secret", "aliyun_access_key")
    auth = oss2.Auth(aliyun_access_key, aliyun_secret)
    # bucket = 'soccer-matches'
    # bucket = oss2.Bucket(auth, 'http://oss-cn-shanghai.aliyuncs.com', bucket)
    bucket = 'soccer-matches-hk'
    bucket = oss2.Bucket(auth, 'http://oss-cn-hongkong.aliyuncs.com', bucket)
    report_lst = list()
    while True:
        for file_path in oss2.ObjectIterator(bucket, prefix='reports/'):
            file = file_path.key
            obj = bucket.get_object_meta(file)
            a = 3
    # uploaded = load_json('oss_matches.json')
    # if len(sys.argv) > 1:
    #     if sys.argv[1] == 'upload':
    #         for path in reversed(sorted(match_pathes())):
    #             if '2023' not in path:
    #                 continue
    #             match_json_file = os.path.join(path, 'match.json')
    #             if not bucket.object_exists(match_json_file):
    #                 print('uploading', match_json_file)
    #                 print('uploaded', bucket.put_object_from_file(match_json_file, match_json_file).status)
    #             else:
    #                 print('skip', match_json_file)
    #             uploaded[match_json_file] = 1
    #     else:
    #         for oss_file in oss2.ObjectIterator(bucket):
    #             match_json_file = oss_file.key
    #             path = match_json_file.replace('match.json', '')
    #             if not os.path.exists(match_json_file):
    #                 if len(sys.argv) > 2 and sys.argv[2] not in match_json_file:
    #                     continue
    #                 print(match_json_file)
    #                 # bucket.delete_object(match_json_file)
    #                 # if match_json_file in uploaded:
    #                 #     del uploaded[match_json_file]
    #                 # continue
    #                 os.makedirs(path, exist_ok=True)
    #                 bucket.get_object_to_file(match_json_file, match_json_file)
    #                 # calculate_path(path)
    #             uploaded[match_json_file] = 1
    #         if sys.argv[1] == 'save':
    #             print('write uploaded')
    #             write_json('oss_matches.json', uploaded)
