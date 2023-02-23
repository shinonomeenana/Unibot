import datetime
import io
import ujson as json
import os
import re
import sqlite3
import time
import traceback
import pymysql
from modules.mysql_config import *
import aiofiles
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dateutil.tz import tzlocal

from modules.config import proxies
from modules.pjskinfo import aliastomusicid
from modules.profileanalysis import userprofile, generatehonor
from moesus.music_score import parse, genGuessChart


assetpath = 'data/assets/sekai/assetbundle/resources'


def hotrank():
    with open('masterdata/realtime/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in range(0, len(musics)):
        try:
            musics[i]['hot']
        except KeyError:
            musics[i]['hot'] = 0
    musics.sort(key=lambda x: x["hot"], reverse=True)
    text = ''
    for i in range(0, 40):
        text = text + f"{i + 1} {musics[i]['title']} ({int(musics[i]['hot'])})\n"

    IMG_SIZE = (500, 40 + 33 * 34)
    img = Image.new('RGB', IMG_SIZE, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 18)
    draw.text((20, 20), '热度排行Top40', '#000000', font, spacing=10)
    font = ImageFont.truetype('fonts/FOT-RodinNTLGPro-DB.ttf', 18)
    draw.text((20, 53), text, '#000000', font, spacing=10)
    font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 15)
    updatetime = time.localtime(os.path.getmtime(r"masterdata/realtime/musics.json"))
    draw.text((20, 1100), '数据来源：https://profile.pjsekai.moe/\nUpdated in '
              + time.strftime("%Y-%m-%d %H:%M:%S", updatetime), '#000000', font)
    img.save(f'piccache/hotrank.png')


def idtoname(musicid):
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in musics:
        if i['id'] == musicid:
            return i['title']
    return ''


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


def levelrank(level, difficulty, fcap=0):
    target = []
    with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open('masterdata/realtime/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in data:
        if i['playLevel'] == level and i['musicDifficulty'] == difficulty:
            try:
                i['playLevelAdjust']
                target.append(i)
            except KeyError:
                pass
    if fcap == 0:
        title = f'{difficulty.upper()} {level}难度排行（仅供参考）'
        target.sort(key=lambda x: x["playLevelAdjust"], reverse=True)
    elif fcap == 1:
        title = f'{difficulty.upper()} {level}FC难度排行（仅供参考）'
        target.sort(key=lambda x: x["fullComboAdjust"], reverse=True)
    else:
        title = f'{difficulty.upper()} {level}AP难度排行（仅供参考）'
        target.sort(key=lambda x: x["fullPerfectAdjust"], reverse=True)
    text = ''
    musictitle = ''
    for i in target:
        for j in musics:
            if j['id'] == i['musicId']:
                musictitle = j['title']
                break
        if fcap == 0:
            text = text + f"{musictitle} ({round(i['playLevel'] + i['playLevelAdjust'], 1)})\n"
        elif fcap == 1:
            text = text + f"{musictitle} ({round(i['playLevel'] + i['fullComboAdjust'], 1)})\n"
        else:
            text = text + f"{musictitle} ({round(i['playLevel'] + i['fullPerfectAdjust'], 1)})\n"
    if text == '':
        return False
    IMG_SIZE = (500, int(100 + text.count('\n') * 31.5))
    img = Image.new('RGB', IMG_SIZE, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 22)
    draw.text((20, 15), title, '#000000', font, spacing=10)
    font = ImageFont.truetype('fonts/FOT-RodinNTLGPro-DB.ttf', 22)
    draw.text((20, 55), text, '#000000', font, spacing=10)
    font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 15)
    updatetime = time.localtime(os.path.getmtime(r"masterdata/realtime/musicDifficulties.json"))
    draw.text((20, int(45 + text.count('\n') * 31.5)), '数据来源：https://profile.pjsekai.moe/\nUpdated in '
              + time.strftime("%Y-%m-%d %H:%M:%S", updatetime), '#000000', font)
    img = img.convert("RGB")
    img.save(f'piccache/{level}{difficulty}{fcap}.jpg', quality=80)
    return True


def levelRankPic(level, difficulty, fcap=0, userid=None, isprivate=False, server='jp', qqnum='未知'):
    target = []
    with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open('masterdata/realtime/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in data:
        if (i['playLevel'] == level if level != 0 else True) and i['musicDifficulty'] == difficulty:
            try:
                i['playLevelAdjust']
                target.append(i)
            except KeyError:
                pass

    if fcap == 0:
        title = f'{difficulty.upper()} {level if level != 0 else ""} 难度表（仅供参考）'
        playLevelKey = "playLevelAdjust"
    elif fcap == 1:
        title = f'{difficulty.upper()} {level if level != 0 else ""} FC难度表（仅供参考）'
        playLevelKey = "fullComboAdjust"
    else:
        title = f'{difficulty.upper()} {level if level != 0 else ""} AP难度表（仅供参考）'
        playLevelKey = "fullPerfectAdjust"

    target.sort(key=lambda x: x['playLevel'] + x[playLevelKey], reverse=True)
    musicData = {}
    for music in target:
        levelRound = str(round(music['playLevel'] + music[playLevelKey], 1))
        try:
            musicData[levelRound].append(music['musicId'])
        except KeyError:
            musicData[levelRound] = [music['musicId']]

    rankPic = singleLevelRankPic(musicData, difficulty, oneRowCount=None if level != 0 else 5)
    rankPic = rankPic.resize((int(rankPic.size[0] / 1.8), int(rankPic.size[1] / 1.8)))
    pic = Image.new("RGBA", (rankPic.size[0] + 20 if rankPic.size[0] > 520 else 600, rankPic.size[1] + 430), (205, 255, 255, 255))
    bg = Image.open('pics/findevent.png')
    picRatio = pic.size[0] / pic.size[1]
    bgRatio = bg.size[0] / bg.size[1]
    if picRatio > bgRatio:
        bg = bg.resize((pic.size[0], int(pic.size[0] / bgRatio)))
    else:
        bg = bg.resize((int(pic.size[1] * bgRatio), pic.size[1]))

    pic.paste(bg, (0, 0))
    userdataimg = Image.open('pics/userdata.png')
    r,g,b,mask = userdataimg.split()
    pic.paste(userdataimg, (0, 0), mask)
    draw = ImageDraw.Draw(pic)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    draw.text((215, 65), '数据已无法获取', fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 15)
    draw.text((218, 114), '由于日服api限制，详细打歌数据已停用', fill=(0, 0, 0), font=font_style)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 30)
    draw.text((65, 264), title, fill=(0, 0, 0), font=font_style)

    r, g, b, mask = rankPic.split()
    pic.paste(rankPic, (40, 320), mask)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 23)
    updatetime = time.localtime(os.path.getmtime(r"masterdata/realtime/musicDifficulties.json"))
    draw.text((50, pic.size[1] - 110), 'Generated by Unibot', fill='#00CCBB', font=font_style)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 16)
    draw.text((50, pic.size[1] - 70), '定数来源：https://profile.pjsekai.moe/   ※定数非官方\n', fill='#00CCBB',
              font=font_style)
    draw.text((50, pic.size[1] - 40), f'Updated in {time.strftime("%Y-%m-%d %H:%M:%S", updatetime)}        '
                                      '※定数每次统计时可能会改变', fill='#00CCBB', font=font_style)
    pic = pic.convert("RGB")
    pic.save(f'piccache/{userid}{level}{difficulty}{fcap}.jpg', quality=80)
    return f'piccache/{userid}{level}{difficulty}{fcap}.jpg'


def singleLevelRankPic(musicData, difficulty, musicResult=None, oneRowCount=None):
    diff = {
        'easy': 0,
        'normal': 1,
        'hard': 2,
        'expert': 3,
        'master': 4
    }
    color = {
        'master': (187, 51, 238),
        'expert': (238, 67, 102),
        'hard': (254, 170, 0),
        'normal': (51, 187, 238),
        'easy': (102, 221, 17),
    }
    iconName = {
        0: 'icon_notClear.png',
        1: 'icon_clear.png',
        2: 'icon_fullCombo.png',
        3: 'icon_allPerfect.png',
    }
    pics = []

    # 总高度 查看所有歌曲时高度适当增加
    finalHeight = 1750 if oneRowCount is None else 2800

    # 每行显示的歌曲数
    if oneRowCount is None:
        oneRowCount = 0
        for rank in musicData:
            if len(musicData[rank]) > oneRowCount:
                oneRowCount = len(musicData[rank])

    # 每一个难度分开画
    for rank in musicData:
        rows = int((len(musicData[rank]) - 1) / oneRowCount) + 1
        singleRank = Image.new("RGBA", (oneRowCount * 130 + 100, rows * 130 + 105), (0, 0, 0, 0))
        draw = ImageDraw.Draw(singleRank)
        font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 45)

        shadow = Image.new("RGBA", (oneRowCount * 130 + 45, rows * 130 + 77), (0, 0, 0, 0))
        shadow.paste(Image.new("RGBA", (oneRowCount * 130 + 35, rows * 130 + 67), (0, 0, 0, 170)), (5, 5))
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        r, g, b, mask = shadow.split()
        singleRank.paste(shadow, (45, 30), mask)

        draw.rectangle((45, 28, oneRowCount * 130 + 75, rows * 130 + 90), fill=(255, 255, 255))

        draw.ellipse((22, 0, 80, 58), fill=color[difficulty])
        draw.rectangle((51, 0, 134, 58), fill=color[difficulty])
        draw.ellipse((105, 0, 163, 58), fill=color[difficulty])
        draw.text((45, -7), rank, (255, 255, 255), font)
        row = 0
        i = 0
        for musicId in musicData[rank]:
            jacket = Image.open(
                f'{assetpath}/startapp/thumbnail/music_jacket/jacket_s_{str(musicId).zfill(3)}.png')
            jacket = jacket.resize((120, 120))
            singleRank.paste(jacket, (70 + 130 * i, 72 + 130 * row))
            if musicResult is not None:
                icon = Image.open(f'pics/{iconName[musicResult[musicId][diff[difficulty]]]}')
                r, g, b, mask = icon.split()
                singleRank.paste(icon, (162 + 130 * i, 164 + 130 * row), mask)
            i += 1
            if i == oneRowCount:
                i = 0
                row += 1
        pics.append(singleRank)

    # 将所有难度合并
    height = 0
    for singlePic in pics:
        height += singlePic.size[1]
    colunm = int(height / finalHeight) + 1
    pic = Image.new("RGBA", ((oneRowCount * 130 + 100) * colunm, height if colunm == 1 else finalHeight), (0, 0, 0, 0))
    pos = [0, 0]
    for singlePic in pics:
        if pos[1] + singlePic.size[1] > finalHeight:
            pos[0] += oneRowCount * 130 + 100
            pos[1] = 0
        r, g, b, mask = singlePic.split()
        pic.paste(singlePic, (pos[0], pos[1]), mask)
        pos[1] += singlePic.size[1] - 20

    # 由于末尾空出的空间相加可能会导致行数+1 这里裁剪一下
    pic = pic.crop((0, 0, pos[0] + oneRowCount * 130 + 160, pic.size[1]))
    return pic


# from https://gitlab.com/pjsekai/musics/-/blob/main/music_bpm.py
def parse_bpm(music_id, diff='expert'):
    try:
        with open('data/assets/sekai/assetbundle/resources'
                  '/startapp/music/music_score/%04d_01/%s' % (music_id, diff), encoding='utf-8') as f:
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


def getPlayLevel(musicid, difficulty):
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        musicDifficulties = json.load(f)
    for diff in musicDifficulties:
        if musicid == diff['musicId'] and diff['musicDifficulty'] == difficulty:
            return diff['playLevel']


def getchart(musicid, difficulty, theme='white'):
    path = f'charts/moe/{theme}/{musicid}/{difficulty}.jpg'
    if os.path.exists(path):  # 本地有缓存
        return path
    else:  # 本地无缓存
        if not os.path.exists(path[:-3] + 'png'):
            withSkill = False if theme != 'skill' else True
            parse(musicid, difficulty, theme, withSkill=withSkill)  # 生成moe
        im = Image.open(path[:-3] + 'png')
        # im = im.convert('RGB')
        im.save(path, quality=60)
        return path

def getcharttheme(qqnum):
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * from chartprefer where qqnum=%s', (qqnum,))
    data = mycursor.fetchone()
    mycursor.close()
    mydb.close()
    if data is not None:
        return data[2]
    return 'white'

def gensvg():
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for music in musics:
        for diff in ['master', 'expert', 'hard', 'normal', 'easy']:
            if not os.path.exists(f'charts/moe/svg/{music["id"]}/{diff}.svg'):
                print('生成谱面', music['id'], diff)
                parse(music['id'], diff, 'svg', False, 'https://assets.unipjsk.com/startapp/music/jacket/%s/%s.png')

def autoGenGuess():
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for music in musics:
        if not os.path.exists(f'charts/moe/guess/{music["id"]}/master.svg'):
            genGuessChart(music['id'])


def setcharttheme(qqnum, theme):
    if theme != 'white' and theme != 'black' and theme != 'color':
        return '白色主题：/theme white\n黑色主题：/theme black\n彩色主题：/theme color'

    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    sql = f"insert into chartprefer (qqnum, prefer) values (%s, %s) " \
          f"on duplicate key update prefer=%s"
    val = (str(qqnum), theme, theme)
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    mydb.close()

    return f'{theme}主题设置成功'


def getsdvxchart(musicid, difficulty):
    try:
        if difficulty == 'master' or difficulty == 'expert':
            if os.path.exists(f'charts/sdvxInCharts/{musicid}/{difficulty}.png'):  # sdvx.in本地有缓存
                return f'charts/sdvxInCharts/{musicid}/{difficulty}.png'
            else:  # 无缓存，尝试下载
                timeid = idtotime(musicid)
                if difficulty == 'master':
                    data = requests.get(f'https://sdvx.in/prsk/obj/data{str(timeid).zfill(3)}mst.png',
                                        proxies=proxies)
                else:
                    data = requests.get(f'https://sdvx.in/prsk/obj/data{str(timeid).zfill(3)}exp.png',
                                        proxies=proxies)
                if data.status_code == 200:  # 下载到了
                    bg = requests.get(f"https://sdvx.in/prsk/bg/{str(timeid).zfill(3)}bg.png",
                                      proxies=proxies)
                    bar = requests.get(f"https://sdvx.in/prsk/bg/{str(timeid).zfill(3)}bar.png",
                                       proxies=proxies)
                    bgpic = Image.open(io.BytesIO(bg.content))
                    datapic = Image.open(io.BytesIO(data.content))
                    barpic = Image.open(io.BytesIO(bar.content))
                    r, g, b, mask = datapic.split()
                    bgpic.paste(datapic, (0, 0), mask)
                    r, g, b, mask = barpic.split()
                    bgpic.paste(barpic, (0, 0), mask)
                    dirs = f'charts/sdvxInCharts/{musicid}'
                    if not os.path.exists(dirs):
                        os.makedirs(dirs)
                    r, g, b, mask = bgpic.split()
                    final = Image.new('RGB', bgpic.size, (0, 0, 0))
                    final.paste(bgpic, (0, 0), mask)
                    final.save(f'charts/sdvxInCharts/{musicid}/{difficulty}.png')
                    return f'charts/sdvxInCharts/{musicid}/{difficulty}.png'
                else:  # 没下载到
                    return None
        else:  # 其他难度
            return None
    except:
        return None


def idtotime(musicid):
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    musics.sort(key=lambda x: x["publishedAt"])
    for i in range(0, len(musics)):
        if musics[i]['id'] == musicid:
            return i + 1
    return 0


def downloadviewerchart(musicid, difficulty):
    try:
        try:
            re = requests.get(f'https://storage.sekai.best/sekai-music-charts/{str(musicid).zfill(4)}/{difficulty}.png',
                              proxies=proxies)
        except:
            re = requests.get(f'https://storage.sekai.best/sekai-music-charts/{str(musicid).zfill(4)}/{difficulty}.png',
                              proxies=None)
        if re.status_code == 200:
            dirs = rf'charts/SekaiViewer/{musicid}'
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            if difficulty == 'master':
                svg = requests.get(f'https://storage.sekai.best/sekai-music-charts/{str(musicid).zfill(4)}/{difficulty}.svg',
                                   proxies=proxies)
                i = 0
                while True:
                    i = i + 1
                    if svg.text.count(f'{str(i).zfill(3)}</text>') == 0:
                        break
                row = int((i - 2) / 4)
                print(row)
                pic = Image.open(io.BytesIO(re.content))
                r, g, b, mask = pic.split()
                final = Image.new('RGB', pic.size, (255, 255, 255))
                final.paste(pic, (0, 0), mask)
                final = final.resize((160 * row + 32, 1300))
                final.save(f'charts/SekaiViewer/{musicid}/{difficulty}.png')
            else:
                pic = Image.open(io.BytesIO(re.content))
                r, g, b, mask = pic.split()
                final = Image.new('RGB', pic.size, (255, 255, 255))
                final.paste(pic, (0, 0), mask)
                final.save(f'charts/SekaiViewer/{musicid}/{difficulty}.png')
            return True
        else:
            return False
    except:
        return False


def aliastochart(full, sdvx=False, qun=False, theme='white'):
    if full[-2:] == 'ex':
        alias = full[:-2]
        diff = 'expert'
    elif full[-2:] == 'hd':
        alias = full[:-2]
        diff = 'hard'
    elif full[-2:] == 'nm':
        alias = full[:-2]
        diff = 'normal'
    elif full[-2:] == 'ez':
        alias = full[:-2]
        diff = 'easy'
    elif full[-2:] == 'ma':
        alias = full[:-2]
        diff = 'master'
    elif full[-6:] == 'expert':
        alias = full[:-6]
        diff = 'expert'
    elif full[-4:] == 'hard':
        alias = full[:-4]
        diff = 'hard'
    elif full[-6:] == 'normal':
        alias = full[:-6]
        diff = 'normal'
    elif full[-4:] == 'easy':
        alias = full[:-4]
        diff = 'easy'
    elif full[-6:] == 'master':
        alias = full[:-6]
        diff = 'master'
    else:
        alias = full
        diff = 'master'
    resp = aliastomusicid(alias)
    if qun and resp['match'] < 0.6:
        return ''
    if resp['musicid'] == 0:
        return None  # 找不到歌曲 return None
    else:
        text = resp['name'] + ' ' + diff.upper() + '\n' + '匹配度: ' + str(round(resp['match'], 4))
        if sdvx:
            dir = getsdvxchart(resp['musicid'], diff)
        else:
            dir = getchart(resp['musicid'], diff, theme)

        bpm = parse_bpm(resp['musicid'])
        bpmtext = ''
        for bpms in bpm[1]:
            bpmtext = bpmtext + ' - ' + str(bpms['bpm']).replace('.0', '')
        if 'sdvxInCharts' in dir:
            text = text + '\nBPM: ' + bpmtext[3:] + '\n谱面图片来自プロセカ譜面保管所'
        elif 'moe' in dir:
            text = text + '\nBPM: ' + bpmtext[3:] + '\n'
        return text, dir



def notecount(count):
    text = ''
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for i in data:
        try:
            if i['noteCount'] == count:
                text += f"{idtoname(i['musicId'])}[{(i['musicDifficulty'].upper())} {i['playLevel']}]\n"
        except KeyError:
            if i['totalNoteCount'] == count:
                text += f"{idtoname(i['musicId'])}[{(i['musicDifficulty'].upper())} {i['playLevel']}]\n"
    if text == '':
        return '没有找到'
    else:
        return text


def tasseiritsu(para):
    intpara = [int(x) for x in para]
    ritsu = (3 * intpara[0] + 2 * intpara[1] + intpara[2]) / (3 * sum(intpara))
    if ritsu < 0.94:
        grade = 'D'
    elif ritsu < 0.97:
        grade = 'C'
    elif ritsu < 0.98:
        grade = 'B'
    elif ritsu < 0.985:
        grade = 'A'
    elif ritsu < 0.99:
        grade = 'S'
    elif ritsu < 0.9925:
        grade = 'S+'
    elif ritsu < 0.995:
        grade = 'SS'
    elif ritsu < 0.9975:
        grade = 'SS+'
    elif ritsu < 0.999:
        grade = 'SSS'
    elif ritsu < 1:
        grade = 'SSS+'
    else:
        grade = 'MAX'
    return f'达成率{grade}\n{round(ritsu * 100, 4)}%/100%'


def findbpm(targetbpm):
    bpm = {}
    text = ''
    with open('masterdata/realtime/musics.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for music in data:
        bpm[music['id']] = parse_bpm(music['id'])[1]
    for musicid in bpm:
        for i in bpm[musicid]:
            if int(i['bpm']) == targetbpm:
                bpmtext = ''
                for bpms in bpm[musicid]:
                    bpmtext += ' - ' + str(bpms['bpm']).replace('.0', '')
                text += f"{idtoname(musicid)}: {bpmtext[3:]}\n"
                break
    if text == '':
        return '没有找到'
    return text


def updaterebase():
    print('\nupdate rebase')
    offset = 0
    timeformat = "%Y-%m-%dT%H:%M:%S.%f%z"
    deletelist = []
    failcount = 0
    while True:
        try:
            resp = requests.get(f'https://gitlab.com/pjsekai/musics/-/refs/main/logs_tree/rebases?format=json&offset={offset}', proxies=proxies)
            offset += 25
            data = resp.json()
            if not data:
                break
            for file in data:
                musicid = int(file['file_name'][:file['file_name'].find('.')])
                if os.path.exists('moesus/rebases/' + file['file_name']):
                    commit_time = datetime.datetime.strptime(file['commit']['committed_date'], timeformat)
                    filetime = datetime.datetime.fromtimestamp(os.path.getmtime('moesus/rebases/' + file['file_name'])).replace(tzinfo=tzlocal())
                    if commit_time > filetime:
                        download_rebase(file['file_name'])
                        if musicid not in deletelist:
                            deletelist.append(musicid)
                else:
                    download_rebase(file['file_name'])
                    if musicid not in deletelist:
                        deletelist.append(musicid)
            failcount = 0
        except:
            failcount += 1
            traceback.print_exc()
            print('下载失败')
            if failcount > 4:
                break
    updatecharts(deletelist)


def download_rebase(file_name):
    print('更新' + file_name)
    for i in range(0, 4):
        try:
            resp = requests.get(f'https://gitlab.com/pjsekai/musics/-/raw/main/rebases/{file_name}?inline=false', proxies=proxies)
            with open('moesus/rebases/' + file_name, 'wb') as f:
                f.write(resp.content)
            return
        except:
            traceback.print_exc()

def updatecharts(deletelist):
    for musicid in deletelist:
        for theme in ['black', 'white', 'color', 'svg']:
            for diff in ['easy', 'normal', 'hard', 'expert', 'master']:
                for fileformat in ['png', 'svg']:
                    path = f'charts/moe/{theme}/{musicid}/{diff}.{fileformat}'
                    if os.path.exists(path):
                        os.remove(path)
                        if theme != 'svg' and diff == 'master' and fileformat == 'svg':
                            print('更新' + path)
                            parse(musicid, diff, theme)
                            im = Image.open(path[:-3] + 'png')
                            # im = im.convert('RGB')
                            im.save(path[:-3] + 'jpg', quality=60)

    gensvg()


def gen_bpm_svg():
    import pandas as pd

    ids = []
    diffs = []    
    names = []
    bpms = []

    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)

    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        musicDifficulties = json.load(f)

    for music in musics:
        ids.append(str(music['id']))

        for diff in musicDifficulties:
            if diff['musicId'] == music['id'] and diff['musicDifficulty'] == 'master':
                diffs.append(str(diff['playLevel']))
                break

        names.append(str(music['title']))
        bpm = parse_bpm(music['id'])
        bpms.append(' - '.join([str(i['bpm']).replace('.0', '') for i in bpm[1]]))

    dataframe = pd.DataFrame({'id': ids, '难度': diffs, '曲名': names, 'bpm': bpms})

    dataframe.to_csv("test/test.csv", index=False, sep=',', encoding='utf_8_sig')


if __name__ == '__main__':
    print(os.path.exists('kk.py'))




