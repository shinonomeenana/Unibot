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
import pjsekai.scores
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dateutil.tz import tzlocal
from selenium import webdriver
from modules.config import proxies, rank_query_ban_servers, env, suite_uploader_path
from modules.pjskinfo import aliastomusicid
from modules.profileanalysis import userprofile, generatehonor


assetpath = 'data/assets/sekai/assetbundle/resources'


def idtoname(musicid):
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in musics:
        if i['id'] == musicid:
            return i['title']
    return ''


def isleak(musicid, musics=None):
    if musics is None:
        with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
            musics = json.load(f)
    for i in musics:
        if i['id'] == musicid:
            if int(time.time() * 1000) < i['publishedAt']:
                return True
            else:
                return False
    return True



def levelRankPic(level, difficulty, fcap=0, userid=None, isprivate=False, server='jp', qqnum='未知'):
    target = []
    with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    now = time.time() * 1000
    for i in data:
        if isleak(i['musicId'], musics):
            continue
        if (i['playLevel'] == level if level != 0 else True) and i['musicDifficulty'] == difficulty:
            try:
                i['playLevelAdjust']
            except KeyError:
                for playLevelKey in ["playLevelAdjust", "fullComboAdjust", "fullPerfectAdjust"]:
                    i[playLevelKey] = None
            target.append(i)

    if fcap == 0:
        title = f'{difficulty.upper()} {level if level != 0 else ""} 难度表（仅供参考）'
        playLevelKey = "playLevelAdjust"
    elif fcap == 1:
        title = f'{difficulty.upper()} {level if level != 0 else ""} FC难度表（仅供参考）'
        playLevelKey = "fullComboAdjust"
    else:
        title = f'{difficulty.upper()} {level if level != 0 else ""} AP难度表（仅供参考）'
        playLevelKey = "fullPerfectAdjust"

    target.sort(key=lambda x: x['playLevel'] + (x[playLevelKey] if x[playLevelKey] is not None else 0), reverse=True)
    musicData = {}
    for music in target:
        if music[playLevelKey] is None:
            if music['playLevel'] < 26:
                levelRound = f"  {music['playLevel']}"
            else:
                levelRound = str(music['playLevel']) + '.?'
        else:
            levelRound = str(round(music['playLevel'] + music[playLevelKey], 1))
        try:
            musicData[levelRound].append(music['musicId'])
        except KeyError:
            musicData[levelRound] = [music['musicId']]

    profile = None
    error = False
    if userid is not None and not isprivate:
        profile = userprofile()
        try:
            profile.getprofile(userid=userid, server=server, qqnum=qqnum, query_type='rank')
            rankPic = singleLevelRankPic(musicData, difficulty, profile.musicResult, oneRowCount=None if level != 0 else 5)
        except:
            profile.isNewData = True
            rankPic = singleLevelRankPic(musicData, difficulty, oneRowCount=None if level != 0 else 5)
            error = True
    else:
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

    if error:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
        draw.text((215, 65), '数据已无法获取', fill=(0, 0, 0), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 15)
        draw.text((218, 114), '由于日服api限制，详细打歌数据已停用', fill=(0, 0, 0), font=font_style)
    elif profile is not None:
        with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
            cards = json.load(f)
        try:
            assetbundleName = ''
            for i in cards:
                if i['id'] == profile.userDecks[0]:
                    assetbundleName = i['assetbundleName']
            if profile.special_training[0]:
                cardimg = Image.open(f'{assetpath}/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
            else:
                cardimg = Image.open(f'{assetpath}/startapp/thumbnail/chara/{assetbundleName}_normal.png')

            cardimg = cardimg.resize((116, 116))
            r, g, b, mask = cardimg.split()
            pic.paste(cardimg, (68, 70), mask)
        except FileNotFoundError:
            pass
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
        draw.text((215, 65), profile.name, fill=(0, 0, 0), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 15)
        draw.text((218, 114), '发送"不给看"可隐藏打歌数据', fill=(0, 0, 0), font=font_style)
        font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 28)
        draw.text((314, 150), str(profile.rank), fill=(255, 255, 255), font=font_style)

        for i in profile.userProfileHonors:
            if i['seq'] == 1:
                try:
                    honorpic = generatehonor(i, True, server, profile.userHonorMissions)
                    honorpic = honorpic.resize((226, 48))
                    r, g, b, mask = honorpic.split()
                    pic.paste(honorpic, (59, 206), mask)
                except:
                    pass

        for i in profile.userProfileHonors:
            if i['seq'] == 2:
                try:
                    honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                    honorpic = honorpic.resize((107, 48))
                    r, g, b, mask = honorpic.split()
                    pic.paste(honorpic, (290, 206), mask)
                except:
                    pass

        for i in profile.userProfileHonors:
            if i['seq'] == 3:
                try:
                    honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                    honorpic = honorpic.resize((107, 48))
                    r, g, b, mask = honorpic.split()
                    pic.paste(honorpic, (403, 206), mask)
                except:
                    pass
    elif isprivate:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
        draw.text((215, 65), '成绩已隐藏', fill=(0, 0, 0), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 15)
        draw.text((218, 114), '发送"给看"可查看歌曲成绩', fill=(0, 0, 0), font=font_style)
    else:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
        draw.text((215, 65), '数据已无法获取', fill=(0, 0, 0), font=font_style)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 15)
        draw.text((218, 114), '由于日服api限制，详细打歌数据已停用', fill=(0, 0, 0), font=font_style)


    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 30)
    draw.text((65, 264), title, fill=(0, 0, 0), font=font_style)

    r, g, b, mask = rankPic.split()
    pic.paste(rankPic, (40, 320), mask)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 27)
    updatetime = time.localtime(os.path.getmtime(r"masterdata/realtime/musicDifficulties.json"))
    draw.text((50, pic.size[1] - 110), '※定数非官方 仅供参考娱乐 请勿当真', fill='#00CCBB', font=font_style)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 20)
    draw.text((50, pic.size[1] - 70), 'Generated by Unibot', fill='#00CCBB',
              font=font_style)
    
    if profile is not None:
        if server in rank_query_ban_servers and not profile.isNewData:
            draw = ImageDraw.Draw(pic)
            font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 25)
            updatetime = time.localtime(os.path.getmtime(f'{suite_uploader_path}{userid}.json'))
            draw.text((68, 20), '数据上传时间：' + time.strftime("%Y-%m-%d %H:%M:%S", updatetime),
                    fill=(100, 100, 100), font=font_style)
    
    if env != 'prod':
        pic.show()
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


def getPlayLevel(musicid, difficulty):
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        musicDifficulties = json.load(f)
    for diff in musicDifficulties:
        if musicid == diff['musicId'] and diff['musicDifficulty'] == difficulty:
            return diff['playLevel']


def svg_to_png(url, write_to, scale=1):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    # Initialize the Chrome webdriver and open the SVG file
    driver = webdriver.Chrome('chromedriver-win64/chromedriver.exe', options=options)
    svg_path_absolute = os.path.abspath(url)
    svg_path_windows = svg_path_absolute.replace("/", "\\")
    driver.get(f'file:///{svg_path_windows}')

    if scale == 1:
        width = driver.execute_script('return document.documentElement.scrollWidth')
        height = driver.execute_script('return document.documentElement.scrollHeight')
    else:
        driver.execute_script(f"document.getElementsByTagName('svg')[0].setAttribute('style', 'transform: scale({scale}); transform-origin: 0 0;')")
        width = int(driver.execute_script('return document.documentElement.scrollWidth') * scale) + 1
        height = int(driver.execute_script('return document.documentElement.scrollHeight') * scale) + 1
    # Set window size
    driver.set_window_size(width, height)

    # Take screenshot
    driver.save_screenshot(write_to)

    driver.quit()


def parse_chart_new(music_id, difficulty, theme, savepng=True, jacketdir=None, scale=1):
    jacketdir = jacketdir or '../../../../data/assets/sekai/assetbundle/resources/startapp/music/jacket/%s/%s.png'
    style_path = 'charts/white.css' if theme in ['svg', 'guess'] else f'charts/{theme}.css'
    
    with open(style_path, encoding='UTF-8') as f:
        style = f.read()

    score = pjsekai.scores.Score.open(
        f'data/assets/sekai/assetbundle/resources/startapp/music/music_score/{music_id:04d}_01/{difficulty}',
        encoding='UTF-8'
    )
    score.meta.difficulty = difficulty

    if theme == 'guess':
        rebase = pjsekai.scores.Rebase.load_from_dict(
                {
                "musicId": 0,
                "events": [
                    {
                        "bar": 0,
                        "bpm": score.events[1].bpm,
                    }
                ]
            }
        )
        score = rebase.rebase(score)
    else:
        try:
            with open(f'moesus/rebases/{music_id}.json', encoding='UTF-8') as f:
                rebase = pjsekai.scores.Rebase.load(f)
            score = rebase.rebase(score)
        except FileNotFoundError:
            pass
    

    try:
        with open(f'moesus/rebases/{music_id}.lyric', encoding='UTF-8') as f:
            lyric = pjsekai.scores.Lyric.load(f)
    except FileNotFoundError:
        lyric = None

    with open('masterdata/musics.json', 'r', encoding='UTF-8') as f:
        music_data = json.load(f)

    with open('masterdata/musicArtists.json', 'r', encoding='UTF-8') as f:
        music_artist_data = json.load(f)

    with open('masterdata/musicDifficulties.json', 'r', encoding='UTF-8') as f:
        music_difficulty_data = json.load(f)

    for i in music_data:
        if i['id'] == music_id:
            artist_id = i['creatorArtistId']
            score.meta.artist = next(j['name'] for j in music_artist_data if j['id'] == artist_id)
            score.meta.jacket = jacketdir % (i['assetbundleName'], i['assetbundleName'])
            score.meta.title = i['title']
            break

    for i in music_difficulty_data:
        if i['musicId'] == music_id and i['musicDifficulty'] == difficulty:
            score.meta.playlevel = str(i["playLevel"])
    
    drawing = pjsekai.scores.Drawing(score=score, lyric=lyric, style_sheet=style, note_host="../../notes_new/custom01")
    
    note_sizes = {
        'easy': 30,
        'normal': 25,
        'hard': 22,
        'expert': 19,
        'master': 18,
        'append': 18
    }
    drawing.note_size = note_sizes[difficulty]
    drawing.time_height = 240

    if score.meta.playlevel:
        if 30 < int(score.meta.playlevel) <= 33:
            drawing.time_height += (int(score.meta.playlevel) - 30) * 25
        elif int(score.meta.playlevel) > 33:
            drawing.time_height = 340

    file_name = f'charts/moe/{theme}/{music_id}/{difficulty}'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    drawing.svg().saveas(f'{file_name}.svg')

    if savepng:
        svg_to_png(url=f'{file_name}.svg', write_to=f'{file_name}.png', scale=scale)


def getchart(musicid, difficulty, theme='white'):
    if musicid == 131 and difficulty == 'append':
        musicid = 388  # 激唱append
    path = f'charts/moe/{theme}/{musicid}/{difficulty}.jpg'
    if os.path.exists(path):  # 本地有缓存
        return path
    else:  # 本地无缓存
        # 可能生成过没有music_meta的版本
        # if theme == 'skill' and os.path.exists(f'charts/moe/{theme}/{musicid}/{difficulty}_nometa.jpg'):
        #     with open('masterdata/realtime/music_metas.json', 'r', encoding='utf-8') as f:
        #         music_metas = json.load(f)
        #     for mm in music_metas:
        #         if mm['music_id'] == musicid and mm['difficulty'] == difficulty:
        #             break
        #     else:
        #         # 如果music_meta还是没有则返回之前的缓存
        #         return f'charts/moe/{theme}/{musicid}/{difficulty}_nometa.jpg'
        if not os.path.exists(path[:-3] + 'png'):
            parse_chart_new(musicid, difficulty, theme, scale=1.15 if theme != 'guess' else None)
        if theme != 'guess':
            # try:
            #     im = Image.open(path[:-3] + 'png')
            # except FileNotFoundError:
            #     im = Image.open(f'charts/moe/{theme}/{musicid}/{difficulty}_nometa.png')
            #     path = f'charts/moe/{theme}/{musicid}/{difficulty}_nometa.jpg'
            im = Image.open(path[:-3] + 'png')
            im = im.convert('RGB')
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
        for diff in ['master', 'expert', 'hard', 'normal', 'easy', 'append']:
            if not os.path.exists(f'charts/moe/svg/{music["id"]}/{diff}.svg'):
                try:
                    parse_chart_new(music['id'], diff, 'svg', False, 'https://assets.unipjsk.com/startapp/music/jacket/%s/%s.png')
                    print('已生成谱面', music['id'], diff)
                except FileNotFoundError:
                    pass
                except:
                    print('生成失败', music['id'], diff)
    

def autoGenGuess():
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for music in musics:
        if not os.path.exists(f'charts/moe/guess/{music["id"]}/master.svg'):
            try:
                parse_chart_new(music['id'], 'master', 'guess')
            except FileNotFoundError:
                pass


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
    full = full.strip().lower()
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
    elif full[-6:] == 'append':
        alias = full[:-6]
        diff = 'append'
    elif full[-2:] == 'ap':
        alias = full[:-2]
        diff = 'append'
    elif full[-3:] == 'apd':
        alias = full[:-3]
        diff = 'append'
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
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
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
    offset = 0
    timeformat = "%Y-%m-%dT%H:%M:%S.%f%z"
    deletelist = []
    failcount = 0
    while True:
        try:
            resp = requests.get(f'https://gitlab.com/pjsekai/rebases/-/refs/main/logs_tree/?format=json&offset={offset}', proxies=proxies)
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
            print('rebase下载失败')
            if failcount > 4:
                break
    updatecharts(deletelist)


def download_rebase(file_name):
    print('更新' + file_name)
    for i in range(0, 4):
        try:
            resp = requests.get(f'https://gitlab.com/pjsekai/rebases/-/raw/main/{file_name}?inline=false', proxies=proxies)
            with open('moesus/rebases/' + file_name, 'wb') as f:
                f.write(resp.content)
            return
        except:
            pass


def updatecharts(deletelist):
    for musicid in deletelist:
        for theme in ['black', 'white', 'color', 'svg']:
            for diff in ['easy', 'normal', 'hard', 'expert', 'master', 'append']:
                for fileformat in ['jpg', 'png', 'svg']:
                    path = f'charts/moe/{theme}/{musicid}/{diff}.{fileformat}'
                    if os.path.exists(path):
                        os.remove(path)
                        print('删除缓存' + path)
                            

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




