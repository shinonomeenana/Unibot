import datetime
import ujson as json
import os
from os import path
import time
import pytz
from PIL import Image, ImageFont, ImageDraw
from modules.config import env
from modules.sk import currentevent

botpath = os.path.abspath(os.path.join(path.dirname(__file__), ".."))
assetpath = botpath + '/data/assets/sekai/assetbundle/resources'
class event(object):

    def __init__(self):
        self.id = 0
        self.eventType = ''
        self.name = ''
        self.assetbundleName = ''
        self.startAt = ''
        self.aggregateAtorin = 0
        self.aggregateAt = ''
        self.unit = ''
        self.bonusechara = []
        self.bonuseattr = ''
        self.music = 0
        self.cards = []

    def getevent(self, eventid):
        masterdatadir = path.join(botpath, 'masterdata/')
        with open(masterdatadir + 'events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(masterdatadir + 'eventCards.json', 'r', encoding='utf-8') as f:
            eventCards = json.load(f)
        with open(masterdatadir + 'eventDeckBonuses.json', 'r', encoding='utf-8') as f:
            eventDeckBonuses = json.load(f)
        for events in data:
            if eventid == events['id']:
                self.id = events['id']
                self.eventType = events['eventType']
                self.name = events['name']
                self.assetbundleName = events['assetbundleName']
                self.startAt = datetime.datetime.fromtimestamp(events['startAt'] / 1000,
                                                    pytz.timezone('Asia/Shanghai')).strftime('%Y/%m/%d %H:%M:%S')
                self.aggregateAtorin = events['aggregateAt']
                self.aggregateAt = datetime.datetime.fromtimestamp(events['aggregateAt'] / 1000 + 1,
                                                    pytz.timezone('Asia/Shanghai')).strftime('%Y/%m/%d %H:%M:%S')
                try:
                    self.unit = events['unit']
                except:
                    pass
                break
        if self.id == 0:
            return False
        for cards in eventCards:
            if cards['eventId'] == self.id:
                self.cards.append(cards['cardId'])
        for bonuse in eventDeckBonuses:
            if bonuse['eventId'] == self.id:
                try:
                    self.bonuseattr = bonuse['cardAttr']
                    self.bonusechara.append(bonuse['gameCharacterUnitId'])
                except:
                    pass
        return True


def analysisunitid(unitid, gameCharacterUnits=None):
    if gameCharacterUnits is None:
        masterdatadir = path.join(botpath, 'masterdata/')
        with open(masterdatadir + 'gameCharacterUnits.json', 'r', encoding='utf-8') as f:
            gameCharacterUnits = json.load(f)
    for units in gameCharacterUnits:
        if units['id'] == unitid:
            if unitid <= 20:
                return unitid, units['unit'], f'chr_ts_90_{unitid}.png'
            elif units['gameCharacterId'] == 21:
                if unitid != 21:
                    return 21, units['unit'], f'chr_ts_90_21_{unitid - 25}.png'
                else:
                    return 21, 'piapro', f'chr_ts_90_21.png'
            else:
                return units['gameCharacterId'], units['unit'], f'chr_ts_90_{units["gameCharacterId"]}_2.png'


def cardthumnail(cardid, istrained=False, cards=None, limitedbadge=False):
    if cards is None:
        masterdatadir = path.join(botpath, 'masterdata/')
        with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
            cards = json.load(f)
    if istrained:
        suffix = 'after_training'
    else:
        suffix = 'normal'
    for card in cards:
        if card['id'] == cardid:
            if card['cardRarityType'] != 'rarity_3' and card['cardRarityType'] != 'rarity_4':
                suffix = 'normal'
            pic = Image.open(f'{assetpath}/startapp/thumbnail/chara/{card["assetbundleName"]}_{suffix}.png')
            pic = pic.resize((156, 156))
            cardFrame = Image.open(f'{botpath}/chara/cardFrame_{card["cardRarityType"]}.png')
            r, g, b, mask = cardFrame.split()
            pic.paste(cardFrame, (0, 0), mask)
            if card['cardRarityType'] == 'rarity_1':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((28, 28))
                r, g, b, mask = star.split()
                pic.paste(star, (10, 118), mask)
            if card['cardRarityType'] == 'rarity_2':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((28, 28))
                r, g, b, mask = star.split()
                pic.paste(star, (10, 118), mask)
                pic.paste(star, (36, 118), mask)
            if card['cardRarityType'] == 'rarity_3':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((28, 28))
                r, g, b, mask = star.split()
                pic.paste(star, (10, 118), mask)
                pic.paste(star, (36, 118), mask)
                pic.paste(star, (62, 118), mask)
            if card['cardRarityType'] == 'rarity_4':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((28, 28))
                r, g, b, mask = star.split()
                pic.paste(star, (10, 118), mask)
                pic.paste(star, (36, 118), mask)
                pic.paste(star, (62, 118), mask)
                pic.paste(star, (88, 118), mask)
            if card['cardRarityType'] == 'rarity_birthday':
                star = Image.open(f'{botpath}/chara/rarity_birthday.png')
                star = star.resize((28, 28))
                r, g, b, mask = star.split()
                pic.paste(star, (10, 118), mask)
            attr = Image.open(f'{botpath}/chara/icon_attribute_{card["attr"]}.png')
            attr = attr.resize((35, 35))
            r, g, b, mask = attr.split()
            pic.paste(attr, (1, 1), mask)
            if limitedbadge:
                badge = Image.open(f'{botpath}/pics/badge_{limitedbadge}.png')
                # attr = attr.resize((35, 35))
                r, g, b, mask = badge.split()
                pic.paste(badge, (43, 0), mask)

            return pic


def cardlarge(cardid, istrained=False, cards=None):
    if cards is None:
        masterdatadir = path.join(botpath, 'masterdata/')
        with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
            cards = json.load(f)
    if istrained:
        suffix = 'after_training'
    else:
        suffix = 'normal'
    for card in cards:
        if card['id'] == cardid:
            if card['cardRarityType'] != 'rarity_3' and card['cardRarityType'] != 'rarity_4':
                suffix = 'normal'
            pic = Image.open(f'{assetpath}/startapp/character/member/{card["assetbundleName"]}/card_{suffix}.png')
            pic = pic.resize((1024, 576))
            cardFrame = Image.open(f'{botpath}/chara/cardFrame_L_{card["cardRarityType"]}.png')
            r, g, b, mask = cardFrame.split()
            pic.paste(cardFrame, (0, 0), mask)
            if card['cardRarityType'] == 'rarity_1':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((72, 70))
                r, g, b, mask = star.split()
                pic.paste(star, (16, 490), mask)
            if card['cardRarityType'] == 'rarity_2':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((72, 70))
                r, g, b, mask = star.split()
                pic.paste(star, (16, 428), mask)
                pic.paste(star, (16, 490), mask)
            if card['cardRarityType'] == 'rarity_3':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((72, 70))
                r, g, b, mask = star.split()
                pic.paste(star, (16, 366), mask)
                pic.paste(star, (16, 428), mask)
                pic.paste(star, (16, 490), mask)
            if card['cardRarityType'] == 'rarity_4':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((72, 70))
                r, g, b, mask = star.split()
                pic.paste(star, (16, 304), mask)
                pic.paste(star, (16, 366), mask)
                pic.paste(star, (16, 428), mask)
                pic.paste(star, (16, 490), mask)
            if card['cardRarityType'] == 'rarity_birthday':
                star = Image.open(f'{botpath}/chara/rarity_birthday.png')
                star = star.resize((72, 70))
                r, g, b, mask = star.split()
                pic.paste(star, (16, 490), mask)
            attr = Image.open(f'{botpath}/chara/icon_attribute_{card["attr"]}.png')
            attr = attr.resize((88, 88))
            r, g, b, mask = attr.split()
            pic.paste(attr, (924, 12), mask)
            return pic


def gachacardthumnail(cardid, istrained=False, cards=None):
    if cards is None:
        masterdatadir = path.join(botpath, 'masterdata/')
        with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
            cards = json.load(f)
    if istrained:
        suffix = 'after_training'
    else:
        suffix = 'normal'
    for card in cards:
        if card['id'] == cardid:
            if card['cardRarityType'] != 'rarity_3' and card['cardRarityType'] != 'rarity_4':
                suffix = 'normal'
            pic = Image.new('RGBA', (338, 338), (0, 0, 0, 0))
            cardpic = Image.open(f'{assetpath}/startapp/character/member_cutout/{card["assetbundleName"]}/{suffix}.png')
            picmask = Image.open(f'{botpath}/pics/gachacardmask.png')
            r, g, b, mask = picmask.split()
            pic.paste(cardpic, (0, 0), mask)
            cardFrame = Image.open(f'{botpath}/chara/cardFrame_{card["cardRarityType"]}.png')
            cardFrame = cardFrame.resize((338, 338))
            r, g, b, mask = cardFrame.split()

            pic.paste(cardFrame, (0, 0), mask)
            if card['cardRarityType'] == 'rarity_1':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((61, 61))
                r, g, b, mask = star.split()
                pic.paste(star, (21, 256), mask)
            if card['cardRarityType'] == 'rarity_2':
                star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((60, 60))
                r, g, b, mask = star.split()
                pic.paste(star, (21, 256), mask)
                pic.paste(star, (78, 256), mask)
            if card['cardRarityType'] == 'rarity_3':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((60, 60))
                r, g, b, mask = star.split()
                pic.paste(star, (21, 256), mask)
                pic.paste(star, (78, 256), mask)
                pic.paste(star, (134, 256), mask)
            if card['cardRarityType'] == 'rarity_4':
                if istrained:
                    star = Image.open(f'{botpath}/chara/rarity_star_afterTraining.png')
                else:
                    star = Image.open(f'{botpath}/chara/rarity_star_normal.png')
                star = star.resize((60, 60))
                r, g, b, mask = star.split()
                pic.paste(star, (21, 256), mask)
                pic.paste(star, (78, 256), mask)
                pic.paste(star, (134, 256), mask)
                pic.paste(star, (190, 256), mask)
            if card['cardRarityType'] == 'rarity_birthday':
                star = Image.open(f'{botpath}/chara/rarity_birthday.png')
                star = star.resize((60, 60))
                r, g, b, mask = star.split()
                pic.paste(star, (21, 256), mask)
            attr = Image.open(f'{botpath}/chara/icon_attribute_{card["attr"]}.png')
            attr = attr.resize((76, 76))
            r, g, b, mask = attr.split()
            pic.paste(attr, (1, 1), mask)
            return pic


def charabonuspic(unitid, attr, cards, gameCharacterUnits, endtime):
    charaid, unit, charapicname = analysisunitid(unitid, gameCharacterUnits)
    img = Image.new('RGBA', (2500, 125), color=(0, 0, 0, 0))

    charapic = Image.open(f'{botpath}/chara/{charapicname}')
    charapic = charapic.resize((80, 80))
    r, g, b, mask = charapic.split()
    img.paste(charapic, (0, 0), mask)

    attrpic = Image.open(f'{botpath}/chara/icon_attribute_{attr}.png')
    attrpic = attrpic.resize((80, 80))
    r, g, b, mask = attrpic.split()
    img.paste(attrpic, (84, 0), mask)
    count = 0
    pos = 172
    for card in cards:
        if card['characterId'] == charaid and card['attr'] == attr and ((card['supportUnit'] == unit) if card['supportUnit'] != 'none' else True) and card['releaseAt'] < endtime:
            count += 1
            cardpic = cardthumnail(card['id'], True, cards)
            cardpic = cardpic.resize((125, 125))
            r, g, b, mask = cardpic.split()
            img.paste(cardpic, (pos, 0), mask)
            pos += 130
    if count == 0:
        return None
    img = img.crop((0, 0, pos, 125))
    return img


def resize_and_center(image, target_width, target_height):
    img_width, img_height = image.size
    
    # 计算缩放比例
    scale = max(target_width / img_width, target_height / img_height)
    
    # 计算新的尺寸
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    
    # 缩放图片
    image = image.resize((new_width, new_height), Image.ANTIALIAS)
    
    # 计算裁剪位置
    left_margin = (new_width - target_width) / 2
    top_margin = (new_height - target_height) / 2
    right_margin = left_margin + target_width
    bottom_margin = top_margin + target_height
    
    # 裁剪图片
    image = image.crop((left_margin, top_margin, right_margin, bottom_margin))
    
    return image


def drawevent(event):
    pic = Image.open(f'{assetpath}/ondemand/event_story/{event.assetbundleName}/screen_image/story_bg.png')
    chara = Image.open(f'{assetpath}/ondemand/event/{event.assetbundleName}/screen/character.png')
    pic = resize_and_center(pic, 2048, 1261)
    r, g, b, mask = chara.split()
    pic.paste(chara, ((1100 - chara.width) if chara.width > 1200 else (900 - chara.width), pic.height - chara.height), mask)
    logo = Image.open(f'{assetpath}/ondemand/event/{event.assetbundleName}/logo/logo.png')
    r, g, b, mask = logo.split()
    pic.paste(logo, (50, 800), mask)
    if event.unit != 'none':
        unit = Image.open(f'{botpath}/pics/logo_{event.unit}.png')
        r, g, b, mask = unit.split()
        pic.paste(unit, (50, 50), mask)
    words = Image.open(f'{botpath}/pics/event.png')
    r, g, b, mask = words.split()
    pic.paste(words, (0, 0), mask)
    draw = ImageDraw.Draw(pic)
    font_style = ImageFont.truetype(f"{botpath}/fonts/SourceHanSansCN-Medium.otf", 34)
    draw.text((294, 1090), event.startAt, fill=(255, 255, 255), font=font_style)
    draw.text((294, 1174), event.aggregateAt, fill=(255, 255, 255), font=font_style)
    pos = [763, 138]
    masterdatadir = path.join(botpath, 'masterdata/')
    with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    for card in event.cards:
        cardimg = cardthumnail(card, True, cards)
        cardimg = cardimg.resize((125, 125))
        r, g, b, mask = cardimg.split()
        pic.paste(cardimg, (pos[0], pos[1]), mask)
        pos[0] += 130
    # if event.music != 0:
    #     jacket = Image.open(f'{assetpath}/startapp/thumbnail/music_jacket/jacket_s_{str(event.music).zfill(3)}.png')
    #     jacket = jacket.resize((145, 145))
    #     pic.paste(jacket, (1560, 147))
    #     font_style = ImageFont.truetype(f"{botpath}/fonts/SourceHanSansCN-Medium.otf", 20)
    #     draw.text((760, 147), info.title, fill=(0, 0, 0), font=font_style)
    with open(masterdatadir + 'gameCharacterUnits.json', 'r', encoding='utf-8') as f:
        gameCharacterUnits = json.load(f)
    bonuspics = []  # 临时保存加成角色卡图
    base_pos = (750, 380)  # 加成图粘贴的基准位置
    max_width = 1980 - base_pos[0]  # 加成图最大宽度
    max_height = 1210 - base_pos[1]  # 加成图最大高度
    offest_size = [0, 0]  # 每张角色各自的加成图的偏移位置
    # 获取各角色加成图以及应该粘贴的位置
    for chara in event.bonusechara:
        bonuspic = charabonuspic(chara, event.bonuseattr, cards, gameCharacterUnits, event.aggregateAtorin)
        if bonuspic is not None:
            # 检查并调整过宽的bonuspic
            if bonuspic.size[0] > max_width:
                scale_factor = max_width / bonuspic.size[0]
                new_height = int(bonuspic.size[1] * scale_factor)
                bonuspic = bonuspic.resize((max_width, new_height))
            if offest_size[0] + bonuspic.size[0] > max_width:
                offest_size[0] = 0
                offest_size[1] += bonuspic.size[1] + 15
            bonuspics.append((bonuspic, offest_size[0], offest_size[1]))
            offest_size[0] += bonuspic.size[0] + 55
    # 生成合适大小的角色加成图
    final_bonuspic = Image.new("RGBA", (max_width, offest_size[1] + bonuspics[-1][0].size[1]))
    for bonuspic, x, y in bonuspics:
        mask = bonuspic.split()[-1]
        final_bonuspic.paste(bonuspic, (x, y), mask)
    # 角色加成图过大时自动缩放
    if final_bonuspic.size[1] > max_height:
        newsize = (int(final_bonuspic.size[0] / final_bonuspic.size[1] * max_height), max_height)
        final_bonuspic = final_bonuspic.resize(newsize)
    # 在背景上粘贴角色加成图
    mask = final_bonuspic.split()[-1]
    pic.paste(final_bonuspic, base_pos, mask)
    if env != "prod":
        pic.show()
    pic = pic.convert('RGB')
    pic.save(f'{botpath}/piccache/event/{event.id}.jpg')

def gachapic(charas, filename):
    pic = Image.open(f'{botpath}/pics/gacha.png')
    masterdatadir = path.join(botpath, 'masterdata/')
    with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    cover = Image.new('RGB', (1550, 600), (255, 255, 255))
    pic.paste(cover, (314, 500))
    for i in range(0, 5):
        cardpic = gachacardthumnail(charas[i], False, cards)
        cardpic = cardpic.resize((263, 263))
        r, g, b, mask = cardpic.split()
        pic.paste(cardpic, (336 + 304 * i, 520), mask)
    for i in range(0, 5):
        cardpic = gachacardthumnail(charas[i+5], False, cards)
        cardpic = cardpic.resize((263, 263))
        r, g, b, mask = cardpic.split()
        pic.paste(cardpic, (336 + 304 * i, 825), mask)
    pic = pic.convert('RGB')
    pic.save(f'{botpath}/piccache/{filename}.jpg')

def geteventpic(eventid=None):
    if eventid is None:
        eventid = currentevent('jp')['id']
    if os.path.exists(f'{botpath}/piccache/event/{eventid}.jpg'):
        return f'piccache/event/{eventid}.jpg'
    eventinfo = event()
    if eventinfo.getevent(eventid):
        drawevent(eventinfo)
        return f'piccache/event/{eventid}.jpg'
    else:
        return False


if __name__ == '__main__':
    gachapic([30, 66, 138, 86, 123, 201, 159, 334, 201, 158], '123')
    # cardthumnail(487, True)
    # event = event()
    # print(event.getevent(88))
    # drawevent(event)
    # print(event.cards)