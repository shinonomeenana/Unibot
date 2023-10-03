import ujson as json
import os
import random
import sqlite3
import time
import pymysql
from PIL import Image
from mutagen.mp3 import MP3
from pydub import AudioSegment

from modules.config import SEdir
from modules.mysql_config import *
from emoji2pic import Emoji2Pic
from modules.musics import isleak, getPlayLevel
from modules.texttoimg import texttoimg


def getrandomchartold():
    path = 'charts/SekaiViewer'
    target = []
    files = os.listdir(path)
    files_dir = [f for f in files if os.path.isdir(os.path.join(path, f))]
    for i in files_dir:
        chartfiles = os.listdir(path + "/" + i)
        files_file = [f for f in chartfiles if os.path.isfile(os.path.join(path + "/" + i, f))]
        if 'master.png' in files_file:
            target.append(i)
    # return f"{path}/{target[random.randint(0, len(target))]}/master.png"
    musicid = int(target[random.randint(0, len(target) - 1)])
    if isleak(musicid):
        print('leak重抽')
        return getrandomchart()
    else:
        return musicid

def guessRank(guessType, typeText, qqnum=None):
    from imageutils import text2image
    mydb = pymysql.connect(host=host, port=port, user='pjskguess', password=password,
                           database='pjskguess', charset='utf8mb4')
    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT * from `%s` order by count desc', (guessType,))
    data = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    count = 0
    text = typeText + ' TOP20\n'
    user_rank = None
    user_count = None
    top20_generated = False
    for raw in data:
        raw = raw[1:]
        count += 1
        name = raw[1]
        if len(name) > 20:
            name = name[:5] + '...' + name[-5:]
        if raw[0] == str(qqnum):
            user_rank = count
            user_count = raw[2]
        if count <= 20:
            if len(raw[0]) >= 15:
                if '#' in name:
                    text += f'{name}(Discord用户): {raw[2]}次\n'
                else:
                    text += f'{name}(频道用户): {raw[2]}次\n'
            else:
                text += f'{name}({raw[0][:3]}***{raw[0][-3:]}): {raw[2]}次\n'
            if count == 20:
                top20_generated = True
        if user_rank is not None and top20_generated:
            break
    if qqnum is not None and user_rank is not None:
        text += f'\n您的排名: {user_rank}位, 次数: {user_count}次'
    elif qqnum is not None:
        text += f'\n您的排名: 暂无排名'
    infopic = text2image(text=text, max_width=1000, padding=(30, 30))
    infopic.save(f'piccache/guess{guessType}{qqnum}.png')
    return f'piccache/guess{guessType}{qqnum}.png'


def recordGuessRank(qqnum, name, guessType):
    mydb = pymysql.connect(host=host, port=port, user='pjskguess', password=password,
                           database='pjskguess', charset='utf8mb4')
    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT * from `%s` where qqnum=%s', (guessType, qqnum))
    data = mycursor.fetchone()
    count = 0
    if data is not None:
        count = data[3]
        mycursor.execute(f'UPDATE `%s` SET name=%s, count=%s WHERE qqnum=%s', (guessType, name, count + 1, str(qqnum)))
    else:
        sql_add = f'insert into `%s` (qqnum, name, count) values(%s, %s, %s)'
        mycursor.execute(sql_add, (guessType, str(qqnum), name, count + 1))

    mydb.commit()
    mycursor.close()
    mydb.close()


def cutchartimgold(musicid, qunnum):
    img = Image.open(f'charts/SekaiViewer/{musicid}/master.png')
    # pic = pic.resize((160 * row + 32, 1300))
    row = int((img.size[0] - 32) / 160)
    rannum = random.randint(2, row - 1)
    img = img.crop((32 + 160 * (rannum - 1), 0, 32 + 160 * (rannum - 1) + 110, img.size[1]))
    img1 = img.crop((0, 0, 110, 650))
    img2 = img.crop((0, 650, 110, 1300))
    final = Image.new('RGB', (220, 640), (255, 255, 255))
    final.paste(img2, (0, 0))
    final.paste(img1, (110, -10))
    final.save(f'piccache/{qunnum}.png')

def getrandomchart():
    path = 'charts/moe/guess'
    target = []
    files = os.listdir(path)
    files_dir = [f for f in files if os.path.isdir(os.path.join(path, f))]
    for i in files_dir:
        chartfiles = os.listdir(path + "/" + i)
        files_file = [f for f in chartfiles if os.path.isfile(os.path.join(path + "/" + i, f))]
        if 'master.png' in files_file:
            target.append(i)
    # return f"{path}/{target[random.randint(0, len(target))]}/master.png"
    musicid = int(target[random.randint(0, len(target) - 1)])
    if isleak(musicid):
        print('leak重抽')
        return getrandomchart()
    else:
        return musicid


def cutchartimg(musicid, qunnum):
    img = Image.open(f'charts/moe/guess/{musicid}/master.png')
    
    row = round((img.size[0] - 80) / 272)
    print(row)
    rannum = random.randint(2, row - 1)
    img = img.crop((int(80 + 272 * (rannum - 1)), 32, int(80 + 272 * (rannum - 1) + 190), img.size[1] - 287))
    img1 = img.crop((0, 0, 190, int(img.size[1] / 2) + 20))
    img2 = img.crop((0, int(img.size[1] / 2) - 20, 190, img.size[1]))
    final = Image.new('RGB', (410, int(img.size[1] / 2) - 10), (255, 255, 255))
    final.paste(img2, (10, -7))
    final.paste(img1, (210, -20))
    # final.show()
    final.save(f'piccache/{qunnum}.png')


def getrandomjacket():
    path = 'data/assets/sekai/assetbundle/resources/startapp/music/jacket'
    target = []
    files = os.listdir(path)
    files_dir = [f for f in files if os.path.isdir(os.path.join(path, f))]
    for i in files_dir:
        target.append(i)
    # return f"{path}/{target[random.randint(0, len(target))]}/master.png"
    musicid = int(target[random.randint(0, len(target) - 1)][-3:])
    if isleak(musicid):
        print('leak重抽')
        return getrandomjacket()
    else:
        return musicid


def cutjacket(musicid, qunnum, size=140, isbw=False):
    img = Image.open('data/assets/sekai/assetbundle/resources'
                     f'/startapp/music/jacket/jacket_s_{str(musicid).zfill(3)}/jacket_s_{str(musicid).zfill(3)}.png')
    ran1 = random.randint(0, img.size[0] - size)
    ran2 = random.randint(0, img.size[1] - size)
    img = img.crop((ran1, ran2, ran1 + size, ran2 + size))
    if isbw:
        img = img.convert("L")
    img.save(f'piccache/{qunnum}.png')


def getrandomcard():
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        cardsdata = json.load(f)
    rannum = random.randint(0, len(cardsdata) - 1)
    while (cardsdata[rannum]['releaseAt'] > int(time.time() * 1000)
           or cardsdata[rannum]['cardRarityType'] == 'rarity_1'
           or cardsdata[rannum]['cardRarityType'] == 'rarity_2'):
        print('重抽')
        rannum = random.randint(0, len(cardsdata) - 1)
    return cardsdata[rannum]['characterId'], cardsdata[rannum]['assetbundleName'], cardsdata[rannum]['prefix'], cardsdata[rannum]['cardRarityType']


def cutcard(assetbundleName, cardRarityType, qunnum, size=250):
    istrained = False
    if cardRarityType == 'rarity_birthday':
        path = 'data/assets/sekai/assetbundle/resources/startapp/' \
               f'character/member/{assetbundleName}/card_normal.png'
    else:
        if random.randint(0, 1) == 1:
            path = 'data/assets/sekai/assetbundle/resources/startapp/' \
                   f'character/member/{assetbundleName}/card_after_training.png'
            istrained = True
        else:
            path = 'data/assets/sekai/assetbundle/resources/startapp/' \
                   f'character/member/{assetbundleName}/card_normal.png'
    print(path)
    img = Image.open(path)
    img = img.convert('RGB')
    if not os.path.exists(path[:-3] + 'jpg'):
        print('转jpg')
        img.save(path[:-3] + 'jpg', quality=95)
    ran1 = random.randint(0, img.size[0] - size)
    ran2 = random.randint(0, img.size[1] - size)
    img = img.crop((ran1, ran2, ran1 + size, ran2 + size))
    img.save(f'piccache/{qunnum}.png')
    return istrained

def defaultvocal(musicid):
    with open('masterdata/musicVocals.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    assetbundleName = ''
    for vocal in data:
        if vocal['musicId'] == musicid:
            if vocal['musicVocalType'] == 'sekai' or vocal['musicVocalType'] == 'instrumental':
                return vocal['assetbundleName']
            elif vocal['musicVocalType'] == 'original_song' or vocal['musicVocalType'] == 'virtual_singer':
                assetbundleName = vocal['assetbundleName']
    else: # 解包2dmv用 有的vocal对应的mvid不是musicid 如8001
        with open('masterdata/musicAssetVariants.json', 'r', encoding='utf-8') as f:
            musicAssetVariants = json.load(f)
        for variant in musicAssetVariants:
            if variant['musicAssetType'] == 'mv':
                if int(variant["assetbundleName"]) == musicid:
                    for vocal in data:
                        if vocal['id'] == variant["musicVocalId"]:
                            return vocal['assetbundleName']
    return assetbundleName


def getrandommusic():
    path = 'data/assets/sekai/assetbundle/resources/ondemand/music/long'
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    target = []
    for music in musics:
        if music['publishedAt'] < time.time() * 1000:
            target.append(music['id'])
    while True:
        musicid = target[random.randint(0, len(target) - 1)]
        assetbundleName = defaultvocal(musicid)
        if os.path.exists(f'{path}/{assetbundleName}/{assetbundleName}.mp3'):
            break
    return musicid, assetbundleName


def getRandomSE():
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    target = []
    for music in musics:
        if music['publishedAt'] < time.time() * 1000:
            target.append(music['id'])
    while True:
        musicid = target[random.randint(0, len(target) - 1)]
        if os.path.exists(f'{SEdir}{musicid}.mp3') and getPlayLevel(musicid, 'master') >= 29:
            break
    return musicid


def cutmusic(assetbundleName, qunnum, reverse=False):
    path = 'data/assets/sekai/assetbundle/resources/ondemand/music/long'
    musicpath = f'{path}/{assetbundleName}/{assetbundleName}.mp3'
    length = MP3(musicpath).info.length
    music = AudioSegment.from_mp3(musicpath)
    starttime = random.randint(20, int(length) - 10)
    if reverse:
        cut = music[starttime * 1000: starttime * 1000 + 5000]
        cut = cut.reverse()
    else:
        cut = music[starttime * 1000: starttime * 1000 + 1700]
    cut.export(f"piccache/{qunnum}.mp3",format="mp3")


def cutSE(musicid, qunnum):
    musicpath = f'{SEdir}{musicid}.mp3'
    length = MP3(musicpath).info.length
    se = AudioSegment.from_mp3(musicpath)
    starttime = random.randint(2, int(length) - 30)
    cut = se[starttime * 1000: starttime * 1000 + 20000]
    cut.export(f"piccache/{qunnum}.mp3", format="mp3", bitrate="96k")

    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for musicdata in musics:
        if musicdata['id'] == musicid:
            break
    path = 'data/assets/sekai/assetbundle/resources/ondemand/music/long'
    vocal = defaultvocal(musicid)
    musicpath = f'{path}/{vocal}/{vocal}.mp3'
    music = AudioSegment.from_mp3(musicpath).apply_gain(-3)
    cut2 = music[starttime * 1000 + musicdata['fillerSec'] * 1000: starttime * 1000 + 20000 + musicdata['fillerSec'] * 1000]
    mix = cut.overlay(cut2)
    mix.export(f"piccache/{qunnum}mix.mp3", format="mp3", bitrate="96k")


def get_two_lines(filename):
    """
    从文件中获取连续的两行，忽略空行。
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 2:
            return None
        line_num = random.randint(0, len(lines) - 2)
        return '\n'.join(lines[line_num:line_num+2])


def random_lyrics():
    """
    从 'musics.json' 中随机选择一首歌，并获取其歌词的两行。
    """
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    while True:
        item = random.choice(data)
        id = item.get('id')
        if os.path.exists(f'moesus/lyrics/{id}.txt'):
            lines = get_two_lines(f'moesus/lyrics/{id}.txt')
            if lines is not None:
                return id, lines