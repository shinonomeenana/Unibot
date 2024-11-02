import os
import re
import time

import pytz
import ujson as json
import datetime
from hashlib import md5

import yaml
from PIL import ImageFont, Image, ImageDraw
from typing import Optional, Dict, List, Tuple, Union
from modules.chara import aliastocharaid
from modules.otherpics import analysisunitid, cardthumnail
from modules.texttoimg import union
from modules.assetdlhelper import load_asset_from_unipjsk


botpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
assetpath = botpath + '/data/assets/sekai/assetbundle/resources'
masterdatadir = os.path.join(botpath, 'masterdata/')


def event_argparse(args: List = None):
    if not args:
        args = []
    event_type = None            # 活动类型
    event_attr = None            # 活动属性
    event_units_name = []        # 活动组合名称，单数时匹配箱活，多数时匹配混活
    event_charas_id = []         # 活动出卡角色id
    isEqualAllUnits = True       # True代表活动加成与筛选组合必须一致，False代表加成包含所有筛选组合即可，且不匹配箱活
    isContainAllCharasId = True  # True代表活动出卡必须包含所有筛选角色，False代表出卡包含任意筛选角色即可
    islegal = True               # 参数是否合法
    isTeamEvent = None           # 是否指定箱活
    unit_dict = {
        'ln': 'light_sound', 'mmj': 'idol', 'vbs': 'street', 'ws': 'theme_park', '25h': 'school_refusal',
    }
    team_dict = {
        '箱活': True, '团队活': True, '团内活': True, '混活': False, '团外活': False
    }
    event_type_dict = {
        '普活': 'marathon', '马拉松': 'marathon', 'marathon': 'marathon',
        '5v5': 'cheerful_carnival', '嘉年华': 'cheerful_carnival', 'cheerful_carnival': 'cheerful_carnival'
    }
    event_attr_dict = {
        '蓝星': 'cool', '紫月': 'mysterious', '橙心': 'happy', '黄心': 'happy', '粉花': 'cute', '绿草': 'pure',
        '蓝': 'cool', '紫': 'mysterious', '橙': 'happy', '黄': 'happy', '粉': 'cute', '绿': 'pure',
        '星': 'cool', '月': 'mysterious', '心': 'happy', '花': 'cute', '草': 'pure',
        'cool': 'cool', 'mysterious': 'mysterious', 'happy': 'happy', 'cute': 'cute', 'pure': 'pure',
    }
    chara_dict = {
        'ick': 1, 'saki': 2, 'hnm': 3, 'shiho': 4,
        'mnr': 5, 'hrk': 6, 'airi': 7, 'szk': 8,
        'khn': 9, 'an': 10, 'akt': 11, 'toya': 12,
        'tks': 13, 'emu': 14, 'nene': 15, 'rui': 16,
        'knd': 17, 'mfy': 18, 'ena': 19, 'mzk': 20,
        'miku': 21, 'rin': 22, 'len': 23, 'luka': 24, 'meiko': 25, 'kaito': 26
    }
    chara2unit_dict = {
        'light_sound': [1,2,3,4],
        'idol': [5,6,7,8],
        'street': [9,10,11,12],
        'theme_park': [13,14,15,16],
        'school_refusal': [17,18,19,20]
    }
    for arg in args:
        # 参数是否指定了箱活或混活
        if arg in team_dict.keys():
            isTeamEvent = team_dict[arg]
            continue
        # 参数是否为活动类型，只能指定一种
        if _ := event_type_dict.get(arg):
            if event_type:
                islegal = False
                break
            else:
                event_type = _
                continue
        # 参数是否为活动属性，只能指定一种
        if _ := event_attr_dict.get(arg):
            if event_attr:
                islegal = False
                break
            else:
                event_attr = _
                continue
        # 参数是否为组合缩写(指定一个时为箱活，指定多个时为混活)
        if _ := unit_dict.get(arg):
            event_units_name.append(_)
            continue
        # 参数是否为组合缩写(对参数中含"混"、"加成"的额外再判定一次)
        # 末尾为"混"、"加成"，说明需要筛选加成包含此组合的活动
        unit_rule = "|".join(unit_dict.keys())
        if match := re.match(rf'^({unit_rule})(?:混|加成)$', arg):
            try:
                event_units_name.append(unit_dict[match.group(1)])
            except KeyError:
                islegal = False
                break
            else:
                isEqualAllUnits = False
                continue
        # 中间为"混"
        if match := re.match(rf'^({unit_rule})混({unit_rule}).*$', arg):
            try:
                event_units_name.extend(unit_dict[j] for j in match.group().split('混'))
                continue
            except KeyError:
                islegal = False
                break
        # 参数是否是带附属组合的vs角色
        if match := re.match(rf"^({unit_rule})(.+)", arg):
            unit = match.group(1)
            alias = match.group(2)
            charaid = chara_dict.get(alias)
            if not charaid:
                charaid = aliastocharaid(alias)[0]
            if charaid > 20:
                event_charas_id.append((charaid, unit_dict[unit]))
                continue
            else:
                islegal = False
                break
        # 以上判定均无果，则认定为sekai角色或无附属组合的vs角色
        charaid = chara_dict.get(arg)
        if not charaid:
            charaid = aliastocharaid(arg)[0]
        if charaid:
            event_charas_id.append(charaid)
        # 参数仍无法识别
        else:
            islegal = False
            break
    for i in event_charas_id:
        if len(event_units_name) == 0:
            break
        if isinstance(i, tuple):
            unit = i[1]
        elif i <= 20:
            unit = [x for x in chara2unit_dict.keys() if i in chara2unit_dict[x]][0]
        else:
            continue
        if unit not in event_units_name:
            event_units_name.append(unit)
            isEqualAllUnits = False
    # 箱活标志只能与活动类型、活动属性搭配
    if isTeamEvent is not None and (len(event_units_name) > 0 or len(event_charas_id) > 0):
        islegal = False
    return {
        'event_type': event_type, 'event_attr': event_attr,
        'event_units_name': list(set(event_units_name)), 'event_charas_id': list(set(event_charas_id)),
        'isEqualAllUnits': isEqualAllUnits, 'isContainAllCharasId': isContainAllCharasId,
        'isTeamEvent': isTeamEvent, 'islegal': islegal
    }


def findevent(msg: str = '') -> str:
    """
    查询活动，返回图片路径
    :param msg: 用户所发送的消息
    """
    args = msg.strip().split()
    # 解析[关键字]参数
    params = event_argparse(args)
    # 当用户发送文本带有[关键字]但关键字不合规范时，返回提示图
    if not params['islegal']:
        tip_path = f"{botpath}/pics/findevent_tips.jpg"
        return tip_path
    # 检查本地活动图鉴是否需要更新
    with open(masterdatadir + 'events.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
    current_time = time.time()
    events = [event for event in events if (event["startAt"] - 3 * 3600 * 1000) / 1000 <= current_time]
    count = len(events)
    # 变化图片路径格式
    _event_charas_id = params['event_charas_id'].copy()
    _event_units_name = params['event_units_name'].copy()
    params['event_units_name'].sort()
    charas_id_name = params['event_charas_id']
    for i in range(len(_event_charas_id)):
        if isinstance(_event_charas_id[i], tuple):
            charaid = _event_charas_id[i][0] + ([
                 'light_sound','idol','street','theme_park','school_refusal'
            ].index(_event_charas_id[i][1])+1)*6
            charas_id_name[i] = charaid
    charas_id_name.sort()
    save_file_prefix = md5(''.join(str(params.values())).encode()).hexdigest()
    save_path = f'piccache/findevent/{save_file_prefix}-{count}.jpg'
    # 还原
    params['event_charas_id'] = _event_charas_id
    params['event_units_name'] = _event_units_name
    # 图片存在缓存，直接发送
    if os.path.exists(save_path):
        return botpath + '/' + save_path
    # 需要生成新活动图鉴
    else:
        # 因为需要更新，所以清除所有旧活动图鉴
        for file in os.listdir(f'piccache/findevent'):
            if not file.split('.')[0].endswith(str(count)):
                os.remove(f'piccache/findevent/{file}')

        # 生成图片
        pic = drawEventHandbook(events=events, **params)
        if pic:
            pic = pic.convert('RGB')
            pic.save(save_path, quality=70)
            return botpath + '/' + save_path
        else:
            tip_path = f"{botpath}/pics/findevent_tips.jpg"
            return tip_path


def drawEventHandbook(
    event_type: Optional[str] = None,
    event_attr: Optional[str] = None,
    event_units_name: Optional[List] = None,
    event_charas_id: Optional[List[Union[int, Tuple[int, str]]]] = None,
    isEqualAllUnits: bool = True,
    isContainAllCharasId: bool = True,
    isTeamEvent: Optional[bool] = None,
    events: Optional[Dict] = None,
    *args, **kwargs
):
    """
    生成活动图鉴
    :param event_type: 筛选的活动类型
    :param event_attr: 筛选的活动属性
    :param event_units_name: 筛选的活动组合
    :param event_charas_id: 筛选的活动出卡角色
    :param isEqualAllUnits: 筛选的活动组合是否需要完全等同所有组合名称，针对event_units_name参数
    :param isContainAllCharasId: 筛选的活动出卡是否需要包含所有角色id，针对event_charas_id参数
    :param isTeamEvent: True时只筛选箱活、False时只筛选混活，会无视除event_type、event_attr的筛选条件
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
    if event_type != 'marathon':
        with open(masterdatadir + 'cheerfulCarnivalTeams.json', 'r', encoding='utf-8') as f:
            allteams = json.load(f)
        # with open(f'{botpath}/yamls/translate.yaml', encoding='utf-8') as f:
        #     trans = yaml.load(f, Loader=yaml.FullLoader)
    font30 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=30)
    font20 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=20)
    font10 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', size=10)
    # 筛选：指定活动图鉴显示的活动类型
    if event_type is not None:
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
        event_bonuseattr = next(filter(lambda x: x.get('cardAttr'), current_bonuse), {}).get('cardAttr')
        if event_attr is not None and event_bonuseattr != event_attr:
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
        # 加成角色的所属团体
        belong_units = set(map(lambda x: x['unit'], event_bonusecharas))
        # 限制为查询所有箱活
        if isTeamEvent is True and len(belong_units) != 1:
            continue
        # 限制为查询所有混活
        if isTeamEvent is False and len(belong_units) == 1:
            continue
        if isTeamEvent is None and event_units_name:
            # 当期加成与筛选团体完全吻合（筛选团体单数时即为筛选箱活）
            if isEqualAllUnits and belong_units != set(event_units_name):
                continue
            # 当期加成中存在筛选团体即可（但排除箱活），可以是复数
            if not isEqualAllUnits and not (
                len(set(belong_units)) > 1 and
                set(event_units_name).issubset(belong_units)
            ):
                continue
        # ********************************生成活动图片******************************** #
        event_img = Image.new('RGB', event_size, 'white')
        draw = ImageDraw.Draw(event_img)
        _interval = 10
        _banner_width = 265
        _left_offset = 70
        _team_size = 70
        _team_pad = 5

        # 生成banner图
        # bannerpic_path = f'{assetpath}/ondemand/event_story/{each["assetbundleName"]}/screen_image/banner_event_story.png'
        # print(bannerpic_path)
        asset_cache_path = load_asset_from_unipjsk(f'ondemand/event_story/{each["assetbundleName"]}/screen_image/banner_event_story.png')
        bannerpic = Image.open(asset_cache_path)
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
        try:
            attrpic = Image.open(f'{botpath}/chara/icon_attribute_{event_bonuseattr}.png').resize((30, 30))
            event_img.paste(attrpic, (bannerpic.width + _left_offset + _interval, 80), attrpic)
        except FileNotFoundError:
            pass
        event_img.paste(charapic, (bannerpic.width + _left_offset + _interval + 60, 80), charapic)

        # 如果活动类型为5v5，粘贴team图
        if each['eventType'] == 'cheerful_carnival':
            teams_info = filter(lambda x: x['eventId'] == each['id'], allteams)
            for _i, team_info in enumerate(teams_info):
                asset_cache_path = load_asset_from_unipjsk(f'ondemand/event/{each["assetbundleName"]}/team_image/{team_info["assetbundleName"]}.png')
                team_img = Image.open(asset_cache_path)
                team_img = team_img.resize((_team_size, _team_size))
                team_bk_img = Image.new('RGBA', (_team_size + _team_pad * 2, _team_size + _team_pad * 2))
                _color = "#00bbdd" if _i % 2 else "#ff8833"
                _draw = ImageDraw.Draw(team_bk_img)
                _draw.rounded_rectangle((0, 0, _team_size + _team_pad, _team_size + _team_pad), 10, _color, light_grey, 3)
                team_bk_img.paste(team_img, (_team_pad - 2, _team_pad - 2), team_img)
                team_name = team_info['teamName']
                # try:
                #     team_name = trans['cheerfulCarnivalTeams'][team_info['id']]
                # except KeyError:
                #     team_name = team_info['teamName']
                pos = (_left_offset+_banner_width+_interval*2+256+_i*(_team_size+2*_team_pad+_interval*3), 0)
                event_img.paste(team_bk_img, (pos[0] + _interval, pos[1]), team_bk_img)
                if _i != 0:
                    draw.text((pos[0] - _interval * 2, pos[1] + _team_size // 2 - 15), 'VS', 'black', font20)
                _name_width = font20.getsize(team_name)[0]
                if _name_width > _team_size + 2 * _interval:
                    _name_width = font10.getsize(team_name)[0]
                    draw.text((pos[0] + (_team_size + 2 * (_interval + _team_pad) - _name_width) // 2,
                               pos[1] + _team_size + _interval), team_name, 'black', font10)
                else:
                    draw.text(
                        (pos[0] + (_team_size + 2 * (_interval + _team_pad) - _name_width) // 2, pos[1] + _team_size),
                        team_name, 'black', font20)

        # 生成活动出卡图
        for index, cardid in enumerate(event_cards):
            _c = cardthumnail(cardid, False, allcards).resize((90, 90))
            event_img.paste(_c, (_left_offset + index * 100, bannerpic.height + _interval), _c)
            draw.text((_left_offset + index * (90 + _interval), bannerpic.height + 90 + _interval), f'ID:{cardid}', dark_grey, font10)
        # 生成活动类型和活动时间图
        eventtype = {"marathon": "马拉松(累积点数)", "cheerful_carnival": "欢乐嘉年华(5v5)", "world_bloom": "WORLD LINK"}.get(each['eventType'], "")
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
    water_mark = 'Code by Yozora (Github @cYanosora)\nGenerated by Unibot'
    tips = '查活动 + [活动ID] 查询活动详情\n查卡 + [卡面ID] 查询卡面详情'
    draw = ImageDraw.Draw(handbook_img)
    draw.text(
        (handbook_img.width - 500 - handbook_pad[3], handbook_img.height - 50 - handbook_pad[1] // 3),
        water_mark,
        '#00CCBB',
        font30
    )
    draw.text(
        (handbook_pad[3], handbook_img.height - 50 - handbook_pad[1] // 3),
        tips,
        '#00CCBB',
        font30
    )
    return handbook_img