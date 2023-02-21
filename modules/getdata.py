import ujson as json
import traceback
from ujson import JSONDecodeError

import requests
import yaml
from requests import ReadTimeout

from modules.config import apiurls, enapiurls, twapiurls, krapiurls, proxies


class maintenanceIn(Exception):
   pass

class userIdBan(Exception):
   pass

class apiCallError(Exception):
    pass

class serverNotSupported(Exception):
    pass

def callapi(url, server='jp'):
    global twapiurls
    global krapiurls

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
            if 'profile' in url:
                """
                删除指定用户对应歌曲fc/ap到clear
                格式示例：
                '1234567890':
                - 135
                """
                try:
                    with open('yamls/apiremove.yaml', 'r', encoding='utf-8') as f:
                        profileMusicDel = yaml.load(f, Loader=yaml.FullLoader)
                    for deluserid in profileMusicDel:
                        if url == f'/user/{deluserid}/profile':
                            print(f"删除{deluserid}fc/ap")
                            for i in range(0, len(data['userMusicResults'])):
                                if data['userMusicResults'][i]["musicId"] in profileMusicDel[deluserid] and \
                                        data['userMusicResults'][i]["musicDifficulty"] == "master":
                                    print(f'删除{data["userMusicResults"][i]["musicId"]}')
                                    data['userMusicResults'][i]["fullComboFlg"] = False
                                    data['userMusicResults'][i]["fullPerfectFlg"] = False
                                    data['userMusicResults'][i]["playResult"] = "clear"
                except:
                    pass

            if server in ['tw', 'kr'] and len(urlroots) > 1 and urlroot == urlroots[1]:
                # 台服api不明原因容易卡死 卡死后切换到备用服务器
                twapiurls[0], twapiurls[1] = twapiurls[1], twapiurls[0]
                krapiurls[0], krapiurls[1] = krapiurls[1], krapiurls[0]
                print('交换外服主从服务器次序，新地址:', twapiurls[0])
            return data
        except (requests.exceptions.ConnectionError, JSONDecodeError, ReadTimeout):
            print(urlroot, '请求失败')
            pass

    raise apiCallError
