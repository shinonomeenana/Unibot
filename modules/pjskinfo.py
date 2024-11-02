import datetime
import math
import random
import re
# import emoji
import ujson as json
import os
import sqlite3
import difflib
import time
import pymysql

from modules.getdata import LeakContent
# from modules.mysql_config import *
import requests
from mutagen.mp3 import MP3
import pytz
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import yaml
from emoji2pic.main import Emoji2Pic
import Levenshtein as lev
from modules.config import loghtml, env
# from modules.r2upload import uploadLogR2
from zhconv import convert

from modules.sk import recordname

class musicinfo(object):

    def __init__(self):
        self.id = 0
        self.title = ''
        self.lyricist = ''
        self.composer = ''
        self.arranger = ''
        self.publishedAt = 0
        self.hot = 0
        self.hotAdjust = 0
        self.length = 0
        self.playLevel = [0, 0, 0, 0, 0, 0]
        self.noteCount = [0, 0, 0, 0, 0, 0]
        self.fillerSec = 0
        self.categories = []
        self.assetbundleName = ''


def isSingleEmoji(content):
    if len(content) != 1:
        return False
    if not content:
        return False
    # if emoji.is_emoji(content):
    #     return True
    return False


# def string_similar(s1, s2):
#     return difflib.SequenceMatcher(None, s1, s2).quick_ratio()
def string_similar(s1, s2):
    s1 = s1.replace(" ", "")
    s2 = s2.replace(" ", "")
    # 使用Levenshtein库计算两个字符串之间的距离
    distance = lev.distance(s1, s2)
    # 计算最大可能的距离
    max_len = max(len(s1), len(s2))
    # 计算相似度，并返回。距离越小，相似度越高，所以我们用1减去它们的比值
    return 1 - (distance / max_len)


def get_match_rate_sqrt(query, title):
    # 将查询和标题转换为小写
    query = query.lower().replace(" ", "")
    title = title.lower().replace(" ", "")

    # 检查query是否是title的子串
    if query in title:
        match_ratio = len(query) / len(title)
        if len(query) == 1 or len(title) < 4:
            return match_ratio
        else:
            adjusted_match_rate = math.pow(match_ratio, 1/3)
        return adjusted_match_rate
    else:
        return 0.0


# from https://gitlab.com/pjsekai/musics/-/blob/main/music_bpm.py
def parse_bpm(music_id):
    try:
        with open('data/assets/sekai/assetbundle/resources'
                  '/startapp/music/music_score/%04d_01/expert' % music_id, encoding='utf-8') as f:
            r = f.read()
    except FileNotFoundError:
        try:
            with open('data/assets/sekai/assetbundle/resources'
                      '/startapp/music/music_score/%04d_01/append' % music_id, encoding='utf-8') as f:
                r = f.read()
        except FileNotFoundError:
            return 0, [{'time': 0.0, 'bpm': '无数据'}], 0, None

    score = {}
    bar_count = 0
    for line in r.split('\n'):
        match: re.Match = re.match(r'#(...)(...?)\s*\:\s*(\S*)', line)
        if match:
            bar, key, value = match.groups()
            score[(bar, key)] = value
            if bar.isdigit():
                bar_count = max(bar_count, int(bar) + 1)

    bpm_palette = {}
    for bar, key in score:
        if bar == 'BPM':
            bpm_palette[key] = float(score[(bar, key)])

    bpm_events = {}
    for bar, key in score:
        if bar.isdigit() and key == '08':
            value = score[(bar, key)]
            length = len(value) // 2

            for i in range(length):
                bpm_key = value[i*2:(i+1)*2]
                if bpm_key == '00':
                    continue
                bpm = bpm_palette[bpm_key]
                t = int(bar) + i / length
                bpm_events[t] = bpm

    bpm_events = [{
        'bar': bar,
        'bpm': bpm,
    } for bar, bpm in sorted(bpm_events.items())]

    for i in range(len(bpm_events)):
        if i > 0 and bpm_events[i]['bpm'] == bpm_events[i-1]['bpm']:
            bpm_events[i]['deleted'] = True

    bpm_events = [bpm_event for bpm_event in bpm_events if bpm_event.get('deleted') != True]

    bpms = {}
    for i in range(len(bpm_events)):
        bpm = bpm_events[i]['bpm']
        if bpm not in bpms:
            bpms[bpm] = 0.0

        if i+1 < len(bpm_events):
            bpm_events[i]['duration'] = (bpm_events[i+1]['bar'] - bpm_events[i]['bar']) / bpm * 4 * 60
        else:
            bpm_events[i]['duration'] = (bar_count - bpm_events[i]['bar']) / bpm * 4 * 60

        bpms[bpm] += bpm_events[i]['duration']

    sorted_bpms = sorted([(bpms[bpm], bpm) for bpm in bpms], reverse=True)
    bpm_main = sorted_bpms[0][1]
    duration = sum([bpm[0] for bpm in sorted_bpms])

    return bpm_main, bpm_events, bar_count, duration


def aliastomusicid(alias):
    # alias = alias.strip()
    # if alias == '':
    #     return {'musicid': 0, 'match': 0, 'name': '', 'translate': ''}
    # mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
    #                        database='pjsk', charset='utf8mb4')
    # mycursor = mydb.cursor()
    # mycursor.execute('SELECT * from pjskalias where alias=%s', (alias,))
    # raw = mycursor.fetchone()
    # mycursor.close()
    # mydb.close()
    # if raw is not None:
    #     with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
    #         data = json.load(f)
    #     name = ''
    #     for musics in data:
    #         if musics['id'] != raw[2]:
    #             continue
    #         name = musics['title']
    #         break
    #     with open('yamls/translate.yaml', encoding='utf-8') as f:
    #         trans = yaml.load(f, Loader=yaml.FullLoader)['musics']
    #     try:
    #         translate = trans[raw[2]]
    #         if translate == name:
    #             translate = ''
    #     except KeyError:
    #         translate = ''
    #     return {'musicid': raw[2], 'match': 1, 'name': name, 'translate': translate}
    # return matchname(alias)
    return 0


def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_hangul(text):
    return any('\uac00' <= char <= '\ud7a3' for char in text)


def get_best_match(alias, data, match, is_translation=False, is_kr=False, is_main_data=False):
    for music in data:
        title = music["infos"][0]["title"] if is_kr else music.get('title', '')
        if is_main_data:
            title = convert(title, 'zh-cn')
        fuzzy_match = string_similar(alias.lower(), title.lower())
        exact_match = get_match_rate_sqrt(alias.lower(), title.lower())
        similar = max(exact_match, fuzzy_match)
        if similar > match['match']:
            match['match'] = similar
            match['musicid'] = music['id']
            if not is_translation:
                match['name'] = title


def match_trans(alias, trans, match):
    for id, translate in trans.items():
        # 拆分翻译选项，以斜线为分隔符
        translate_options = translate.split('/')
        
        for option in translate_options:
            fuzzy_match = string_similar(alias.lower(), option.lower())
            exact_match = get_match_rate_sqrt(alias.lower(), option.lower())
            similar = max(exact_match, fuzzy_match)

            if similar > match['match']:
                match['match'] = similar
                match['musicid'] = id
                match['translate'] = option  # 保存当前匹配的翻译选项


def matchname(alias):
    alias = convert(alias, 'zh-cn')
    match = {'musicid': 0, 'match': 0, 'name': '', 'translate': ''}

    main_data = load_data('masterdata/musics.json')
    en_data = load_data('../enapi/masterdata/musics.json')
    kr_data = load_data('../krapi/masterdata/musics.json') if is_hangul(alias) else []
    with open('yamls/translate.yaml', encoding='utf-8') as f:
        trans = yaml.load(f, Loader=yaml.FullLoader)['musics']

    get_best_match(alias, main_data, match, is_main_data=True)
    get_best_match(alias, en_data, match)
    match_trans(alias, trans, match)
    if is_hangul(alias):
        get_best_match(alias, kr_data, match, is_kr=True)

    if match['musicid']:
        original_name = next((m['title'] for m in main_data if m['id'] == match['musicid']), '')
        match['name'] = original_name
        match['translate'] = trans.get(match['musicid'], '')

    return match


def get_filectime(file):
    return datetime.datetime.fromtimestamp(os.path.getmtime(file))


def isleak(musicid):
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in musics:
        if i['id'] == musicid:
            if int(time.time() * 1000) < i['publishedAt']:
                return True
            else:
                return False
    return True


def pjskinfo(musicid):
    if os.path.exists(f'piccache/pjskinfo/{musicid}.png'):
        pjskinfotime = get_filectime(f'piccache/pjskinfo/{musicid}.png')
        masterdatatime = get_filectime('masterdata/musics.json')
        with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
            musics = json.load(f)
        publishedAt = 0
        for i in musics:
            if i['id'] == musicid:
                publishedAt = i['publishedAt'] / 1000
        if pjskinfotime > masterdatatime:  # 缓存后数据未变化
            if time.time() < publishedAt:  # 捷豹
                return True
            else:  # 已上线
                if pjskinfotime.timestamp() < publishedAt:  # 缓存是上线前的
                    return drawpjskinfo(musicid)
                return False
        else:
            return drawpjskinfo(musicid)
    else:
        return drawpjskinfo(musicid)


def drawpjskinfo(musicid):
    info = musicinfo()
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for music in data:
        if music['id'] == musicid:
            info.title = music['title']
            info.lyricist = music['lyricist']
            info.composer = music['composer']
            info.arranger = music['arranger']
            info.publishedAt = music['publishedAt']
            info.fillerSec = music['fillerSec']
            info.categories = music['categories']
            info.assetbundleName = music['assetbundleName']
            break
    else:
        raise KeyError("日服不存在该歌曲；The song doesn't exist in JP ver")
    
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    difficulties = ['easy', 'normal', 'hard', 'expert', 'master', 'append']
    found_difficulties = set()
    for entry in data:
        if entry['musicId'] == musicid:
            difficulty = entry['musicDifficulty']
            if difficulty in difficulties:
                index = difficulties.index(difficulty)
                info.playLevel[index] = entry['playLevel']
                info.noteCount[index] = entry['totalNoteCount']
                found_difficulties.add(difficulty)
        if found_difficulties == set(difficulties):
            break
    now = int(time.time() * 1000)
    leak = False


    if os.path.exists(f'pics/pjskinfo/{musicid}.png'):
        color = (255, 255, 255)
        alpha = True
        img = Image.open(f'pics/pjskinfo/{musicid}.png')
        if now < info.publishedAt:
            img2 = Image.open('pics/leak_alpha.png')
            leak = True
        else:
            img2 = Image.open('pics/pjskinfo_alpha.png')
        r, g, b, mask = img2.split()
        img.paste(img2, (0, 0), mask)
    else:
        alpha = False
        color = (67, 70, 101)
        if now < info.publishedAt:
            raise LeakContent
            img = Image.open('pics/leak.png')
            leak = True
        else:
            img = Image.open('pics/pjskinfo.png')
    try:
        jacket = Image.open('data/assets/sekai/assetbundle/resources'
                            f'/startapp/music/jacket/{info.assetbundleName}/{info.assetbundleName}.png')
        jacket = jacket.resize((650, 650))
        img.paste(jacket, (80, 47))
    except FileNotFoundError:
        pass
    font_style = ImageFont.truetype("fonts/KOZGOPRO-BOLD.OTF", 90)
    size = font_style.getsize(info.title)
    if size[0] < 1150:
        highplus = 0
    else:
        size = int(90 * (1150 / size[0]))
        font_style = ImageFont.truetype("fonts/KOZGOPRO-BOLD.OTF", size)
        text_width = font_style.getsize(info.title)
        if text_width[1] != 90:
            highplus = (90 - text_width[1]) / 2
        else:
            highplus = 0
    draw = ImageDraw.Draw(img)
    # 标题
    if not alpha:
        draw.text((760, 100 + highplus), info.title, fill=(1, 255, 221), font=font_style)
    else:
        draw.text((760, 100 + highplus), info.title, fill=(255, 255, 255), font=font_style)
    # 作词作曲编曲
    font_style = ImageFont.truetype("fonts/KOZGOPRO-BOLD.OTF", 40)
    draw.text((930, 268), info.lyricist, fill=(255, 255, 255), font=font_style)
    draw.text((930, 350), info.composer, fill=(255, 255, 255), font=font_style)
    draw.text((930, 430), info.arranger, fill=(255, 255, 255), font=font_style)
    # 长度
    info.length = parse_bpm(musicid)[3]
    if info.length is not None:
        length = f'{round(info.length, 1)}秒 ({int(info.length / 60)}分{round(info.length - int(info.length / 60) * 60, 1)}秒)'
    else:
        length = 'No data'
    draw.text((928, 514), length, fill=(255, 255, 255), font=font_style)
    # 上线时间
    if info.publishedAt < 1601438400000:
        info.publishedAt = 1601438400000
    Time = datetime.datetime.fromtimestamp(info.publishedAt / 1000,
                                           pytz.timezone('Asia/Shanghai')).strftime('%Y/%m/%d %H:%M:%S (UTC+8)')
    draw.text((930, 593), Time, fill=(255, 255, 255), font=font_style)

    if all(x == 0 for x in info.playLevel[:5]):  # 只有append难度
        diff_img = Image.open('pics/pjskinfo_diff3.png')
        img.paste(diff_img, (80, 700), diff_img.split()[3])
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 60)
        text_width = font_style.getsize(str(info.playLevel[5]))
        text_coordinate = (int(545 - text_width[0] / 2), int(823 - text_width[1] / 2))
        draw.text(text_coordinate, str(info.playLevel[5]), fill=(1, 255, 221), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 45)
        text_width = font_style.getsize(str(info.noteCount[5]))
        text_coordinate = (int(543 - text_width[0] / 2), int(910 - text_width[1] / 2))
        draw.text(text_coordinate, str(info.noteCount[5]), fill=color, font=font_style)
    else:
        if info.playLevel[5] == 0:
            x_add = 60
            diff_img = Image.open('pics/pjskinfo_diff1.png')
            img.paste(diff_img, (80, 700), diff_img.split()[3])
        else:
            x_add = 0
            diff_img = Image.open('pics/pjskinfo_diff2.png')
            img.paste(diff_img, (20, 700), diff_img.split()[3])
            font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 60)
            text_width = font_style.getsize(str(info.playLevel[5]))
            text_coordinate = (int(707 - text_width[0] / 2), int(873 - text_width[1] / 2))
            draw.text(text_coordinate, str(info.playLevel[5]), fill=(1, 255, 221), font=font_style)
            font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 45)
            text_width = font_style.getsize(str(info.noteCount[5]))
            text_coordinate = (int(705 - text_width[0] / 2), int(960 - text_width[1] / 2))
            draw.text(text_coordinate, str(info.noteCount[5]), fill=color, font=font_style)

        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 60)
        for i in range(0, 5):
            text_width = font_style.getsize(str(info.playLevel[i]))
            text_coordinate = (int((105 + x_add + 118 * i) - text_width[0] / 2), int(873 - text_width[1] / 2))
            draw.text(text_coordinate, str(info.playLevel[i]), fill=(1, 255, 221), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 45)
        for i in range(0, 5):
            text_width = font_style.getsize(str(info.noteCount[i]))
            text_coordinate = (int((103 + x_add + 118 * i) - text_width[0] / 2), int(960 - text_width[1] / 2))
            draw.text(text_coordinate, str(info.noteCount[i]), fill=color, font=font_style)

    # 1824 592
    pos = 1834
    count = 0
    for type in info.categories:
        if type == 'mv':
            type = 'mv_3d'
        if type == 'image':
            continue
        type_pic = Image.open(f'pics/{type}.png')
        type_pic = type_pic.resize((75, 75))
        img.paste(type_pic, (pos, 592), type_pic.split()[3])
        count += 1
        pos -= 82

    vocals = vocalimg(musicid, alpha)
    r, g, b, mask = vocals.split()
    if vocals.size[1] < 320:
        img.paste(vocals, (758, 710), mask)
    else:
        img.paste(vocals, (758, 670), mask)

    if not leak:
        qidong = Image.open(f'pics/qidong/{get_random_character(musicid)}.png')
        qidong = qidong.resize((355, 307))
        img.paste(qidong, (1510, 720), qidong.split()[3])

    img.save(f'piccache/pjskinfo/{musicid}.png')
    if env != 'prod':
        img.show()
    return leak

def vocalimg(musicid, alpha):
    if alpha:
        color = (255, 255, 255)
    else:
        color = (67, 70, 101)
    with open('masterdata/musicVocals.json', 'r', encoding='utf-8') as f:
        musicVocals = json.load(f)
    with open('masterdata/outsideCharacters.json', 'r', encoding='utf-8') as f:
        outsideCharacters = json.load(f)
    pos = 20
    row = 0
    height = [20, 92, 164, 236, 308]
    cut = [0, 0]
    vs = 0
    sekai = 0
    noan = True

    for vocal in musicVocals:
        if vocal['musicId'] == musicid:
            if vocal['musicVocalType'] == "original_song":
                vs += 1
            elif vocal['musicVocalType'] == "sekai":
                sekai += 1
            elif vocal['musicVocalType'] == "virtual_singer":
                vs += 1
            elif vocal['musicVocalType'] == "instrumental":
                img = Image.open('pics/inst.png')
                if alpha:
                    bright_enhancer = ImageEnhance.Brightness(img)
                    img = bright_enhancer.enhance(0.9)
                return img
            else:
                noan = False
                break
    if vs > 1:
        noan = False

    if noan:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
        img = Image.open('pics/vocal.png')
        if alpha:
            bright_enhancer = ImageEnhance.Brightness(img)
            img = bright_enhancer.enhance(0.9)
        if vs == 0:
            draw = ImageDraw.Draw(img)
            draw.text((220, 102), 'SEKAI Ver. ONLY', fill=(227, 246, 251), font=font_style)
        if sekai == 0:
            draw = ImageDraw.Draw(img)
            draw.text((165, 257), 'Virtual Singer Ver. ONLY', fill=(227, 246, 251), font=font_style)
        for vocal in musicVocals:
            if vocal['musicId'] == musicid:
                vocalimg = Image.new('RGBA', (750, 85), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(vocalimg)
                innerpos = 0
                count = 1
                for chara in vocal['characters']:
                    if chara['characterType'] == 'game_character':
                        chara = Image.open(f'chara/chr_ts_{chara["characterId"]}.png').resize((70, 70))
                        r, g, b, mask = chara.split()
                        vocalimg.paste(chara, (innerpos + 5, 8), mask)
                        innerpos += 80
                    else:
                        try:
                            chara = Image.open(f'chara/outsideCharacters/{chara["characterId"]}.png').resize((70, 70))
                            r, g, b, mask = chara.split()
                            vocalimg.paste(chara, (innerpos + 5, 8), mask)
                            innerpos += 80
                        except:
                            for i in outsideCharacters:
                                if i['id'] == chara['characterId']:
                                    if count == 1:
                                        draw.text((innerpos + 8, 20), i['name'], fill=(67, 70, 101), font=font_style)
                                        innerpos += 8 + font_style.getsize(str(i['name']))[0]
                                    else:
                                        draw.text((innerpos + 8, 20), ', ' + i['name'], fill=(67, 70, 101), font=font_style)
                                        innerpos += 8 + font_style.getsize(str(', ' + i['name']))[0]
                    count += 1
                vocalimg = vocalimg.crop((0, 0, innerpos + 15, 150))
                r, g, b, mask = vocalimg.split()
                if vocal['musicVocalType'] == "original_song" or vocal['musicVocalType'] == "virtual_singer":
                    img.paste(vocalimg, (370 - int(vocalimg.size[0] / 2), 162 - int(vocalimg.size[1] / 2)), mask)
                elif vocal['musicVocalType'] == "sekai":
                    img.paste(vocalimg, (370 - int(vocalimg.size[0] / 2), 317 - int(vocalimg.size[1] / 2)), mask)
    else:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 27)
        img = Image.new('RGBA', (720, 380), color=(0, 0, 0, 0))
        for vocal in musicVocals:
            if vocal['musicId'] == musicid:
                vocalimg = Image.new('RGBA', (700, 70), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(vocalimg)
                if vocal['musicVocalType'] == "original_song":
                    text = '原曲版'
                elif vocal['musicVocalType'] == "sekai":
                    text = 'SEKAI版'
                elif vocal['musicVocalType'] == "virtual_singer":
                    text = 'V版'
                elif vocal['musicVocalType'] == "april_fool_2022":
                    text = '愚人节版'
                elif vocal['musicVocalType'] == "another_vocal":
                    text = '其他'
                elif vocal['musicVocalType'] == "instrumental":
                    text = '无人声伴奏'
                else:
                    text = vocal['musicVocalType']
                innerpos = 25 + font_style.getsize(str(text))[0]
                draw.text((20, 20), text, fill=color, font=font_style)
                for chara in vocal['characters']:
                    if chara['characterType'] == 'game_character':
                        chara = Image.open(f'chara/chr_ts_{chara["characterId"]}.png').resize((60, 60))
                        r, g, b, mask = chara.split()
                        vocalimg.paste(chara, (innerpos + 5, 8), mask)
                        innerpos += 65
                    else:
                        try:
                            chara = Image.open(f'chara/outsideCharacters/{chara["characterId"]}.png').resize((60, 60))
                            r, g, b, mask = chara.split()
                            vocalimg.paste(chara, (innerpos + 5, 8), mask)
                            innerpos += 65
                        except:
                            for i in outsideCharacters:
                                if i['id'] == chara['characterId']:
                                    draw.text((innerpos + 8, 20), i['name'], fill=(67, 70, 101), font=font_style)
                                    innerpos += 8 + font_style.getsize(str(i['name']))[0]
                vocalimg = vocalimg.crop((0, 0, innerpos + 15, 72))
                r, g, b, mask = vocalimg.split()

                if pos + vocalimg.size[0] > 720:
                    pos = 20
                    row += 1
                img.paste(vocalimg, (pos, height[row]), mask)
                if pos + vocalimg.size[0] > cut[0]:
                    cut[0] = pos + vocalimg.size[0]
                pos += vocalimg.size[0]
                if (vocal['musicVocalType'] == "sekai" or vocal['musicVocalType'] == "original_song"
                    or vocal['musicVocalType'] == "virtual_singer") and pos != 20:
                    pos = 20
                    row += 1
        if pos == 20:
            row -= 1
        cut[1] = height[row] + 65
        img = img.crop((0, 0, cut[0] + 10, cut[1] + 10))
    return img


def get_random_character(music_id):
    # 从 json 文件加载数据
    with open('masterdata/musicVocals.json', 'r', encoding='utf-8') as f:
        vocals_data = json.load(f)

    # 根据 musicId 筛选 vocals
    relevant_vocals = [vocal for vocal in vocals_data if vocal['musicId'] == music_id]

    # 根据 musicVocalType 和 characterType 筛选 vocals，按照优先级进行筛选
    vocals_by_type = {}
    has_outside_character = False
    for vocal in relevant_vocals:
        music_vocal_type = vocal['musicVocalType']
        if music_vocal_type not in vocals_by_type:
            vocals_by_type[music_vocal_type] = []
        for character in vocal['characters']:
            if character['characterType'] == 'game_character':
                vocals_by_type[music_vocal_type].append(character['characterId'])
            elif character['characterType'] == 'outside_character':
                has_outside_character = True

    # 尝试从 sekai，然后 original_song，然后其他的获取角色
    for vocal_type in ['sekai', 'original_song']:
        if vocal_type in vocals_by_type and vocals_by_type[vocal_type]:
            return random.choice(vocals_by_type[vocal_type])

    # 如果没有 sekai 或 original_song 的角色，从其他的获取随机角色
    other_character_ids = [character_id for vocal_type, characters in vocals_by_type.items() if vocal_type not in ['sekai', 'original_song'] for character_id in characters]
    if other_character_ids:
        return random.choice(other_character_ids)
    
    # 如果只有 outside_character，返回 1 和 26 之间的随机数
    return random.randint(1, 26)



def pjskset(newalias, oldalias, qqnum, username, qun, is_hide=False):
    # newalias = newalias.strip()
    # if isSingleEmoji(newalias):
    #     return "由于数据库排序规则原因，不支持单个emoji字符作为歌曲昵称"
    # resp = aliastomusicid(oldalias)
    # if resp['musicid'] == 0:
    #     return "找不到你要设置的歌曲，请使用正确格式：pjskset新昵称to旧昵称"
    # musicid = resp['musicid']
    # if not recordname(qqnum, 'pjskset', newalias):
    #     return "该昵称可能不合规，如果判断错误请联系bot主添加"
    # mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
    #                        database='pjsk', charset='utf8mb4')
    # mycursor = mydb.cursor()
    # sql = f"insert into pjskalias(ALIAS,MUSICID) values (%s, %s) " \
    #       f"on duplicate key update musicid=%s"
    # val = (newalias, musicid, musicid)
    # mycursor.execute(sql, val)
    # mydb.commit()
    # mycursor.close()
    # mydb.close()
    #
    # with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    # title = ''
    # for music in data:
    #     if music['id'] != musicid:
    #         continue
    #     title = music['title']
    # timeArray = time.localtime(time.time())
    # Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    # writelog(f'[{Time}] {qun} {username}({qqnum}): {newalias}->{title}')
    # if is_hide:
    #     return f"设置成功！\n已记录bot文档中公开的实时日志，设置不合适的昵称将会被拉黑"
    # else:
    #     return f"设置成功！{newalias}->{title}\n已记录bot文档中公开的实时日志，设置不合适的昵称将会被拉黑"
    return None


def pjskdel(alias, qqnum, username, qun):
    # alias = alias.strip()
    # resp = aliastomusicid(alias)
    # if resp['match'] != 1:
    #     return "找不到你要设置的歌曲，请使用正确格式：pjskdel昵称"
    # mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
    #                        database='pjsk', charset='utf8mb4')
    # mycursor = mydb.cursor()
    # mycursor.execute("DELETE from pjskalias where alias=%s", (alias,))
    # mydb.commit()
    # mycursor.close()
    # mydb.close()
    # timeArray = time.localtime(time.time())
    # Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    # if str(qqnum) == '1103479519':
    #     writelog(f'[{Time}] 管理员删除了{resp["name"]}的昵称：{alias}')
    #     return "删除成功！"
    # writelog(f'[{Time}] {qun} {username}({qqnum}): 删除了{resp["name"]}的昵称：{alias}')
    # return "删除成功！\n已记录bot文档中公开的实时日志，乱删将被拉黑"
    return None


def pjskalias(alias, musicid=None):
    # from imageutils import text2image
    # if musicid is None:
    #     resp = aliastomusicid(alias)
    #     if resp['musicid'] == 0:
    #         return "找不到你说的歌曲哦"
    #     musicid = resp['musicid']
    #     if resp['translate'] == '':
    #         returnstr = f"{resp['name']}\n匹配度:{round(resp['match'], 4)}\n"
    #     else:
    #         returnstr = f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}\n"
    # else:
    #     returnstr = ''
    # mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
    #                        database='pjsk', charset='utf8mb4')
    # mycursor = mydb.cursor()
    # mycursor.execute('SELECT * from pjskalias where musicid=%s', (musicid,))
    # respdata = mycursor.fetchall()
    # mycursor.close()
    # mydb.close()
    # for raw in respdata:
    #     returnstr = returnstr + raw[1] + "，"
    # if len(returnstr[:-1]) > 170:
    #     infopic = text2image(text=returnstr[:-1] + '\n昵称均为用户添加，与bot和bot主无关\n\n', max_width=800, padding=(30, 30))
    #     infopic.save(f'piccache/{musicid}alias.png')
    #     return f"[CQ:image,file=file:///{os.getcwd()}/piccache/{musicid}alias.png,cache=0]"
    # else:
    #     return returnstr[:-1] + '\n昵称均为用户添加，与bot和bot主无关'
    return None


def pjskalias2(alias, musicid=None):
    if musicid is None:
        resp = aliastomusicid(alias)
        if resp['musicid'] == 0:
            return "找不到你说的歌曲哦"
        musicid = resp['musicid']
        if resp['translate'] == '':
            returnstr = f"{resp['name']}\n匹配度:{round(resp['match'], 4)}\n"
        else:
            returnstr = f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}\n"
    else:
        returnstr = ''
    # mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
    #                        database='pjsk', charset='utf8mb4')
    # mycursor = mydb.cursor()
    # mycursor.execute('SELECT * from pjskalias where musicid=%s', (musicid,))
    # respdata = mycursor.fetchall()
    # mycursor.close()
    # mydb.close()
    # count = 0
    # data = []
    # for raw in respdata:
    #     count += 1
    #     data.append({'id': count, 'alias': raw[1]})
    # return data


def txt2html(txt):
    def escape(txt):
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        txt = txt.replace('\'', '&#39;')
        return txt

    def format_line(line):
        line = escape(line)

        # 高亮时间戳
        line = re.sub(r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\])', r'<span style="color:blue;">\1</span>', line)

        # 箭头两端的文字加粗下划线
        line = re.sub(r': (.+?)-&gt;(.+)', r': <b><u>\1</u></b>-><b><u>\2</u></b>', line)

        # 删除了xxx的昵称：xxxx，把xxx内容下划线
        line = re.sub(r'删除了(.+?)的昵称：(.+)', r'删除了<u>\1</u>的昵称：<u>\2</u>', line)

        return line

    lines = txt.split('\n')
    for i, line in enumerate(lines):
        lines[i] = format_line(line) + '<br/>'
    txt = ''.join(lines)

    return r'<!doctype html><html><head><meta charset="utf-8"><title>日志</title></head><body>' + txt + '</body></html>'

def writelog(text=None):
    today = datetime.datetime.today()
    if text is not None:
        with open(f'logs/{today.year}{str(today.month).zfill(2)}.txt', 'a', encoding='utf-8') as f:
            print(text, file=f)
    logtohtml(f'logs/{today.year}{str(today.month).zfill(2)}.txt')


def logtohtml(dir):
    # with open(dir, 'r', encoding='utf-8') as f:
    #     log = f.read()
    # today = datetime.datetime.today()
    # with open(f"{loghtml}{today.year}{str(today.month).zfill(2)}.html", 'w', encoding='utf-8') as f:
    #     f.write(txt2html(log))
    # if env == 'prod':
    #     uploadLogR2(f"{loghtml}{today.year}{str(today.month).zfill(2)}.html", f"logs/{today.year}{str(today.month).zfill(2)}.html")
    pass


def musiclength(musicid, fillerSec=0):
    audiodir = 'data/assets/sekai/assetbundle/resources/ondemand/music/long'
    try:
        with open('masterdata/musicVocals.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for vocal in data:
            if vocal['musicId'] == musicid:
                audio = MP3(fr"{audiodir}\{vocal['assetbundleName']}\{vocal['assetbundleName']}.mp3")
                return audio.info.length - fillerSec
        return 0
    except:
        return 0

if __name__ == '__main__':
    # print(musiclength(49))
    # logtohtml()
    # pjskset('ws32', 'wonders')
    # print(pjskdel('ws32'))
    # resp = aliastomusicid('16bit')

    # resp = aliastomusicid('てらてら')
    # drawpjskinfo(resp['musicid'])
    #print(pjskalias('机关枪'))
    pass
