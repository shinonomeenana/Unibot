import math
import os
import time
import yaml
import pytz
import datetime
from os import path
from PIL import Image, ImageDraw, ImageFilter
from typing import List, Dict, Union, Optional
from modules.getdata import LeakContent
from modules.texttoimg import t2i, union
from modules.pjskinfo import musicinfo as MusicInfo
from modules.gacha import gachainfo as GachaInfo
from modules.otherpics import (
    cardthumnail,
    cardlarge,
    analysisunitid,
    event as EventInfo
)
from modules.assetdlhelper import load_asset_from_unipjsk
try:
    import ujson as json
except:
    import json

botpath = os.path.abspath(os.path.join(path.dirname(__file__), ".."))
assetpath = botpath + '/data/assets/sekai/assetbundle/resources'
masterdatadir = path.join(botpath, 'masterdata/')


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


def cardtype(cardid):
    with open('masterdata/resourceBoxes.json', 'r', encoding='utf-8') as f:
        resourceBoxes = json.load(f)
    with open('masterdata/gachaCeilExchangeSummaries.json', 'r', encoding='utf-8') as f:
        gachaCeilExchangeSummaries = json.load(f)
    resourcebox_id = find_resourcebox_id_by_cardid(cardid, resourceBoxes)
    for item in gachaCeilExchangeSummaries:
        for exchange in item.get("gachaCeilExchanges", []):
            if exchange.get("resourceBoxId") == resourcebox_id:
                label_type = exchange.get("gachaCeilExchangeLabelType")
                if label_type in ["limited", "fes"]:
                    return label_type
    return False


def cardskill(skillid, skills, description=None):
    for skill in skills:
        if skill['id'] == skillid:
            if description is None:
                description = skill['description']
            count = description.count('{{')
            for i in range(0, count):
                para = description[description.find('{{') + 2:description.find('}}')].split(';')
                for effect in skill['skillEffects']:
                    try:
                        if effect['id'] == int(para[0]):
                            detail = effect['skillEffectDetails']
                            if para[1] == 'd':
                                replace = '/'.join(str(i["activateEffectDuration"]) for i in detail)
                            elif para[1] == 'e':
                                replace = str(effect['skillEnhance']['activateEffectValue'])
                            elif para[1] == 'm':
                                replace = '/'.join(
                                    str(i["activateEffectValue"] + 5*effect['skillEnhance']['activateEffectValue']) for i in detail
                                )
                            else:
                                replace = '/'.join(str(i["activateEffectValue"]) for i in detail)
                            # 全等级效果相同
                            if len(set(replace.split('/'))) == 1:
                                replace = replace.split('/')[0]
                            description = description.replace('{{' + para[0] + ';' + para[1] + '}}', replace, 1)
                    except:
                        pass
            return description
    return ''


class CardInfo(object):
    def __init__(self, config: Optional[Dict] = None):
        self.config: Dict[str, bool] = (  # 基础配置
            config if config else {
                'event': True,  # 展示图是否展示出场活动
                'music': True,  # 展示图是否展示活动歌曲
                'gacha': True,  # 展示图是否展示来源卡池
            }
        )

        self.id: int = 0  # 卡面id
        self.characterId: int = 0  # 角色id
        self.costume3dId: int = 0  # 衣装id
        self.skillId: int = 0  # 技能id

        self.unit: str = 'none'  # 所属组合
        self.cardRarityType: str = ''  # 卡面星数
        self.attr: str = ''  # 卡面属性
        self.isLimited: bool = False  # 卡面是否限定
        self.limitType: str = ''  # 限定类型（普限，fes）
        self.cardParameters: Dict[str, int] = {}  # 卡面综合力
        self.releaseAt: str = ''  # 发布时间

        self.charaName: str = ''  # 角色名称(仅日文)
        self.prefix: str = ''  # 卡面名称(仅日文)
        self.gachaPhrase: Dict[str, str] = {}  # 招募语(含中日文显示)
        self.cardSkillName: Dict[str, str] = {}  # 技能名称(含中日文显示)
        self.cardSkillDes: Dict[str, str] = {}  # 技能效果(含中日文显示)

        self.event: EventInfo = EventInfo()  # 登场活动(如果有的话)
        self.music: MusicInfo = MusicInfo()  # 活动歌曲(如果有的话)
        self.gacha: GachaInfo = GachaInfo()  # 来源卡池(如果有的话)

        # 卡面所需图片资源
        self.assets: Dict[str, Union[str, Dict[str, List[str]]]] = {
            'card': '',  # 卡图
            'costume': {  # 附带衣装
                'hair': [],  # 发型
                'head': [],  # 发饰
                'body': []  # 服装
            },
        }

    def _get_music_info(self):
        if self.event.id == 0:
            # 获取活动id
            with open(masterdatadir + 'eventCards.json', 'r', encoding='utf-8') as f:
                event_cards = json.load(f)
            for each in event_cards:
                if each["cardId"] == self.id:
                    self.event.id = each["eventId"]
                    break
        if self.event.id == 0:
            raise Exception("卡面无对应活动")
        # 获取活动歌曲id
        with open(masterdatadir + 'eventMusics.json', 'r', encoding='utf-8') as f:
            event_musics = json.load(f)
        for each in event_musics:
            if each["eventId"] == self.event.id:
                self.event.music = each["musicId"]
                break
        # 获取活动歌曲信息
        if self.event.music == 0:
            raise Exception("活动无对应歌曲")
        with open(masterdatadir + 'musics.json', 'r', encoding='utf-8') as f:
            musics = json.load(f)
        for each_music in musics:
            if each_music["id"] == self.event.music:
                self.music.id = each_music["id"]
                self.music.title = each_music["title"]
                self.music.lyricist = each_music['lyricist']
                self.music.composer = each_music['composer']
                self.music.arranger = each_music['arranger']
                self.music.assetbundleName = each_music["assetbundleName"]
                self.music.publishedAt = each_music['publishedAt']

    def _get_event_info(self):
        """
        根据卡面id获取当期活动信息
        """
        # 获取活动id
        with open(masterdatadir + 'eventCards.json', 'r', encoding='utf-8') as f:
            event_cards = json.load(f)
        for each in event_cards:
            if each["cardId"] == self.id:
                self.event.id = each["eventId"]
                break
        if self.event.id == 0:
            raise Exception('卡面无对应活动')
        # 获取活动信息
        with open(masterdatadir + 'events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)
        for each_event in events:
            if each_event["id"] == self.event.id:
                self.event.eventType = each_event['eventType']
                self.event.name = each_event['name']
                self.event.assetbundleName = each_event['assetbundleName']
                self.event.startAt = datetime.datetime.fromtimestamp(
                    each_event['startAt'] / 1000, pytz.timezone('Asia/Shanghai')
                ).strftime('%Y/%m/%d %H:%M:%S')
                self.event.aggregateAtorin = each_event['aggregateAt']
                self.event.aggregateAt = datetime.datetime.fromtimestamp(
                    each_event['aggregateAt'] / 1000 + 1, pytz.timezone('Asia/Shanghai')
                ).strftime('%Y/%m/%d %H:%M:%S')
                break
        # 获取参与活动的角色信息、活动属性
        with open(masterdatadir + 'eventDeckBonuses.json', 'r', encoding='utf-8') as f:
            eventDeckBonuses = json.load(f)
        for bonuse in eventDeckBonuses:
            if bonuse['eventId'] == self.event.id:
                if not self.event.bonuseattr:
                    try:
                        self.event.bonuseattr = bonuse['cardAttr']
                    except:
                        pass
                try:
                    if bonuse['bonusRate'] == 50:
                        self.event.bonusechara.append(bonuse["gameCharacterUnitId"])
                except:
                    pass

        with open(masterdatadir + 'gameCharacterUnits.json', 'r', encoding='utf-8') as f:
            game_character_units = json.load(f)
        tmp_bonuse_charas = []
        for unitid in self.event.bonusechara:
            charaid, unit, charapicname = analysisunitid(unitid, game_character_units)
            tmp_bonuse_charas.append({
                'id': charaid,
                'unit': unit,
                'asset': charapicname
            })
        # 对箱活加成角色作额外处理，只对杏二箱(id:37)后箱活作处理，之前的箱活加成角色不用变
        if self.event.id >= 37 and len(set(i['unit'] for i in tmp_bonuse_charas)) == 1:
            for bonuse_chara in tmp_bonuse_charas.copy():
                if bonuse_chara['id'] > 20:
                    tmp_bonuse_charas.remove(bonuse_chara)
            tmp_bonuse_charas.append({
                'unit': tmp_bonuse_charas[0]['unit'],
                'asset': 'vs_90.png'
            })
        self.event.bonusechara = tmp_bonuse_charas

    def _get_gacha_info(self):
        with open(masterdatadir + 'gachas.json', 'r', encoding='utf-8') as f:
            gachas = json.load(f)
        for each_gacha in gachas:
            if not (  # 开服的二三星以及活动报酬卡都是后来才进的卡池，这类卡的来源卡池个人定义为初次登场的卡池
                each_gacha["gachaType"] == 'ceil'
                and each_gacha["name"] != "イベントメンバー出現率UPガチャ"
                and not each_gacha['name'].startswith('[1回限定]')
            ):
                continue
            for each_card in each_gacha["gachaDetails"]:
                if each_card["cardId"] == self.id:
                    self.gacha.id = each_gacha["id"]
                    # gachaCardRarityRateGroupId：
                    # 1天井池和常规池(不清楚怎么区分，只能靠卡面类型区分)、2一去不复返的3星券池子、3fes限、4生日池
                    self.gacha.gachaCardRarityRateGroupId = each_gacha["gachaCardRarityRateGroupId"]
                    self.gacha.name = each_gacha["name"]
                    self.gacha.assetbundleName = each_gacha["assetbundleName"]
                    self.gacha.startAt = datetime.datetime.fromtimestamp(
                        each_gacha['startAt'] / 1000, pytz.timezone('Asia/Shanghai')
                    ).strftime('%Y/%m/%d %H:%M:%S')
                    self.gacha.endAt = datetime.datetime.fromtimestamp(
                        each_gacha["endAt"] / 1000, pytz.timezone('Asia/Shanghai')
                    ).strftime('%Y/%m/%d %H:%M:%S')
                    return

    def getinfo(self, cardid: int, groupid: 0):
        """
        根据卡面id获取卡面信息
        """
        with open(masterdatadir + 'cards.json', 'r', encoding='utf-8') as f:
            allcards = json.load(f)
        for each_card in allcards:
            if each_card["id"] == cardid:
                self.id = each_card["id"]  # 卡面id
                self.characterId = each_card["characterId"]  # 角色id
                self.skillId = each_card["skillId"]  # 技能id

                self.cardRarityType = each_card["cardRarityType"]  # 卡面星数
                self.attr = each_card["attr"]  # 卡面属性
                if each_card.get("supportUnit", "none") != "none":
                    self.unit = each_card["supportUnit"]
                self.prefix = each_card["prefix"]  # 卡面名称
                if each_card["gachaPhrase"] != '-':  # 初始卡无招募语
                    self.gachaPhrase['JP'] = each_card["gachaPhrase"]  # 招募语
                self.cardSkillName['JP'] = each_card["cardSkillName"]  # 技能名称
                if each_card['releaseAt'] / 1000 > time.time():
                    raise LeakContent
                self.releaseAt = datetime.datetime.fromtimestamp(
                    each_card['releaseAt'] / 1000, pytz.timezone('Asia/Shanghai')
                ).strftime('%Y/%m/%d %H:%M:%S')  # 发布时间
                self.assets["card"] = each_card["assetbundleName"]  # 卡面大图asset名称
                # 卡面综合力
                for cardparams in each_card["cardParameters"]:
                    self.cardParameters[cardparams["cardParameterType"]] = cardparams["power"]
                break
        # 日文技能效果
        with open(masterdatadir + 'skills.json', 'r', encoding='utf-8') as f:
            skills = json.load(f)
        for each_skill in skills:
            if each_skill["id"] == self.skillId:
                self.cardSkillDes['JP'] = each_skill["description"]
                break

        # 角色名称(日文)、组合名称
        with open(masterdatadir + 'gameCharacters.json', 'r', encoding='utf-8') as f:
            allcards = json.load(f)
        for each_card in allcards:
            if each_card["id"] == self.characterId:
                self.charaName = (
                        each_card.get("firstName", "") + " " + each_card.get("givenName", "")
                ).strip()  # 角色名称
                self.unit = self.unit if self.unit != 'none' else each_card["unit"]  # 组合名称
                break
        # 获取衣装asset名
        with open(masterdatadir + 'cardCostume3ds.json', 'r', encoding='utf-8') as f:
            costume3ds = json.load(f)
        card_costumes_ids = []
        for each_costume in costume3ds:
            if each_costume['cardId'] == self.id:
                card_costumes_ids.append(each_costume["costume3dId"])
        with open(masterdatadir + 'costume3ds.json', 'r', encoding='utf-8') as f:
            costume3ds = json.load(f)
        for each_costume_id in card_costumes_ids:
            for each_model in costume3ds:
                if each_model['id'] == each_costume_id:
                    _parttype = each_model["partType"]
                    _assetbundleName = each_model["assetbundleName"]
                    self.assets["costume"][_parttype] = self.assets["costume"].get(_parttype, [])
                    self.assets["costume"][_parttype].append(_assetbundleName)
                    break
        
        self.limitType = cardtype(cardid)
        if self.limitType:
            self.isLimited = True

        # # 尝试获取翻译信息
        # with open(f'{botpath}/yamls/translate.yaml', encoding='utf-8') as f:
        #     trans = yaml.load(f, Loader=yaml.FullLoader)
        # # 招募语
        # try:
        #     self.gachaPhrase['CN'] = trans['card_phrase'][self.id]
        # except:
        #     pass
        # # 技能名称
        # try:
        #     self.cardSkillName['CN'] = trans['skill_name'][self.id]
        # except:
        #     pass
        # # 技能效果
        # try:
        #     self.cardSkillDes['CN'] = trans['skill_desc'][self.skillId]
        # except:
        #     pass

        for key in self.cardSkillDes.keys():
            self.cardSkillDes[key] = cardskill(self.skillId, skills, self.cardSkillDes[key])

        # 获取活动信息
        if self.config.get('event', True):
            try:
                self._get_event_info()
            except:
                pass
        # 获取歌曲信息
        if self.config.get('music', True):
            try:
                self._get_music_info()
            except:
                pass

        # 获取卡池信息
        if self.config.get('gacha', True):
            try:
                self._get_gacha_info()
            except:
                pass

    def toimg(self, groupid: 0) -> 'Image':
        """
        生成卡面的详细信息图
        """
        _tmpcards = [{
            'id': self.id,
            'cardRarityType': self.cardRarityType,
            'assetbundleName': self.assets['card'],
            'attr': self.attr
        }]
        style_color = "#00CCBB"  # 作图的背景色
        left_width = 880  # 左侧图的宽度
        left_pad = (30, 30, 40, 40)  # 左侧图的pad
        right_width = 860  # 右侧图的宽度
        right_pad = (65, 75, 50, 50)  # 右侧图的pad
        _l_w = left_width + left_pad[2] + left_pad[3]
        _r_w = right_width + right_pad[2] + right_pad[3]
        # 生成卡面标题图片title_img
        charaname_img = union(
            [t2i(self.prefix, font_color='white', max_width=int(_r_w / 18 * 13)), t2i(self.charaName, font_color='white')],
            type='row',
            length=0,
            interval=5
        )
        unit_img = Image.open(f'{botpath}/pics/logo_{self.unit}.png')
        unit_img = unit_img.resize((int(_r_w / 18 * 5), int(_r_w / 18 * 5 / unit_img.width * unit_img.height)))
        title_img = union(
            [unit_img, charaname_img],
            type='col',
            length=right_width + 40,
            padding=(20, 20, 30, 30),
            interval=35 + (right_width - unit_img.width - charaname_img.width) // 2,
            align_type='center',
            bk_color=style_color,
            border_type='circle',
            border_radius=_r_w // 36
        )
        # 生成卡面详情图片detail_img
        tmp_imgs = []
        # 综合力
        power = sum([self.cardParameters[key] for key in self.cardParameters.keys()])
        tmp_union = union([t2i('综合力'), t2i(str(power))], type='col', length=right_width)
        tmp_imgs.append(tmp_union)
        # 综合力组成
        tmp_paramimgs = []
        tmp_union = union(
            [t2i('演奏'), t2i(str(self.cardParameters['param1']))], type='col', length=right_width
        )
        tmp_paramimgs.append(tmp_union)
        tmp_union = union(
            [t2i('技巧'), t2i(str(self.cardParameters['param2']))], type='col', length=right_width
        )
        tmp_paramimgs.append(tmp_union)
        tmp_union = union(
            [t2i('耐力'), t2i(str(self.cardParameters['param3']))], type='col', length=right_width
        )
        tmp_paramimgs.append(tmp_union)
        tmp_imgs.append(union(tmp_paramimgs, length=0, interval=25, type='row'))
        # 卡面类型
        limit_discribe = {
            'limited': '普通限定',
            'fes': 'FES限定'
        }
        tmp_union = union(
            [t2i('类型'), t2i(limit_discribe[self.limitType] if self.isLimited else '普通')], type='col', length=right_width
        )
        tmp_imgs.append(tmp_union)
        # 技能名
        skillname_img = union(
            [t2i(
                f"{self.cardSkillName[each]}\n({each})", max_width=586, wrap_type='right'
            ) for each in self.cardSkillName.keys()],
            type='row',
            align_type='right',
            length=0,
            interval=10,
        )
        tmp_imgs.append(union(
            [t2i('技能名'), skillname_img], type='col', length=right_width
        ))
        # 技能效果
        skilldes_img = union(
            [t2i(
                f"{self.cardSkillDes[each]}\n({each})",
                max_width=right_width - right_pad[2] - 160,
                wrap_type='right'
            ) for each in self.cardSkillDes.keys()],
            type='row',
            align_type='right',
            length=0,
            interval=10
        )
        tmp_imgs.append(union(
            [t2i('技能效果'), skilldes_img], type='col', length=right_width
        ))
        # 招募语
        if len(self.gachaPhrase) > 0:
            gachahrase_img = union(
                [t2i(
                    f"{self.gachaPhrase[each]}\n({each})", max_width=586, wrap_type='right'
                ) for each in self.gachaPhrase.keys()],
                type='row',
                align_type='right',
                length=0,
                interval=10
            )
            tmp_imgs.append(union(
                [t2i('招募语'), gachahrase_img], type='col', length=right_width
            ))
        # 发布时间
        tmp_union = union([t2i('发布时间'), t2i(f'{self.releaseAt}(UTC+8)')], type='col', length=right_width)
        tmp_imgs.append(tmp_union)
        # 卡面缩略图
        if self.cardRarityType in ['rarity_3', 'rarity_4']:
            cardthumnail_pic = union(
                [
                    cardthumnail(self.id, False, _tmpcards).resize((180, 180)),
                    cardthumnail(self.id, True, _tmpcards).resize((180, 180))
                ], type='col', length=0, interval=30)
        else:
            cardthumnail_pic = cardthumnail(self.id, False).resize((180, 180))
        tmp_imgs.append(union([t2i('缩略图'), cardthumnail_pic], type='col', length=right_width))
        # 衣装缩略图
        single_costume_pics = []
        for key in self.assets['costume'].keys():
            for i in self.assets['costume'][key]:
                asset_cache_path = load_asset_from_unipjsk(f'startapp/thumbnail/costume/{i}.png')
                tmp = Image.open(asset_cache_path).resize((180, 180))
                _type = {'hair': '发型', 'head': '发饰', 'body': '服装'}
                single_costume_pics.append(
                    union([tmp, t2i(_type[key])], type='row', length=0, interval=10)
                )
        _cnt = math.ceil(len(single_costume_pics) / 2)
        if _cnt > 0:
            costume_pic = union(
                single_costume_pics[0: 2], type='col', length=0, interval=30
            )
            for i in range(_cnt - 1):
                tmp_union_pic = union(
                    single_costume_pics[i + 2: i + 4], type='col', length=0, interval=30
                )
                costume_pic = union([costume_pic, tmp_union_pic], type='row', length=0, interval=30)

            tmp_imgs.append(union([t2i('衣装缩略图'), costume_pic], type='col', length=right_width))

        tmp_imgs.append(union([t2i('ID'), t2i(str(self.id))], type='col', length=right_width))

        detail_img = union(
            tmp_imgs,
            type="row",
            interval=43,
            interval_size=3,
            interval_color="#dbdbdb",
            padding=right_pad,
            border_size=3,
            border_color="#a19d9e",
            border_type="circle",
            bk_color='white'
        )

        # 生成卡面大图cardlarge_img
        if self.cardRarityType in ['rarity_3', 'rarity_4']:
            cardlarge_img = union(
                [
                    cardlarge(self.id, False, _tmpcards).resize((_l_w, int(_l_w * 0.61))),
                    cardlarge(self.id, True, _tmpcards).resize((_l_w, int(_l_w * 0.61))),
                ], type='row', length=0, interval=30)
        else:
            cardlarge_img = cardlarge(self.id, False, _tmpcards).resize((_l_w, int(_l_w * 0.61)))

        # 生成gacha大图gacha_img
        gacha_img = None
        if self.gacha.id != 0:
            asset_cache_path = load_asset_from_unipjsk(f'startapp/home/banner/banner_gacha{self.gacha.id}/banner_gacha{self.gacha.id}.png')
            bannerpic = Image.open(asset_cache_path)
            bannerpic = bannerpic.resize((left_width, int(left_width / bannerpic.width * bannerpic.height)))
            timepic = union(
                [t2i('开始时间：' + self.gacha.startAt, font_size=25),
                 t2i('结束时间：' + self.gacha.endAt, font_size=25)],
                type='col',
                length=left_width,
            )
            # TODO: 修改判断方法，这个方法是错的，假四会显示池子是普通
            if (  # 若卡面为限定卡，当卡池也为当期池时，认定池子为限定池
                    self.isLimited
                    and self.gacha.startAt == self.releaseAt
                    and self.gacha.gachaCardRarityRateGroupId != 3
            ):
                gachatype = "期间限定"
            else:
                gachatype = {
                    "1": "常规", "3": "fes限定", "4": "生日限定"
                }.get(str(self.gacha.gachaCardRarityRateGroupId), "")
            gachanamepic = union(
                [t2i(self.gacha.name, max_width=left_width), t2i(f"{gachatype}  ID:{self.gacha.id}", font_size=30)],
                type='row',
                length=0,
                interval=10
            )
            gacha_img = union(
                [bannerpic, gachanamepic, timepic],
                type='row',
                padding=left_pad,
                interval=40,
                bk_color='white',
                border_color='#a19d9e',
                border_size=3,
                border_type='circle'
            )

        # 生成event大图event_img
        event_img = None
        if self.event.id != 0:
            asset_cache_path = load_asset_from_unipjsk(f'ondemand/event_story/{self.event.assetbundleName}/screen_image/banner_event_story.png')
            bannerpic = Image.open(asset_cache_path)
            bannerpic = bannerpic.resize((left_width, int(left_width / bannerpic.width * bannerpic.height)))
            eventtype = {"marathon": "马拉松(累积点数)", "cheerful_carnival": "欢乐嘉年华(5v5)"}.get(self.event.eventType, "")
            eventnamepic = union(
                [t2i(self.event.name, max_width=left_width), t2i(f"{eventtype}  ID:{self.event.id}", font_size=30)],
                type='row',
                length=0,
                interval=10
            )
            timepic = union(
                [t2i('开始时间：' + self.event.startAt, font_size=30),
                 t2i('结束时间：' + self.event.aggregateAt, font_size=30)],
                type='row',
                length=0,
                interval=40
            )
            bonusechara_pic = []
            for bonusechara in self.event.bonusechara:
                unitcolor = {
                    'piapro': '#000000',
                    'light_sound': '#4455dd',
                    'idol': '#88dd44',
                    'street': '#ee1166',
                    'theme_park': '#ff9900',
                    'school_refusal': '#884499',
                }
                # 活动角色边框显示组合色
                # 这里不是很懂为什么需要经过多次放缩才能让图片锯齿没那么明显，但总之试出来了(ˉ▽ˉ；)...
                _chr_pic = Image.open(f'{botpath}/chara/{bonusechara["asset"]}').resize((110, 110))
                _bk = Image.new('RGBA', (130, 130), color=unitcolor[bonusechara['unit']])
                _bk.paste(_chr_pic, (10, 10), mask=_chr_pic.split()[-1])
                mask = Image.new("L", _bk.size, 0)
                ImageDraw.Draw(mask).ellipse((1, 1, _bk.size[0] - 2, _bk.size[1] - 2), 255)
                mask = mask.filter(ImageFilter.GaussianBlur(0))
                _bk.putalpha(mask)
                bonusechara_pic.append(_bk.resize((65, 65)).copy())
            charapic = union(bonusechara_pic, type='col', length=0, interval=10)
            try:
                attrpic = Image.open(f'{botpath}/chara/icon_attribute_{self.event.bonuseattr}.png').resize((60, 60))
            except IOError:
                attrpic = Image.new('RGBA', (1, 1), (0, 0, 0, 0))  # 创建一个1x1透明图像
            _ = union([attrpic, charapic], type='row', interval=10, align_type='right')
            _ = union([timepic, _], type='col', interval=60, length=left_width)
            event_img = union(
                [bannerpic, eventnamepic, _],
                padding=left_pad,
                interval=40,
                type='row',
                bk_color='white',
                border_type='circle',
                border_size=3,
                border_color='#a19d9e'
            )

        # 生成music大图music_img
        music_img = None
        if self.music.id != 0:
            # 图、名称、时间
            asset_cache_path = load_asset_from_unipjsk(fr'startapp/music/jacket/jacket_s_{str(self.music.id).zfill(3)}/jacket_s_{str(self.music.id).zfill(3)}.png')
            jacketpic = Image.open(asset_cache_path).resize((280, 280))

            musicnamepic = t2i(self.music.title, font_size=50, max_width=left_width)
            timepic = t2i('上线时间：' + datetime.datetime.fromtimestamp(
                self.music.publishedAt / 1000, pytz.timezone('Asia/Shanghai')
            ).strftime('%Y/%m/%d %H:%M:%S'))
            _m_w = left_width - 280 - left_pad[2]
            authorpic = union(
                [t2i(f'作词： {self.music.lyricist}', font_size=40, max_width=_m_w),
                 t2i(f'作曲： {self.music.composer}', font_size=40, max_width=_m_w),
                 t2i(f'编曲： {self.music.arranger}', font_size=40, max_width=_m_w)],
                type='row',
                length=0,
                interval=5,
                align_type='left'
            )
            music_img = union(
                [union(
                    [jacketpic, authorpic],
                    type='col',
                    interval=50,
                    length=left_width
                ), union(
                    [musicnamepic, t2i(f"ID:{self.music.id}", font_size=30)],
                    type='row',
                    interval=10,
                ), timepic],
                type='row',
                interval=40,
                padding=left_pad,
                bk_color='white',
                border_type='circle',
                border_size=3,
                border_color='#a19d9e'
            )

        _interval = 60
        left_imgs = [cardlarge_img]
        right_imgs = [title_img, detail_img]
        # gacha图放在左边
        if gacha_img:
            _k = '当期卡池' if self.releaseAt == self.gacha.startAt else '初次可得卡池'
            _t = t2i(_k, font_size=50, font_color='white')
            _i = Image.new('RGBA', (_l_w, 70))
            ImageDraw.Draw(_i).rounded_rectangle((0, 0, _i.width, _i.height), 25, style_color)
            _i.paste(_t, ((_l_w - 50 * len(_k)) // 2, 10), mask=_t.split()[-1])
            left_imgs.append(_i.copy())
            left_imgs.append(gacha_img)
        # event图放在左边
        if event_img:
            _t = t2i('活动', font_size=50, font_color='white')
            _i = Image.new('RGBA', (_l_w, 70))
            _d = ImageDraw.Draw(_i)
            _d.rounded_rectangle((0, 0, _i.width, _i.height), 25, style_color)
            _i.paste(_t, ((_l_w - 100) // 2, 10), mask=_t.split()[-1])
            left_imgs.append(_i.copy())
            left_imgs.append(event_img)
        # music图根据左右侧图长度差距决定放在哪边
        if music_img:
            _i = Image.new('RGBA', (_l_w, 70))
            ImageDraw.Draw(_i).rounded_rectangle((0, 0, _i.width, _i.height), 25, style_color)
            _t = t2i('歌曲', font_size=50, font_color='white')
            _i.paste(_t, ((_l_w - 100) // 2, 10), mask=_t.split()[-1])
            if (
                    sum(i.height for i in left_imgs) + _interval * (len(right_imgs) - 1) >
                    sum(i.height for i in right_imgs) + _interval * (len(left_imgs) - 1) + 80
            ):
                right_imgs.append(_i.copy())
                right_imgs.append(music_img)
            else:
                left_imgs.append(_i.copy())
                left_imgs.append(music_img)
        # 合成左侧图
        left_img = union(
            left_imgs,
            type='row',
            interval=_interval,
            length=_l_w,
            align_type='left',
        )
        # 合成右侧图
        right_img = union(right_imgs, type='row', interval=_interval, align_type='left')
        # 生成最终的info_img
        # info_pad留白，用于自行留下水印
        info_pad = (60, 180)
        info_width = int(sum([left_img.width, right_img.width]) + info_pad[0])
        info_height = int(max([left_img.height, right_img.height]))
        info_img = Image.open(f'{botpath}/pics/cardinfo.png').resize((info_width + info_pad[0] * 2, info_height + info_pad[1] * 2))
        info_img.paste(left_img, info_pad, mask=left_img.split()[-1])
        info_img.paste(right_img, (left_img.width + info_pad[0] * 2, info_pad[1]), mask=right_img.split()[-1])

        badge_img = Image.open(f'{botpath}/pics/cardinfo_badge.png')
        badge_img = badge_img.resize((right_img.width // 2, int(badge_img.height / badge_img.width * right_img.width // 2)))
        info_img.paste(badge_img, (info_pad[0], int(info_pad[1] / 3 * 2 - badge_img.height)), mask=badge_img.split()[-1])
        watermark_img = t2i(f'Code by Yozora (Github @cYanosora)', font_size=35, font_color=style_color)
        info_img.paste(
            watermark_img,
            (info_img.width - watermark_img.width - info_pad[0],
             info_img.height - watermark_img.height - info_pad[1] // 6),
            mask=watermark_img.split()[-1]
        )
        return info_img
