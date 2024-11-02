import os
import time
import ujson as json
import traceback
from ujson import JSONDecodeError
from datetime import datetime
import pytz
import requests
from requests import ReadTimeout

from modules.config import apiurls, enapiurls, twapiurls, krapiurls, proxies, \
                            rank_query_ban_servers


class maintenanceIn(Exception):
   pass

class userIdBan(Exception):
   pass

class apiCallError(Exception):
    pass

class serverNotSupported(Exception):
    pass

class LeakContent(Exception):
    pass

class MasterStructureChange(Exception):
    def __init__(self, message="Master data structure update, operation failed."):
        self.message = message
        super().__init__(self.message)


class QueryBanned(Exception):
    def __init__(self, server="jp"):
        self.server = server


current_api_index = {'tw': 0}


def callapi(url, server='jp', query_type='unknown', is_force_update=False, chara_id=None):
    global twapiurls
    global krapiurls
    global current_api_index

    if server == 'jp':
        urlroots = apiurls
    elif server == 'en':
        urlroots = enapiurls
    elif server == 'tw':
        urlroots = twapiurls
    elif server == 'kr':
        urlroots = krapiurls
    else:
        raise serverNotSupported
    
    # 由于该函数经历过日服先修改API，其他服慢慢跟上的过程，每个API修改的时间点都为了不改动逻辑做出了很多适应性修改
    # 现在所有服务器已经完成API修改，不再需要适应性，但是代码未直接按照新API重写，会比较晦涩难懂，请勿参考。
    # 以下都是为了不改动逻辑代码而在数据获取时做出的适应性改动。
    if server in rank_query_ban_servers:
        if server == 'jp':
            if '/ranking?targetRank' in url:
                targetRank = int(url[url.find('targetRank=') + len('targetRank='):])
                
                if targetRank <= 100:
                    with open('data/jptop100.json', 'r', encoding='utf-8') as f:
                        jptop100 = json.load(f)
                    updatetime = time.localtime(os.path.getmtime('data/jptop100.json'))
                    if chara_id is not None:
                        for chapter in jptop100['userWorldBloomChapterRankings']:
                            if chapter['gameCharacterId'] == chara_id:
                                jptop100 = chapter
                    for single in jptop100["rankings"]:
                        if single["rank"] == targetRank:
                            return {
                                "rankings": [single],
                                'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                            }
                    else:
                        return {
                                "rankings": []
                            }
                else:
                    with open('data/jpborder.json', 'r', encoding='utf-8') as f:
                        jpborder = json.load(f)
                    updatetime = time.localtime(os.path.getmtime('data/jpborder.json'))
                    if chara_id is not None:
                        for chapter in jpborder['userWorldBloomChapterRankingBorders']:
                            if chapter['gameCharacterId'] == chara_id:
                                jpborder = chapter
                    for single in jpborder["borderRankings"]:
                        if single["rank"] == targetRank:
                            return {
                                "rankings": [single],
                                'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                            }
                    else:
                        return {
                                "rankings": []
                            }
                    
            if '/ranking?targetUserId=' in url:
                targetUserId = int(url[url.find('targetUserId=') + len('targetUserId='):])
                with open('data/jptop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/jptop100.json'))
                if chara_id is not None:
                    for chapter in jptop100['userWorldBloomChapterRankings']:
                        if chapter['gameCharacterId'] == chara_id:
                            jptop100 = chapter
                for single in jptop100["rankings"]:
                    if single["userId"] == targetUserId:
                        return {
                            "rankings": [single],
                            'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                        }
                else:
                    return {
                            "rankings": []
                        }
            # if '/profile' in url and query_type != 'daibu' and not is_force_update:
            #     userid = url[url.find('user/') + 5:url.find('/profile')]
            #     if os.path.exists(f'{suite_uploader_path}{userid}.json'):
            #         with open(f'{suite_uploader_path}{userid}.json', 'r', encoding='utf-8') as f:
            #             data = json.load(f)
            #         return data
            #     elif query_type in ['b30', 'jindu', 'rank']:
            #         raise QueryBanned(server)
        elif server == 'tw':
            if '/ranking?targetRank' in url:
                targetRank = int(url[url.find('targetRank=') + len('targetRank='):])
                with open('data/twtop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/twtop100.json'))
                for single in jptop100["rankings"]:
                    if single["rank"] == targetRank:
                        return {
                            "rankings": [single],
                            'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/ranking?targetUserId=' in url:
                targetUserId = int(url[url.find('targetUserId=') + len('targetUserId='):])
                with open('data/twtop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/twtop100.json'))
                for single in jptop100["rankings"]:
                    if single["userId"] == targetUserId:
                        return {
                            "rankings": [single],
                            'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/profile' in url and query_type != 'daibu' and not is_force_update:
                if query_type in ['b30', 'jindu', 'rank']:
                    raise QueryBanned(server)
        elif server == 'kr':
            if '/ranking?targetRank' in url:
                targetRank = int(url[url.find('targetRank=') + len('targetRank='):])
                with open('data/krtop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/krtop100.json'))
                for single in jptop100["rankings"]:
                    if single["rank"] == targetRank:
                        return {
                            "rankings": [single],
                            'updateTime': datetime.fromtimestamp(time.mktime(updatetime), pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Tokyo')).strftime('%m-%d %H:%M:%S')
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/ranking?targetUserId=' in url:
                targetUserId = int(url[url.find('targetUserId=') + len('targetUserId='):])
                with open('data/krtop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/krtop100.json'))
                for single in jptop100["rankings"]:
                    if single["userId"] == targetUserId:
                        return {
                            "rankings": [single],
                            'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/profile' in url and query_type != 'daibu' and not is_force_update:
                if query_type in ['b30', 'jindu', 'rank']:
                    raise QueryBanned(server)
        elif server == 'en':
            if '/ranking?targetRank' in url:
                targetRank = int(url[url.find('targetRank=') + len('targetRank='):])
                with open('data/entop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/entop100.json'))
                for single in jptop100["rankings"]:
                    if single["rank"] == targetRank:
                        return {
                            "rankings": [single],
                            'updateTime': datetime.fromtimestamp(time.mktime(updatetime), pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Tokyo')).strftime('%m-%d %H:%M:%S')
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/ranking?targetUserId=' in url:
                targetUserId = int(url[url.find('targetUserId=') + len('targetUserId='):])
                with open('data/entop100.json', 'r', encoding='utf-8') as f:
                    jptop100 = json.load(f)
                updatetime = time.localtime(os.path.getmtime('data/entop100.json'))
                for single in jptop100["rankings"]:
                    if single["userId"] == targetUserId:
                        return {
                            "rankings": [single],
                            'updateTime': time.strftime("%m-%d %H:%M:%S", updatetime)
                        }
                else:
                    return {
                            "rankings": []
                        }
            if '/profile' in url and query_type != 'daibu' and not is_force_update:
                if query_type in ['b30', 'jindu', 'rank']:
                    raise QueryBanned(server)
    if server == 'tw':
        urlroots = twapiurls
        urlroot = urlroots[current_api_index['tw']]
        try:
            if 'https' in urlroot:
                resp = requests.get(urlroot + url, timeout=10, proxies=proxies)
            else:
                resp = requests.get(urlroot + url, timeout=10)
            data = json.loads(resp.content)
            if data == {'status': 'maintenance_in'}:
                raise maintenanceIn
            elif data == {'status': 'user_id_ban'}:
                raise userIdBan
            
            current_api_index['tw'] = (current_api_index['tw'] + 1) % len(urlroots)
            return data
        except (requests.exceptions.ConnectionError, JSONDecodeError, ReadTimeout):
            print(urlroot, '请求失败')
            current_api_index['tw'] = (current_api_index['tw'] + 1) % len(urlroots)
            pass

    for urlroot in urlroots:
        try:
            if 'https' in urlroot:
                resp = requests.get(urlroot + url, timeout=10, proxies=proxies)
            else:
                resp = requests.get(urlroot + url, timeout=10)
            data = json.loads(resp.content)
            if data == {'status': 'maintenance_in'}:
                raise maintenanceIn
            elif data == {'status': 'user_id_ban'}:
                raise userIdBan
            return data
        except (requests.exceptions.ConnectionError, JSONDecodeError, ReadTimeout):
            print(urlroot, '请求失败')
            pass

    raise apiCallError
