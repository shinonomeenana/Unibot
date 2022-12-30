import json
import os
import random
import sqlite3
import time
from urllib.parse import quote
import pymysql
from modules.mysql_config import *
import aiohttp
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from modules.config import vitsapiurl, proxy, vitsvoiceurl
from modules.gacha import getcharaname
from modules.otherpics import cardthumnail
from modules.pjskinfo import isSingleEmoji, writelog
from modules.cardinfo import CardInfo
from modules.texttoimg import texttoimg


def getcardinfo(cardid):
    savepath = f'piccache/cardinfo/cardinfo_{cardid}.jpg'
    if not os.path.exists(savepath):
        cardinfo = CardInfo()
        cardinfo.getinfo(cardid)
        pic = cardinfo.toimg()
        pic = pic.convert("RGB")
        pic.save(savepath, quality=85)
    return f'cardinfo_{cardid}.jpg'


def cardidtopic(cardid):
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    assetbundleName = ''
    for card in allcards:
        if card['id'] == cardid:
            assetbundleName = card['assetbundleName']
    if assetbundleName == '':
        return []
    path = 'data/assets/sekai/assetbundle/resources/startapp/character/member'
    path = path + "/" + assetbundleName
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    if not os.path.exists(path + '/card_normal.jpg'):  # 频道bot最多发送4MB 这里转jpg缩小大小
        im = Image.open(path + '/card_normal.png')
        im = im.convert('RGB')
        im.save(path + '/card_normal.jpg', quality=95)

    if 'card_after_training.png' in files_file:
        if not os.path.exists(path + '/card_after_training.jpg'):  # 频道bot最多发送4MB 这里转jpg缩小大小
            im = Image.open(path + '/card_after_training.png')
            im = im.convert('RGB')
            im.save(path + '/card_after_training.jpg', quality=95)
        return [path + '/card_normal.jpg', path + '/card_after_training.jpg']
    else:
        return [path + '/card_normal.jpg']

def cardtype(cardid, cardCostume3ds, costume3ds):
    # 普通0 限定1
    costume = []
    for i in cardCostume3ds:
        if i['cardId'] == cardid:
            costume.append(i['costume3dId'])
    for costumeid in costume:
        for model in costume3ds:
            if model['id'] == costumeid:
                if model['partType'] == 'hair':
                    return 1
    return 0

def findcard(charaid, cardRarityType=None):
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    with open(f'masterdata/cardCostume3ds.json', 'r', encoding='utf-8') as f:
        cardCostume3ds = json.load(f)
    with open(f'masterdata/costume3ds.json', 'r', encoding='utf-8') as f:
        costume3ds = json.load(f)
    allcards.sort(key=lambda x: x["releaseAt"], reverse=True)
    pic = Image.new('RGB', (1500, 5000), (235, 235, 235))
    count = 0
    for card in allcards:
        if card['characterId'] == charaid:
            if cardRarityType is not None:
                if card['cardRarityType'] != cardRarityType:
                    continue
            pos = (int(70 + count % 3 * 470), int(count / 3) * 310 + 60)
            count += 1
            single = findcardsingle(card, allcards, cardCostume3ds, costume3ds)
            pic.paste(single, pos)
    pic = pic.crop((0, 0, 1500, (int((count - 1) / 3) + 1) * 310 + 60))

    pic.save(f'piccache/{charaid}{cardRarityType}.jpg')
    return f'{charaid}{cardRarityType}.jpg'


def findcardsingle(card, allcards, cardCostume3ds, costume3ds):
    pic = Image.new("RGB", (420, 260), (255, 255, 255))
    badge = False
    cardtypenum = cardtype(card['id'], cardCostume3ds, costume3ds)
    if cardtypenum == 1 or card['cardRarityType'] == 'rarity_birthday':
        badge = True
    if card['cardRarityType'] == 'rarity_3' or card['cardRarityType'] == 'rarity_4':
        thumnail = cardthumnail(card['id'], istrained=False, cards=allcards, limitedbadge=badge)
        r, g, b, mask = thumnail.split()
        pic.paste(thumnail, (45, 15), mask)

        thumnail = cardthumnail(card['id'], istrained=True, cards=allcards, limitedbadge=badge)
        r, g, b, mask = thumnail.split()
        pic.paste(thumnail, (220, 15), mask)
    else:
        thumnail = cardthumnail(card['id'], istrained=False, cards=allcards, limitedbadge=badge)
        r, g, b, mask = thumnail.split()
        pic.paste(thumnail, (132, 15), mask)

    draw = ImageDraw.Draw(pic)
    font = ImageFont.truetype(r'fonts\SourceHanSansCN-Medium.otf', 28)
    text_width = font.getsize(f'{card["id"]}. {card["prefix"]}')
    text_coordinate = ((210 - text_width[0] / 2), int(195 - text_width[1] / 2))
    draw.text(text_coordinate, f'{card["id"]}. {card["prefix"]}', '#000000', font)

    name = getcharaname(card['characterId'])
    font = ImageFont.truetype(r'fonts\SourceHanSansCN-Medium.otf', 18)
    text_width = font.getsize(name)
    text_coordinate = ((210 - text_width[0] / 2), int(230 - text_width[1] / 2))
    draw.text(text_coordinate, name, '#505050', font)

    return pic

def charainfo(alias, qunnum=''):
    resp = aliastocharaid(alias, qunnum)
    qunalias = ''
    allalias = ''
    if resp[0] == 0:
        return "找不到你说的角色哦"
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * from qunalias where charaid=%s AND qunnum=%s", (resp[0], qunnum))
    data = mycursor.fetchall()
    for row in data:
        qunalias = qunalias + row[2] + "，"

    mycursor.execute("SELECT * from charaalias where charaid=%s", (resp[0],))
    data = mycursor.fetchall()
    for row in data:
        allalias = allalias + row[1] + "，"

    mycursor.close()
    mydb.close()
    return f"{resp[1]}\n全群昵称：{allalias[:-1]}\n本群昵称：{qunalias[:-1]}"

async def getvits(chara, word):
    # 因为某些库Window水土不服装不了所以弄成api部署在linux上了
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{vitsapiurl}gen?word={word}&chara={chara}', proxy=f'http://{proxy}') as r:
            result = await r.text()
    if 'playSounds' in result:
        return True, vitsvoiceurl + quote(result.replace('playSounds/', ''), 'utf-8')
    else:
        return False, result

def charadel(alias, qqnum, username, qun):
    resp = aliastocharaid(alias)
    if resp[0] == 0:
        return "找不到你说的角色哦，如删除仅本群可用昵称请使用grcharadel"
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute("DELETE from charaalias where alias=%s", (alias,))
    mydb.commit()
    mycursor.close()
    mydb.close()
    timeArray = time.localtime(time.time())
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    if str(qqnum) == '1103479519':
        writelog(f'[{Time}] 管理员删除了{resp[1]}的昵称:{alias}')
        return "删除成功！"
    writelog(f'[{Time}] {qun} {username}({qqnum}): 删除了{resp[1]}的昵称:{alias}')
    return "删除成功！\n已记录bot文档中公开的实时日志，乱删将被拉黑"


def grcharadel(alias, qunnum=''):
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    count = mycursor.execute("DELETE from qunalias where alias=%s AND qunnum=%s", (alias, qunnum))
    mydb.commit()
    mycursor.close()
    mydb.close()
    if count == 0:
        return "找不到你说的角色哦，如删除全群可用昵称请使用charadel"
    else:
        return "删除成功！"


def aliastocharaid(alias, qunnum=''):
    charaid = 0
    name = ''
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * from qunalias where alias=%s AND qunnum=%s", (alias, qunnum))
    raw = mycursor.fetchone()
    if raw is not None:
        charaid = raw[3]
        name = getcharaname(charaid)
    else:
        mycursor.execute("SELECT * from charaalias where alias=%s", (alias,))
        raw = mycursor.fetchone()
        if raw is not None:
            charaid = raw[2]
            name = getcharaname(charaid)

    mycursor.close()
    mydb.close()
    return charaid, name


def charaset(newalias, oldalias, qqnum, username, qun):
    if isSingleEmoji(newalias):
        return "由于数据库排序规则原因，不支持单个emoji字符作为歌曲昵称"
    resp = aliastocharaid(oldalias)
    print(resp)
    if resp[0] == 0:
        return "找不到你说的角色哦，如删除仅本群可用昵称请使用grcharadel"
    charaid = resp[0]

    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    sql = f"insert into charaalias(ALIAS,CHARAID) values (%s, %s) " \
          f"on duplicate key update charaid=%s"
    val = (newalias, charaid, charaid)
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    mydb.close()

    timeArray = time.localtime(time.time())
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    writelog(f'[{Time}] {qun} {username}({qqnum}): {newalias}->{resp[1]}')
    return f"设置成功！(全群可用)\n{newalias}->{resp[1]}\n已记录bot文档中公开的实时日志，如全群昵称添加不相关/不友好/无关联的首字母拼词等请立刻删除，否则一旦发现立刻拉黑\n可用grcharaset设置仅当前群可用的昵称）"


def grcharaset(newalias, oldalias, qunnum):
    if isSingleEmoji(newalias):
        return "由于数据库排序规则原因，不支持单个emoji字符作为歌曲昵称"
    resp = aliastocharaid(oldalias)
    if resp[0] == 0:
        return "找不到你说的角色哦，如删除仅本群可用昵称请使用grcharadel"
    charaid = resp[0]
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    sql = f"insert into qunalias(QUNNUM,ALIAS,CHARAID) values(%s, %s, %s) " \
          f"on duplicate key update charaid=%s"
    val = (str(qunnum), newalias, charaid, charaid)
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    mydb.close()
    return f"设置成功！(仅本群可用)\n{newalias}->{resp[1]}"

def get_card(charaid):
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    cardsdata = []
    for i in allcards:
        if i['characterId'] == charaid:
            cardsdata.append({
                'prefix': i['prefix'],
                'assetbundleName': i['assetbundleName'],
                'releaseAt': i['releaseAt'],
            })
    rannum = random.randint(0, len(cardsdata) - 1)
    while cardsdata[rannum]['releaseAt'] > int(time.time() * 1000):
        print(cardsdata[rannum]['prefix'], '重抽')
        rannum = random.randint(0, len(cardsdata) - 1)
    if random.randint(0, 1) == 1:
        path = 'data/assets/sekai/assetbundle/resources/startapp/character/member'
        path = path + "/" + cardsdata[rannum]['assetbundleName']
        files = os.listdir(path)
        files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
        if 'card_after_training.png' in files_file:
            if random.randint(0, 1) == 1:
                path = path + '/card_after_training.png'
            else:
                path = path + '/card_normal.png'
        else:
            path = path + '/card_normal.png'
        if not os.path.exists(path[:-3] + 'jpg'):  # 频道bot最多发送4MB 这里转jpg缩小大小
            im = Image.open(path)
            im = im.convert('RGB')
            im.save(path[:-3] + 'jpg', quality=95)
    else:
        path = 'data/assets/sekai/assetbundle/resources/startapp/character/member_cutout_trm'
        path = path + "/" + cardsdata[rannum]['assetbundleName']
        files = os.listdir(path)
        files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
        if 'after_training.png' in files_file:
            if random.randint(0, 1) == 1:
                path = path + '/after_training.png'
            else:
                path = path + '/normal.png'
        else:
            path = path + '/normal.png'
    return path
