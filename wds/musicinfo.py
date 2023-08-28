from datetime import datetime, timezone, timedelta
import time
import pymysql
import ujson as json
from selenium import webdriver
import os
import requests
import Levenshtein as lev
import yaml
from modules.pjskinfo import isSingleEmoji, writelog
from wds.api import get_asset
from wds.config import PROXY
from modules.mysql_config import *

roman_numerals = {
        1: 'I',
        2: 'II',
        3: 'III',
        4: 'IV',
        5: 'V',
        6: 'VI',
        7: 'VII',
        8: 'VIII',
        9: 'IX',
        10: 'X'
    }


def wds_to_unix_timestamp(wds_timestamp):
    return wds_timestamp - 32400


def seconds_to_minutes(seconds):
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}分{sec}秒"


def wds_is_leak(musicid):
    with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
        music_data = json.load(f)
    music_info = next((item for item in music_data if item['id'] == musicid), None)
    if not music_info:
        return False
    released_at_unix = wds_to_unix_timestamp(music_info.get('releasedAt', 0))
    if released_at_unix > time.time():
        return True
    else:
        return False


def wdsinfo(musicid):
    # 读取 music.json 和 live.json
    with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
        music_data = json.load(f)
    with open('wds/masterdata/live.json', 'r', encoding='utf-8') as f:
        live_data = json.load(f)
    with open('wds/translate.yaml', encoding='utf-8') as f:
        trans = yaml.load(f, Loader=yaml.FullLoader)

    # 寻找匹配的音乐信息
    music_info = next((item for item in music_data if item['id'] == musicid), None)
    if not music_info:
        return False, "没有找到你要的歌曲"

    # 获取基础信息
    name = music_info.get('name', '未知')
    if (translation := trans.get(int(musicid), '')) != '':
        name += f'({translation})'
    lyric_writer = music_info.get('lyricWriter', '未知')
    composer = music_info.get('composer', '未知')
    arranger = music_info.get('arranger', '未知')
    # 格式化开放时间
    released_at_unix = wds_to_unix_timestamp(music_info.get('releasedAt', 0))
    if released_at_unix > time.time():
        return False, '没有找到你要的歌曲，可能是还没有实装，再等等？'
    if released_at_unix < 1690344000:
        released_at_unix = 1690344000
    released_at_utc8 = datetime.fromtimestamp(released_at_unix, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S (UTC+8)')
    music_time_second = seconds_to_minutes(music_info.get('musicTimeSecond', 0))
    vocalVersions = music_info.get('vocalVersions', [])
    if len(vocalVersions) == 1:
        vocals = vocalVersions[0]['singer']
    else:
        vocals = "\n" + "\n".join(['◉' + v['singer'] for v in vocalVersions])

    # 寻找所有相关的难度等级
    difficulties = [live for live in live_data if live['musicMasterId'] == musicid]
    difficulty_str = ""
    for diff in ["Normal", "Hard", "Extra", "Stella", "Olivier"]:
        level = next((item['level'] for item in difficulties if item['difficulty'] == diff), None)
        if diff == 'Olivier':
            level = roman_numerals[level - 100]
        difficulty_str += f"{level if level else '-'} / "

    difficulty_str = difficulty_str.rstrip(" / ")

    # 格式化输出
    output_str = f"""作词: {lyric_writer}
作曲: {composer}
编曲: {arranger}
开放时间: {released_at_utc8}
播放长度: {music_time_second}
Vocal: {vocals}
难度: {difficulty_str}
"""
    jacket_path = f'jacket/{musicid}.png'
    get_asset(jacket_path)
    return True, name, os.path.join("data/assets/sekai/assetbundle/resources/wds", jacket_path), output_str


def get_wds_chart(music_id, difficulty):
    png_path = f'charts/wds/{music_id}/{difficulty}.png'
    
    # Step 2: Check if the PNG file already exists
    if os.path.exists(png_path):
        return png_path

    # Create directories if not exist
    os.makedirs(f'charts/wds/{music_id}', exist_ok=True)

    # Step 3: Download SVG if PNG doesn't exist
    svg_url = f'https://redive.estertion.win/wds/Notations/{music_id}/{difficulty}.svg'
    svg_path = f'charts/wds/{music_id}/{difficulty}.svg'

    
    response = requests.get(svg_url, proxies=PROXY)
    if response.status_code != 200:
        return False
    with open(svg_path, 'wb') as f:
        f.write(response.content)
    
    # Step 4: Convert SVG to PNG
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # Initialize the Chrome webdriver and open the SVG file
    driver = webdriver.Chrome('wds/chrome/chromedriver-win64/chromedriver.exe', options=options)
    svg_path_absolute = os.path.abspath(svg_path)
    svg_path_windows = svg_path_absolute.replace("/", "\\")
    driver.get(f'file:///{svg_path_windows}')
    
    # Get the SVG element dimensions
    width = driver.execute_script('return document.documentElement.scrollWidth')
    height = driver.execute_script('return document.documentElement.scrollHeight')
    
    # Set window size
    driver.set_window_size(width, height)
    
    # Take screenshot
    driver.save_screenshot(png_path)
    
    driver.quit()
    
    # Step 5: Return PNG path
    return png_path


def string_similar(s1, s2):
    # 使用Levenshtein库计算两个字符串之间的距离
    distance = lev.distance(s1, s2)
    # 计算最大可能的距离
    max_len = max(len(s1), len(s2))
    # 计算相似度，并返回。距离越小，相似度越高，所以我们用1减去它们的比值
    return 1 - (distance / max_len)


def wds_alias_to_music_id(alias):
    alias = alias.strip()
    if alias == '':
        return {'musicid': 0, 'match': 0, 'name': '', 'translate': ''}
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * from wdsalias where alias=%s', (alias,))
    raw = mycursor.fetchone()
    mycursor.close()
    mydb.close()
    if raw is not None:
        with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        name = ''
        for musics in data:
            if musics['id'] != raw[2]:
                continue
            name = musics['name']
            break

        with open('wds/translate.yaml', encoding='utf-8') as f:
            trans = yaml.load(f, Loader=yaml.FullLoader)
        try:
            translate = trans[raw[2]]
            if translate == name:
                translate = ''
        except KeyError:
            translate = ''
        return {'musicid': raw[2], 'match': 1, 'name': name, 'translate': translate}
    return wds_match_name(alias)



def wds_match_name(alias):
    match = {'musicid': 0, "match": 0, 'name': ''}
    with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open('wds/translate.yaml', encoding='utf-8') as f:
        trans = yaml.load(f, Loader=yaml.FullLoader)

    for musics in data:
        name = musics['name']
        similar = string_similar(alias.lower(), name.lower())
        if similar > match['match']:
            match['match'] = similar
            match['musicid'] = musics['id']
            match['name'] = musics['name']
        try:
            translate = trans[musics['id']]
            if '/' in translate:
                alltrans = translate.split('/')
                for i in alltrans:
                    similar = string_similar(alias.lower(), i.lower())
                    if similar > match['match']:
                        match['match'] = similar
                        match['musicid'] = musics['id']
                        match['name'] = musics['name']
            else:
                similar = string_similar(alias.lower(), translate.lower())
                if similar > match['match']:
                    match['match'] = similar
                    match['musicid'] = musics['id']
                    match['name'] = musics['name']
        except KeyError:
            pass
    try:
        match['translate'] = trans[match['musicid']]
        if match['translate'] == match['name']:
            match['translate'] = ''
    except KeyError:
        match['translate'] = ''
    return match


def wdsset(newalias, oldalias, qqnum, username, qun):
    newalias = newalias.strip()
    if isSingleEmoji(newalias):
        return "由于数据库排序规则原因，不支持单个emoji字符作为歌曲昵称"
    resp = wds_alias_to_music_id(oldalias)
    if resp['musicid'] == 0:
        return "找不到你要设置的歌曲，请使用正确格式：pjskinfo新昵称to旧昵称"
    musicid = resp['musicid']

    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    sql = f"insert into wdsalias(ALIAS,MUSICID) values (%s, %s) " \
          f"on duplicate key update musicid=%s"
    val = (newalias, musicid, musicid)
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    mydb.close()

    with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    title = ''
    for music in data:
        if music['id'] != musicid:
            continue
        title = music['name']
    timeArray = time.localtime(time.time())
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    writelog(f'[WDS][{Time}] {qun} {username}({qqnum}): {newalias}->{title}')
    return f"设置成功！{newalias}->{title}\n已记录bot文档中公开的实时日志，设置不合适的昵称将会被拉黑"


def wdsdel(alias, qqnum, username, qun):
    alias = alias.strip()
    resp = wds_alias_to_music_id(alias)
    if resp['match'] != 1:
        return "找不到你要设置的歌曲，请使用正确格式：pjskdel昵称"
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute("DELETE from wdsalias where alias=%s", (alias,))
    mydb.commit()
    mycursor.close()
    mydb.close()
    timeArray = time.localtime(time.time())
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    if str(qqnum) == '1103479519':
        writelog(f'[WDS][{Time}] 管理员删除了{resp["name"]}的昵称：{alias}')
        return "删除成功！"
    writelog(f'[{Time}] {qun} {username}({qqnum}): 删除了{resp["name"]}的昵称：{alias}')
    return "删除成功！\n已记录bot文档中公开的实时日志，乱删将被拉黑"


def wdsalias(alias, musicid=None):
    from imageutils import text2image
    if musicid is None:
        resp = wds_alias_to_music_id(alias)
        if resp['musicid'] == 0:
            return "找不到你说的歌曲哦"
        musicid = resp['musicid']
        if resp['translate'] == '':
            returnstr = f"{resp['name']}\n匹配度:{round(resp['match'], 4)}\n"
        else:
            returnstr = f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}\n"
    else:
        returnstr = ''
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * from wdsalias where musicid=%s', (musicid,))
    respdata = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    for raw in respdata:
        returnstr = returnstr + raw[1] + "，"
    if len(returnstr[:-1]) > 170:
        infopic = text2image(text=returnstr[:-1] + '\n昵称均为用户添加，与bot和bot主无关\n\n', max_width=800, padding=(30, 30))
        infopic.save(f'piccache/{musicid}alias.png')
        return f"[CQ:image,file=file:///{os.getcwd()}/piccache/{musicid}alias.png,cache=0]"
    else:
        return returnstr[:-1] + '\n昵称均为用户添加，与bot和bot主无关'
    

def wds_alias_to_chart(full, qun=False):
    if full[-2:] == 'ex':
        alias = full[:-2]
        diff = 3
    elif full[-2:] == 'hd':
        alias = full[:-2]
        diff = 2
    elif full[-2:] == 'nm':
        alias = full[:-2]
        diff = 1
    elif full[-2:] == 'st':
        alias = full[:-2]
        diff = 4
    elif full[-2:] == "ol":
        alias = full[:-2]
        diff = 5
    elif full[-6:] == 'extra':
        alias = full[:-6]
        diff = 3
    elif full[-4:] == 'hard':
        alias = full[:-4]
        diff = 2
    elif full[-6:] == 'normal':
        alias = full[:-6]
        diff = 1
    elif full[-6:] == 'stella':
        alias = full[:-4]
        diff = 4
    elif full[-7:] == 'olivier':
        alias = full[:-6]
        diff = 5
    else:
        alias = full
        diff = 4
    resp = wds_alias_to_music_id(alias)
    if resp['musicid'] == 0 or wds_is_leak(resp['musicid']):
        return None  # 找不到歌曲 return None
    else:
        diff_name = {
                1: 'NORMAL',
                2: 'HARD',
                3: 'EXTRA',
                4: 'STELLA',
                5: 'OLIVIER'
            }
        text = f'{resp["name"]} {diff_name[diff]}\n匹配度: {round(resp["match"], 4)}\n谱面来自estertion.win'
        dir = get_wds_chart(resp['musicid'], diff)
        if dir:
            return text, dir
        else:
            return False