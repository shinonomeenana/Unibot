import os
import pytz
import json
import datetime
from hashlib import md5
from PIL import ImageFont, Image, ImageDraw
from typing import Optional, Dict, List, Tuple, Union
from modules.chara import aliastocharaid
from modules.otherpics import analysisunitid, cardthumnail
from modules.texttoimg import union


botpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
assetpath = botpath + '/data/assets/sekai/assetbundle/resources'
masterdatadir = os.path.join(botpath, 'masterdata/')


def findevent(msg: str = '') -> str:
    """
    查询活动，返回图片路径
    :param msg: 用户所发送的消息
    """
    args = msg.strip().split()
    event_type = 'all'
    event_attr = 'all'
    event_charas_id = []
    # 解析[关键字]参数
    for i in args:
        # 是否为活动类型
        if _ := {
            '普活': 'marathon', '马拉松': 'marathon', 'marathon': 'marathon',
            '5v5': 'cheerful_carnival', 'cheerful_carnival': 'cheerful_carnival'
        }.get(i):
            event_type = _
        # 是否为活动属性
        elif _ := {
            '蓝星':'cool', '紫月':'mysterious', '橙心':'happy', '粉花':'cute', '绿草':'pure',
            '蓝': 'cool', '紫': 'mysterious', '橙': 'happy', '粉': 'cute', '绿': 'pure',
            '星': 'cool', '月': 'mysterious', '心': 'happy', '花': 'cute', '草': 'pure',
            'cool': 'cool', 'mysterious': 'mysterious', 'happy': 'happy', 'cute': 'cute', 'pure': 'pure',
        }.get(i):
            event_attr = _
        # 是否为组合（并不包含vs角色）
        elif _ := {
            'ln': [1,2,3,4], 'mmj': [5,6,7,8],'vbs': [9,10,11,12],'ws': [13,14,15,16],'25': [17,18,19,20],
        }.get(i):
            event_charas_id.extend(_)
        # 是否为角色
        else:
            # 是否是带附属组合的vs角色
            for unit in ['ln','mmj','vbs','ws','25']:
                if i.startswith(unit):
                    unit_dict = {
                        'ln': 'light_sound', 'mmj': 'idol', 'vbs': 'street', 'ws': 'theme_park', '25': 'school_refusal'
                    }
                    chara_dict = {'miku':21,'rin':22,'len':23,'luka':24,'meiko':25,'kaito':26}
                    charaid = chara_dict.get(i[len(unit):])
                    if not charaid:
                        charaid = aliastocharaid(i[len(unit):])[0]
                    if charaid != 0:
                        event_charas_id.append((charaid,unit_dict[unit]))
                        break
            # sekai角色、无附属组合的vs角色
            else:
                chara_dict = {
                    'ick': 1, 'saki': 2, 'hnm': 3, 'shiho': 4,
                    'mnr': 5, 'hrk': 6, 'airi': 7, 'szk': 8,
                    'khn': 9, 'an': 10, 'akt': 11, 'toya': 12,
                    'tks': 13, 'emu': 14, 'nene': 15, 'rui': 16,
                    'knd': 17, 'mfy': 18, 'ena': 19, 'mzk': 20,
                    'miku': 21, 'rin': 22, 'len': 23, 'luka': 24, 'meiko': 25, 'kaito': 26
                }
                charaid = chara_dict.get(i)
                if not charaid:
                    charaid = aliastocharaid(i)[0]
                if charaid != 0:
                    event_charas_id.append(charaid)
    # 当用户发送文本带有[关键字]但关键字不合规范时，返回提示图
    if args and event_type == 'all' and event_attr == 'all' and not event_charas_id:
        tip_path = f"{botpath}/pics/findevent_tips.jpg"
        return tip_path
    # 检查本地活动图鉴是否需要更新
    with open(masterdatadir + 'events.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
    count = len(events)
    # 变化图片路径格式
    charas_id_name = event_charas_id.copy()
    for i in range(len(event_charas_id)):
        if isinstance(event_charas_id[i], tuple):
            charaid = event_charas_id[i][0] + ([
                 'light_sound','idol','street','theme_park','school_refusal'
            ].index(event_charas_id[i][1])+1)*6
            charas_id_name[i] = charaid
    charas_id_name.sort()
    save_file_prefix = md5(f'{event_type}{event_attr}{charas_id_name}'.encode()).hexdigest()
    save_path = f'piccache/findevent/{save_file_prefix}-{count}.jpg'
    # 图片存在缓存，直接发送
    if os.path.exists(save_path):
        return save_path
    # 需要生成新活动图鉴
    else:
        # 因为需要更新，所以清除所有旧活动图鉴
        for file in os.listdir(f'piccache/findevent'):
            if not file.split('.')[0].endswith(str(count)):
                os.remove(f'piccache/findevent/{file}')

        # 活动出卡是否需要包含所有角色id
        isContainAllCharasId = True
        # 生成图片
        pic = drawEventHandbook(event_type, event_attr, event_charas_id, isContainAllCharasId, events)
        if pic:
            pic = pic.convert('RGB')
            pic.save(save_path, quality=70)
            return save_path
        else:
            tip_path = f"{botpath}/pics/findevent_tips.jpg"
            return tip_path


def drawEventHandbook(
    event_type: str = 'all',
    event_attr: str = 'all',
    event_charas_id: Optional[List[Union[int, Tuple[int, str]]]] = None,
    isContainAllCharasId: bool = False,
    events: Optional[Dict] = None
):
    """
    生成活动图鉴
    :param event_type: 筛选的活动类型
    :param event_attr: 筛选的活动属性
    :param event_charas_id: 筛选的活动出卡角色
    :param isContainAllCharasId: 筛选的活动出卡是否需要包含所有角色id，针对event_charas_id参数
    :param events: events.json
    """
    # 先统一载入所有需要的文件数据
    if events is None:
        with open(masterdatadir + 'events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)
    with open(masterdatadir + 'eventCards.json', 'r', encoding='utf-8') as f:
        eventCards = json.load(f)
    with open(masterdatadir + 'eventDeckBonuses.json', 'r', encoding='utf-8') as f:
        eventDeckBonuses = json.load(f)
    with open(masterdatadir + 'gameCharacterUnits.json', 'r', encoding='utf-8') as f:
        game_character_units = json.load(f)
    with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
        allcards = json.load(f)
    font30 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=30)
    font20 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=20)
    font10 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=10)
    # 筛选：指定活动图鉴显示的活动类型
    if event_type != 'all':
        events = filter(lambda x: x['eventType'] == event_type, events)
    limit_count = 10  # 单列活动缩略图的个数
    event_size = (835, 230)  # 每张活动图的尺寸
    event_interval = 20  # 每张活动图的行间距
    event_pad = (40, 20, 25, 25)  # 每张活动图的pad
    handbook_interval = 50  # 每列活动概要的列间距
    handbook_pad = (180, 180, 50, 50)  # 整张活动概要的pad
    light_grey = '#dbdbdb'
    dark_grey = '#929292'
    col_event_imgs = []     # 存放每列活动概要
    _tmp_event_imgs = []
    for each in events:
        # ********************************获取活动信息******************************** #
        # 获取活动出卡情况
        event_cards = [i['cardId'] for i in filter(lambda x:x['eventId'] == each['id'], eventCards)]
        # 筛选：指定活动图鉴显示的对应角色/组合
        if event_charas_id:
            _count = 0 if isContainAllCharasId else len(event_charas_id) - 1
            # 获取当期卡的信息
            current_cards = list(filter(lambda x: x['id'] in event_cards, allcards))
            # 遍历所有需要筛选角色
            for each_id in event_charas_id:
                # 若筛选角色在当期卡内
                try:
                    # 针对有附属组合的vocaloid角色
                    if isinstance(each_id, tuple):
                        if next(filter(lambda x: each_id == (x['characterId'],x['supportUnit']), current_cards)):
                            _count += 1
                    # 针对无附属组合的vocaloid角色、sekai角色
                    else:
                        if next(filter(lambda x: each_id == x['characterId'], current_cards)):
                            _count += 1
                # 筛选角色不在当期卡内，next(filter(...))会抛StopIteration异常，pass掉
                except:
                    pass
            if _count < len(event_charas_id):
                continue
        # 获取活动加成角色，属性
        event_bonusecharas = []
        current_bonuse = list(filter(lambda x: x['eventId'] == each['id'], eventDeckBonuses))
        event_bonusecharas.extend(
            bonuse["gameCharacterUnitId"] for bonuse in current_bonuse
            if bonuse['bonusRate'] == 50 and bonuse.get('gameCharacterUnitId')
        )
        event_bonuseattr = next(filter(lambda x: x.get('cardAttr'), current_bonuse))['cardAttr']
        if event_attr != 'all' and event_bonuseattr != event_attr:
            continue
        tmp_bonuse_charas = []
        for unitid in event_bonusecharas:
            charaid, unit, charapicname = analysisunitid(unitid, game_character_units)
            tmp_bonuse_charas.append({
                'id': charaid,
                'unit': unit,
                'asset': charapicname
            })
        # 对箱活加成角色作额外处理，只对杏二箱(id:37)后箱活作处理，之前的箱活加成角色不用变
        if each['id'] >= 37 and len(set(i['unit'] for i in tmp_bonuse_charas)) == 1:
            for bonuse_chara in tmp_bonuse_charas.copy():
                if bonuse_chara['id'] > 20:
                    tmp_bonuse_charas.remove(bonuse_chara)
            tmp_bonuse_charas.append({
                'unit': tmp_bonuse_charas[0]['unit'],
                'asset': 'vs_90.png'
            })
        event_bonusecharas = tmp_bonuse_charas
        # ********************************生成活动图片******************************** #
        event_img = Image.new('RGB', event_size, 'white')
        draw = ImageDraw.Draw(event_img)
        _interval = 10
        _banner_width = 265
        _left_offset = 70

        # 生成banner图
        bannerpic = Image.open(f'{assetpath}/ondemand/event_story/{each["assetbundleName"]}/screen_image/banner_event_story.png')
        bannerpic = bannerpic.resize((_banner_width, int(_banner_width / bannerpic.width * bannerpic.height)))
        event_img.paste(bannerpic, (_left_offset, 0), bannerpic)

        # 生成活动属性和加成角色图
        bonusechara_pic = []
        for bonusechara in event_bonusecharas:
            unitcolor = {
                'piapro': '#000000',
                'light_sound': '#4455dd',
                'idol': '#88dd44',
                'street': '#ee1166',
                'theme_park': '#ff9900',
                'school_refusal': '#884499',
            }
            # 活动角色边框显示组合色
            _chr_pic = Image.open(f'{botpath}/chara/{bonusechara["asset"]}').resize((110, 110))
            _bk = Image.new('RGBA', (130, 130))
            ImageDraw.Draw(_bk).ellipse((0, 0, _bk.size[0], _bk.size[1]), unitcolor[bonusechara['unit']])
            _bk.paste(_chr_pic, (10, 10), _chr_pic)
            bonusechara_pic.append(_bk.resize((30, 30)).copy())
        charapic = union(bonusechara_pic, type='col', length=0, interval=2)
        attrpic = Image.open(f'{botpath}/chara/icon_attribute_{event_bonuseattr}.png').resize((30, 30))
        event_img.paste(attrpic, (bannerpic.width + _left_offset + _interval, 80), attrpic)
        event_img.paste(charapic, (bannerpic.width + _left_offset + _interval + 60, 80), charapic)

        # 生成活动出卡图
        for index, cardid in enumerate(event_cards):
            _c = cardthumnail(cardid, False, allcards).resize((90, 90))
            event_img.paste(_c, (_left_offset + index * 100, bannerpic.height + _interval), _c)
            draw.text((_left_offset + index * (90 + _interval), bannerpic.height + 90 + _interval), f'ID:{cardid}', dark_grey, font10)
        # 生成活动类型和活动时间图
        eventtype = {"marathon": "马拉松(累积点数)", "cheerful_carnival": "欢乐嘉年华(5v5)"}.get(each['eventType'], "")
        startAt = datetime.datetime.fromtimestamp(
            each['startAt'] / 1000, pytz.timezone('Asia/Shanghai')
        ).strftime('%Y/%m/%d %H:%M:%S')
        aggregateAt = datetime.datetime.fromtimestamp(
            each['aggregateAt'] / 1000 + 1, pytz.timezone('Asia/Shanghai')
        ).strftime('%Y/%m/%d %H:%M:%S')
        draw.text((2*_interval, 0), '{:3}'.format(each['id']), 'black', font20)
        draw.text((bannerpic.width + _left_offset + _interval, 0), eventtype, 'black', font20)
        draw.text((bannerpic.width + _left_offset + _interval, 25), f"开始于 {startAt}", 'black', font20)
        draw.text((bannerpic.width + _left_offset + _interval, 50), f"结束于 {aggregateAt}", 'black', font20)
        _tmp_event_imgs.append(event_img.copy())
        # 活动图数量达到每列限制数量
        if len(_tmp_event_imgs) >= limit_count:
            col_event_imgs.append(union(
                _tmp_event_imgs, type='row', bk_color='white',
                interval=event_interval, interval_color=light_grey, interval_size=3,
                padding=event_pad,
                border_type='circle', border_size=4, border_color=dark_grey, border_radius=25
            ))
            _tmp_event_imgs.clear()
    # 拼接未满每列限制数量的剩余活动图
    if len(_tmp_event_imgs) > 0:
        col_event_imgs.append(union(
            _tmp_event_imgs, type='row', bk_color='white',
            interval=event_interval, interval_color=light_grey, interval_size=3,
            padding=event_pad,
            border_type='circle', border_size=4, border_color=dark_grey, border_radius=25
        ))

    # 若没有任何活动满足需求
    if len(col_event_imgs) == 0:
        return None

    # 合成最终的活动图鉴
    _union_img = union(
        col_event_imgs, type='col', padding=handbook_pad, interval=handbook_interval, align_type='top'
    )
    handbook_img = Image.open(f'{botpath}/pics/findevent.png').resize(_union_img.size)
    handbook_img.paste(_union_img, mask=_union_img)

    # 活动图鉴其他标识
    badge_img = Image.open(f'{botpath}/pics/findevent_badge.png')
    badge_img = badge_img.resize((event_size[0] // 2, int(badge_img.height / badge_img.width * event_size[0] // 2)))
    handbook_img.paste(badge_img, (handbook_pad[2], int(handbook_pad[1] / 3 * 2 - badge_img.height)), badge_img.split()[-1])
    water_mark = 'Generated by Unibot'
    tips = '查活动 + [活动ID] 查询活动详情\n查卡 + [卡面ID] 查询卡面详情'
    draw = ImageDraw.Draw(handbook_img)
    draw.text(
        (handbook_img.width - 300 - handbook_pad[3], handbook_img.height - 50 - handbook_pad[1] // 3),
        water_mark,
        '#00CCBB',
        font30
    )
    draw.text(
        (handbook_pad[3], handbook_img.height - 25 - handbook_pad[1] // 3),
        tips,
        '#00CCBB',
        font30
    )
    return handbook_img