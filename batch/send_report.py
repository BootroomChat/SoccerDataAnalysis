import argparse
import os
import time
import oss2
from config.config import default_config
from utils.data import load_client_info, save_client_info
from utils.messaging import AttachmentEmailSender


def send_report(bucket, remote_path, local_path=None):
    local_path = remote_path if local_path is None else local_path
    local_path = local_path.replace('reports', 'statistics')
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bucket.get_object_to_file(remote_path, root_path + '/' + local_path + '.pdf')


def send_report_bucket(bucket: oss2.Bucket, path_list: list, email=None):
    """
    :param bucket:
    :param path_list:
    :param client_id:
    :return:
    """
    local_path_list = list()
    for each_path in path_list:
        local_path = each_path.replace('reports', '')
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_path = root_path + local_path + '.pdf'
        if not os.path.exists(local_path):
            bucket.get_object_to_file(each_path, local_path)
        local_path_list.append(local_path)

    client_info = load_client_info()
    send_dict = dict()
    if email is None:
        for index, info in client_info.iterrows():
            if (info['Trial'] and info['ReportSent'] < 5) or info['Membership']:
                send_dict[info['Email']] = list()
                for each_path in local_path_list:
                    if info['Level'] == 'Team':
                        if info['Team'] == 'ALL':
                            send_dict[info['Email']].append(each_path)
                        else:
                            for each_team in info['Team'].split(','):
                                if each_team in each_path:
                                    send_dict[info['Email']].append(each_path)
                    elif info['Level'] == 'League':
                        if info['League'] == 'ALL':
                            send_dict[info['Email']].append(each_path)
                        else:
                            for each_league in info['League'].split(','):
                                if each_league in each_path:
                                    send_dict[info['Email']].append(each_path)
                    elif info['Level'] == 'Season':
                        if info['Season'] == 'ALL':
                            send_dict[info['Email']].append(each_path)
                        else:
                            for each_season in info['Season'].split(','):
                                if each_season in each_path:
                                    send_dict[info['Email']].append(each_path)
                    else:
                        lv = info['Level']
                        raise NotImplementedError(f'Level{lv} is not supported yet!')
                client_info.loc[index, 'ReportSent'] = info['ReportSent'] + len(send_dict[info['Email']])
        save_client_info(client_info)
    else:
        send_dict = {email: local_path_list}
    emailSenderClient = AttachmentEmailSender()
    for k, v in send_dict.items():
        if len(v) != 0:
            content = "Dear Reader, \n\n    Please find the reports as attached. \n    Thank you.\n\nBest,\nXTScore Team\nEmail: bootroomchat_editor@outlook.com\n"
            sig = '======================================\n'
            sig = sig + 'The match report belongs to the owner of this email sender, all information contained in this message may be privileged and confidential. It is intended to be read only by the individual or entity to whom it is addressed or by their designee. If the reader of this message is not the intended recipient, you are on notice that any distribution of this message, in any form, is strictly prohibited. If you have received this message in error, please immediately notify the sender and delete or destroy any copy of this message.'
            content = content + sig
            subject = 'XT Match report'
            emailSenderClient.send_email([k], subject, content, v)

    for each_path in local_path_list:
        os.remove(each_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-email', default=None)
    parser.add_argument('-method', default='batch')
    parser.add_argument('-source', default='oss')
    parser.add_argument('-report_path', default=None)
    args = parser.parse_args()
    config = default_config()
    info = load_client_info()
    aliyun_access_key = config.get("aliyun", "aliyun_access_key")
    aliyun_secret = config.get("aliyun", "aliyun_secret")
    auth = oss2.Auth(aliyun_access_key, aliyun_secret)
    # bucket = 'soccer-matches'
    # bucket = oss2.Bucket(auth, 'http://oss-cn-shanghai.aliyuncs.com', bucket)
    bucket = 'soccer-matches-hk'
    bucket = oss2.Bucket(auth, 'http://oss-cn-hongkong.aliyuncs.com', bucket)
    if args.method == 'batch':
        report_lst = list()
        while True:
            this_report_lst = list()
            for file_path in oss2.ObjectIterator(bucket, prefix='reports/'):
                this_report_lst.append(file_path.key)
            if len(report_lst) == 0:
                report_lst = this_report_lst
            else:
                if len(this_report_lst) > len(report_lst):
                    new_report_set = list(set(this_report_lst).difference(set(report_lst)))
                    send_report_bucket(bucket, new_report_set)
                    report_lst = this_report_lst
                else:
                    time.sleep(300)
    elif args.method == 'single':
        if args.report_path is not None:
            path = args.report_path.split(',')
            path =[each_path.replace("+",' ') for each_path in path]
            send_report_bucket(bucket=bucket, path_list=path, email=args.email)
