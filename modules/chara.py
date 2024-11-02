import ujson as json
import os
import random
import sqlite3
import time
from urllib.parse import quote
import pymysql
# from modules.getdata import LeakContent
# from modules.mysql_config import *
import aiohttp
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from modules.config import vitsapiurl, proxy, vitsvoiceurl, env
from modules.gacha import getcharaname
from modules.otherpics import cardthumnail
from modules.pjskinfo import isSingleEmoji, writelog
from modules.cardinfo import CardInfo
from modules.sk import recordname
from modules.texttoimg import texttoimg

botpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
charaalistxt = os.path.join(botpath, 'gamealias', 'chara.txt')


def getcardinfo(cardid, groupid: 0):
    savepath = f'piccache/cardinfo/cardinfo_{cardid}.jpg'
    if not os.path.exists(savepath):
        cardinfo = CardInfo()
        cardinfo.getinfo(cardid, groupid)
        pic = cardinfo.toimg(groupid)
        pic = pic.convert("RGB")
        pic.save(savepath, quality=85)
    return savepath


def cardidtopic(cardid):
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    assetbundleName = ''
    for card in allcards:
        if card['id'] == cardid:
            # if card["releaseAt"] / 1000 > time.time():
            #     raise LeakContent
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


# 用于创建 resourceBoxes 的索引
def create_resourcebox_index(resourceBoxes):
    index = {}
    for item in resourceBoxes:
        if item.get('resourceBoxPurpose') == 'gacha_ceil_exchange':
            for detail in item.get('details', []):
                if detail.get('resourceType') == 'card':
                    cardid = detail.get('resourceId')
                    index[cardid] = item.get('id')
    return index

# 用于创建 gachaCeilExchangeSummaries 的索引
def create_exchange_summary_index(gachaCeilExchangeSummaries):
    index = {}
    for item in gachaCeilExchangeSummaries:
        for exchange in item.get("gachaCeilExchanges", []):
            resourceBoxId = exchange.get("resourceBoxId")
            index[resourceBoxId] = exchange.get("gachaCeilExchangeLabelType")
    return index


def find_resourcebox_id_by_cardid(cardid, resourceBoxes=None):
    if resourceBoxes is None:
        with open('masterdata/resourceBoxes.json', 'r', encoding='utf-8') as f:
            resourceBoxes = json.load(f)
    for item in resourceBoxes:
        if item.get('resourceBoxPurpose') == 'gacha_ceil_exchange':
            for detail in item.get('details', []):
                if detail.get('resourceType') == 'card' and detail.get('resourceId') == cardid:
                    return item.get('id')
    return None


# 优化后的 cardtype 函数
def cardtype(cardid, resourcebox_index, exchange_summary_index):
    resourcebox_id = resourcebox_index.get(cardid)
    if resourcebox_id:
        label_type = exchange_summary_index.get(resourcebox_id)
        if label_type in ["limited", "fes"]:
            return label_type
    return False


def findcard(charaid, cardRarityType=None):
    # if os.path.exists(f"piccache/cardinfo/{charaid}{cardRarityType}.jpg") and env == 'prod':
    #     return f"cardinfo/{charaid}{cardRarityType}.jpg"
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    with open(f'masterdata/skills.json', 'r', encoding='utf-8') as f:
        skills = json.load(f)
    with open('masterdata/resourceBoxes.json', 'r', encoding='utf-8') as f:
        resourceBoxes = json.load(f)
    with open('masterdata/gachaCeilExchangeSummaries.json', 'r', encoding='utf-8') as f:
        gachaCeilExchangeSummaries = json.load(f)
    resourcebox_index = create_resourcebox_index(resourceBoxes)
    exchange_summary_index = create_exchange_summary_index(gachaCeilExchangeSummaries)
    current_time = time.time()
    allcards = [card for card in allcards if card["releaseAt"] / 1000 <= current_time]
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
            single = findcardsingle(card, allcards, skills, resourcebox_index, exchange_summary_index)
            pic.paste(single, pos)
    pic = pic.crop((0, 0, 1500, (int((count - 1) / 3) + 1) * 310 + 60))
    pic.save(f'piccache/cardinfo/{charaid}{cardRarityType}.jpg')
    # if env != 'prod':
    #     pic.show()
    return f'cardinfo/{charaid}{cardRarityType}.jpg'


def findcardsingle(card, allcards, skills, resourcebox_index, exchange_summary_index):
    pic = Image.new("RGB", (420, 260), (255, 255, 255))
    badge = cardtype(card['id'], resourcebox_index, exchange_summary_index)

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
    font = ImageFont.truetype(r'fonts/SourceHanSansCN-Medium.otf', 28)
    text_width = font.getsize(card["prefix"])

    if text_width[0] > 420:
        font = ImageFont.truetype(r'fonts/SourceHanSansCN-Medium.otf', int(28 / (text_width[0] / 420)))
        text_width = font.getsize(card["prefix"])

    text_coordinate = ((210 - text_width[0] / 2), int(195 - text_width[1] / 2))
    draw.text(text_coordinate, card["prefix"], '#000000', font)

    name = getcharaname(card['characterId'])
    font = ImageFont.truetype(r'fonts/SourceHanSansCN-Medium.otf', 18)
    text_width = font.getsize(f'id:{card["id"]}  {name}')
    text_coordinate = ((210 - text_width[0] / 2), int(230 - text_width[1] / 2))
    draw.text(text_coordinate, f'id:{card["id"]}  {name}', '#505050', font)

    for skill in skills:
        if skill['id'] == card['skillId']:
            descriptionSpriteName = skill['descriptionSpriteName']

    skillTypePic = Image.open(f'chara/skill_{descriptionSpriteName}.png')
    skillTypePic = skillTypePic.resize((40, 40))
    r, g, b, mask = skillTypePic.split()
    pic.paste(skillTypePic, (370, 210), mask)

    return pic

def charainfo(alias, qunnum=''):
    return ''

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
    return ''


def grcharadel(alias, qunnum=''):
    return ''


def aliastocharaid(alias, qunnum=''):
    with open(charaalistxt, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            rows = line.strip().split(':')
            if rows[0] == alias:
                return int(rows[1]), rows[0]
    return 0, 'unknown'


def charaset(newalias, oldalias, qqnum, username, qun, is_hide=False):
    return ''


def grcharaset(newalias, oldalias, qunnum, is_hide=False):
    return ''

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
    if True:  # random.randint(0, 1) == 1:
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
