import os
import ujson as json
import random
from datetime import datetime
from ujson import JSONDecodeError
import asyncio
import aiocqhttp
import aiofiles
import aiohttp
import requests
import re
import time
import traceback
import yaml
from aiocqhttp import CQHttp, Event
from chunithm.alias import chualias, chudel, chuset
from chunithm.daily_bonus import chuni_signin, chuni_signin_lin
from modules.chara import charaset, grcharaset, charadel, charainfo, grcharadel, aliastocharaid, get_card, cardidtopic, \
    findcard, getvits, getcardinfo
from chunithm.qiu import getqiubind, qiu_bind_aimeid, qiub30
from modules.config import whitelist, msggroup, groupban, asseturl, verifyurl, distributedurl
from modules.blacklist import *
from modules.getdata import apiCallError, maintenanceIn, userIdBan, QueryBanned
from modules.getdata import LeakContent
from modules.findevent import findevent
from modules.opencv import matchjacket
from modules.otherpics import geteventpic
from modules.gacha import getcharaname, getcurrentgacha, fakegacha
from modules.musics import parse_bpm, aliastochart, idtoname, notecount, tasseiritsu, findbpm, \
    getcharttheme, setcharttheme, getPlayLevel, levelRankPic
from modules.pjskguess import get_two_lines, getrandomjacket, cutjacket, getrandomchart, cutchartimg, getrandomcard, cutcard, random_lyrics,\
    getrandommusic, cutmusic, getrandomchartold, cutchartimgold, recordGuessRank, guessRank, getRandomSE, cutSE
from modules.pjskinfo import aliastomusicid, pjskset, pjskdel, pjskalias, pjskinfo, writelog
from modules.profileanalysis import daibu, rk, pjskjindu, pjskprofile, pjskb30, r30
from modules.sk import sk, getqqbind, bindid, setprivate, skyc, verifyid, gettime, teamcount, chafang, \
    getstoptime, ss, drawscoreline, cheaterFound, cheater_ban_reason, score_line
from modules.texttoimg import texttoimg, blank
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from imageutils import text2image
import hashlib
from chunithm.b30 import chunib30, getchunibind, bind_aimeid
from chunithm.info import search_song, song_details, chu_level_rank
from chunithm.chart import get_chunithm_chart
from wds.musicinfo import wds_alias_to_music_id, wdsinfo, wdsset, wdsdel, wdsalias, wds_alias_to_chart
from wds.event import wds_score_line

if os.path.basename(__file__) == 'bot.py':
    bot = CQHttp()
    botdebug = False
else:
    guildhttpport = 1988
    bot = CQHttp(api_root=f'http://127.0.0.1:{guildhttpport}')
    botdebug = True
botdir = os.getcwd()

pjskguess = {}
charaguess = {}
ciyunlimit = {}
groupaudit = {}
wife = {}
menberLists = {}
gachalimit = {'lasttime': '', 'count': 0}
pokelimit = {'lasttime': '', 'count': 0}
vitslimit = {'lasttime': '', 'count': 0}
admin = [1103479519]
mainbot = [1513705608]
requestwhitelist = []  # 邀请加群白名单 随时设置 不保存到文件

botname = {
    1513705608: '一号机',
    3506606538: '三号机',
    "9892212940143267151": '频道bot'
}
guildbot = "9892212940143267151"
send1 = False
send3 = False
opencvmatch = False

async def geturl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            print(res.status)
            text = await res.text()
            return text

@bot.on_message('group')
async def handle_msg(event: Event):
    if event.self_id == guildbot:
        return
    global blacklist
    global botdebug
    global wife
    global menberLists
    if event.user_id in block:
        # print('黑名单成员已拦截')
        return
    if event.raw_message == '关闭sk':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id in blacklist['sk']:  # 如果在黑名单
                await bot.send(event, '已经关闭过了')
                return
            blacklist['sk'].append(event.group_id)  # 加到黑名单
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '关闭成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '开启sk':
        info = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=event.user_id)
        if info['role'] == 'owner' or info['role'] == 'admin':
            if event.group_id not in blacklist['sk']:  # 如果不在黑名单
                await bot.send(event, '已经开启过了')
                return
            blacklist['sk'].remove(event.group_id)  # 从黑名单删除
            with open('yamls/blacklist.yaml', "w") as f:
                yaml.dump(blacklist, f)
            await bot.send(event, '开启成功')
        else:
            await bot.send(event, '此命令需要群主或管理员权限')
        return
    if event.raw_message == '开启debug' and event.user_id in admin:
        botdebug = True
        await bot.send(event, '开启成功')
    if event.raw_message == '关闭debug' and event.user_id in admin:
        botdebug = False
        await bot.send(event, '关闭成功')


@bot.on_message('group')
def sync_handle_msg(event):
    if event.self_id == guildbot:
        event.message = event.message[event.message.find(f"qq={guildbot}") + len(f"qq={guildbot}]"):].strip()
    global pjskguess
    global charaguess
    global ciyunlimit
    global gachalimit
    global blacklist
    global requestwhitelist
    if botdebug:
        timeArray = time.localtime(time.time())
        Time = time.strftime("[%Y-%m-%d %H:%M:%S]", timeArray)
        try:
            print(Time, botname[event.self_id] + '收到消息', event.group_id, event.user_id, event.message.replace('\n', ''))
        except KeyError:
            print(Time, '测试bot收到消息', event.group_id, event.user_id, event.message.replace('\n', ''))
    if event.group_id in groupban:
        # print('黑名单群已拦截')
        return
    if event.user_id in block:
        # print('黑名单成员已拦截')
        return
    if event.message[0:1] == '/':
        event.message = event.message[1:]
    try:
        # -----------------------功能测试-----------------------------
        # if event.message == 'test':
        #     sendmsg(event, event.sender['nickname'] + event.sender['card'])
        # -----------------------结束测试-----------------------------
        if event.message == 'help':
            if event.self_id == guildbot:
                sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/guild/')
            else:
                sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/')
            return
        if event.message.startswith('songinfo'):
            sendmsg(event, '从来没有过songinfo命令，请使用pjskinfo或song（频道用）')
            return
        if msg := re.match('(?:pjskinfo|song|查歌曲?)(.*)', event.message):
            resp = aliastomusicid(msg.group(1).strip())
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                leak = pjskinfo(resp['musicid'])
                if resp['match'] < 0.8:
                    text = '你要找的可能是：'
                else:
                    text = ""
                if leak:
                    text = text + f"匹配度:{round(resp['match'], 4)}\n⚠该内容为剧透内容"
                else:
                    if resp['translate'] == '':
                        text = text + f"{resp['name']}\n匹配度:{round(resp['match'], 4)}"
                    else:
                        text = text + f"{resp['name']} ({resp['translate']})\n匹配度:{round(resp['match'], 4)}"
                sendmsg(event,
                        text + fr"[CQ:image,file=file:///{botdir}\piccache\pjskinfo\{resp['musicid']}.png,cache=0]")
            return
        if event.message[:7] == 'pjskset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[7:]
            para = event.message.split('to')
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = pjskset(para[0], para[1], event.user_id, username, f"{qun['name']}({event.guild_id})内", is_hide=True)
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = pjskset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:7] == 'pjskdel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[7:]
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = pjskdel(event.message, event.user_id, username, f"{qun['name']}({event.guild_id})内")
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = pjskdel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:9] == 'pjskalias':
            if event.self_id == guildbot:
                sendmsg(event, '频道bot不支持此功能')
                return
            event.message = event.message[9:]
            resp = pjskalias(event.message)
            sendmsg(event, resp)
            return
        # if event.message[:8] == "sekai真抽卡":
        #     if event.self_id not in mainbot:
        #         return
        #     if event.group_id in blacklist['ettm']:
        #         return
        #     if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
        #         nowtime = f"{str(datetime.now().hour).zfill(2)}{str(datetime.now().minute).zfill(2)}"
        #         lasttime = gachalimit['lasttime']
        #         count = gachalimit['count']
        #         if nowtime == lasttime and count >= 2:
        #             sendmsg(event, f'技能冷却中，剩余cd:{60 - datetime.now().second}秒（一分钟内所有群只能抽两次）')
        #             return
        #         if nowtime != lasttime:
        #             count = 0
        #         gachalimit['lasttime'] = nowtime
        #         gachalimit['count'] = count + 1
        #     sendmsg(event, '了解')
        #     gachaid = event.message[event.message.find("sekai真抽卡") + len("sekai真抽卡"):].strip()
        #     if gachaid == '':
        #         result = gacha()
        #     else:
        #         currentgacha = getallcurrentgacha()
        #         targetgacha = None
        #         for gachas in currentgacha:
        #             if int(gachas['id']) == int(gachaid):
        #                 targetgacha = gachas
        #                 break
        #         if targetgacha is None:
        #             sendmsg(event, '你指定的id现在无法完成无偿十连')
        #             return
        #         else:
        #             result = gacha(targetgacha)
        #     sendmsg(event, result)
        #     return
        if event.message == "时速":
            texttoimg(ss(), 300, 'ss')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\ss.png,cache=0]")
            return
        if event.message.startswith("时速"):
            charaname = event.message[2:].strip()
            charaid = aliastocharaid(charaname, event.group_id)
            if charaid[0] != 0:
                texttoimg(ss(charaid[0]), 300, 'ss')
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\ss.png,cache=0]")
                return
        if event.message == "sk预测":
            texttoimg(skyc(), 540, 'skyc')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\skyc.png,cache=0]")
            return
        elif msg := re.match('^(?:查询?卡面?|findcard)(.*)', event.message):
            msg = msg.group(1).strip()
            if msg.isdigit():
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/piccache/cardinfo/{getcardinfo(int(msg))},cache=0]")
                return
            para = msg.split(' ')
            resp = aliastocharaid(para[0], event.group_id)
            if resp[0] != 0:
                if len(para) == 1:
                    sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], None)},cache=0]")
                elif len(para) == 2:
                    if para[1] == '一星' or para[1] == '1':
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_1')},cache=0]")
                    elif para[1] == '二星' or para[1] == '2':
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_2')},cache=0]")
                    elif para[1] == '三星' or para[1] == '3':
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_3')},cache=0]")
                    elif para[1] == '四星' or para[1] == '4':
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_4')},cache=0]")
                    elif '生日' in para[1] or 'birthday' in para[1]:
                        sendmsg(event,
                                fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_birthday')},cache=0]")
                    else:
                        sendmsg(event, '命令不正确')
            else:
                sendmsg(event, '找不到你说的角色哦')
            return
        # ---------------------- 服务器判断 -------------------------
        server = 'jp'
        if event.message[:2] == "jp":
            event.message = event.message[2:]
        elif event.message[:2] == "tw":
            event.message = event.message[2:]
            server = 'tw'
        elif event.message[:2] == "en":
            event.message = event.message[2:]
            server = 'en'
        elif event.message[:2] == "kr":
            event.message = event.message[2:]
            server = 'kr'
        # -------------------- 多服共用功能区 -----------------------
        if event.message == "sk线" or event.message == "skline":
            texttoimg(score_line(server), 540, f'score_line_{server}')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\score_line_{server}.png,cache=0]")
            return
        if event.message[:2] == "sk":
            if event.group_id in blacklist['sk'] and server == 'jp':
                return
            if event.message == "sk":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                result = sk(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                if 'piccache' in result:
                    sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                else:
                    sendmsg(event, result)
            else:
                event.message = event.message[event.message.find("sk") + len("sk"):].strip()
                userids = event.message.split(' ')
                if len(userids) > 8:
                    sendmsg(event, '少查一点吧')
                    return
                if len(userids) == 1:
                    userid = event.message.strip()
                    if '[CQ:at' in userid:
                        userid = re.sub(r'\D', "", userid)
                    if not userid.isdigit():
                        # 新增world link单独榜线查询
                        charaid = aliastocharaid(userid, event.group_id)
                        if charaid[0] != 0:
                            bind = getqqbind(event.user_id, server)
                            if bind is None:
                                sendmsg(event, '你没有绑定id！')
                                return
                            result = sk(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id, world_link_chara_id=charaid[0])
                            if 'piccache' in result:
                                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                            else:
                                sendmsg(event, result)
                    try:
                        if int(userid) > 10000000:
                            result = sk(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                        else:
                            result = sk(targetrank=userid, secret=True, server=server, qqnum=event.user_id)
                        if 'piccache' in result:
                            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                        else:
                            sendmsg(event, result)
                        return
                    except ValueError:
                        return
                else:
                    if len(userids) == 2:
                        if not userids[0].isdigit():
                            # 新增world link单独榜线查询
                            charaid = aliastocharaid(userids[0], event.group_id)
                            if charaid[0] != 0:
                                try:
                                    if int(userids[1]) > 10000000:
                                        result = sk(targetid=userids[1], secret=False, server=server, qqnum=event.user_id, world_link_chara_id=charaid[0])
                                    else:
                                        result = sk(targetrank=userids[1], secret=True, server=server, qqnum=event.user_id, world_link_chara_id=charaid[0])
                                    if 'piccache' in result:
                                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                                    else:
                                        sendmsg(event, result)
                                    return
                                except ValueError:
                                    return
                    result = ''
                    for userid in userids:
                        userid = re.sub(r'\D', "", userid)
                        if userid == '':
                            sendmsg(event, '你这id有问题啊')
                            return
                        if int(userid) > 10000000:
                            result += sk(targetid=userid, secret=False, server=server, simple=True, qqnum=event.user_id)
                        else:
                            result += sk(targetrank=userid, secret=True, server=server, simple=True, qqnum=event.user_id)
                        result += '\n\n'
                    sendmsg(event, result[:-2])
                    return
        if event.message[:2] == "绑定":
            userid = event.message.replace("绑定", "").strip()
            try:
                int(userid)
                sendmsg(event, bindid(event.user_id, userid, server))
                return
            except ValueError:
                return
        if event.message == "不给看":
            if setprivate(event.user_id, 1, server):
                sendmsg(event, '不给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message == "给看":
            if setprivate(event.user_id, 0, server):
                sendmsg(event, '给看！')
            else:
                sendmsg(event, '你还没有绑定哦')
            return
        if event.message[:2] == "逮捕":
            if event.group_id in blacklist['sk'] and server == 'jp':
                return
            if event.message == "逮捕":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
                result = daibu(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                sendmsg(event, result)
            else:
                userid = event.message.replace("逮捕", "").strip()
                if userid == '':
                    return
                if '[CQ:at' in userid:
                    qq = re.sub(r'\D', "", userid)
                    bind = getqqbind(qq, server)
                    if bind is None:
                        sendmsg(event, '查不到捏，可能是没绑定')
                        return
                    elif bind[2] and qq != str(event.user_id):
                        sendmsg(event, '查不到捏，可能是不给看')
                        return
                    else:
                        result = daibu(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                        sendmsg(event, result)
                        return
                try:
                    if int(userid) > 10000000:
                        result = daibu(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                    else:
                        # 本来想写逮捕排位排名的 后来忘了 之后有时间看看
                        result = daibu(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                    sendmsg(event, result)
                except ValueError:
                    return
            return
        if event.message == "pjsk进度":
            bind = getqqbind(event.user_id, server)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'master', server, event.user_id)
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message in ["pjsk进度ex", "pjsk进度expert"]:
            bind = getqqbind(event.user_id, server)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'expert', server, event.user_id)
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.message in ["pjsk进度ap", "pjsk进度apd", "pjsk进度append"]:
            bind = getqqbind(event.user_id, server)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'append', server, event.user_id)
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if re.match('^pjsk *b30$', event.message):
            bind = getqqbind(event.user_id, server)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskb30(userid=bind[1], private=bind[2], server=server, qqnum=event.user_id)
            sendmsg(event, fr"同等级下已按实装顺序排序[CQ:image,file=file:///{botdir}\piccache\{bind[1]}b30.jpg,cache=0]")
            return
        if msg := re.match('^pjsk *r30(.*)', event.message):
            # 给冲色段的朋友打5v5看对手情况用的 不冲5v5色段看这个没用
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            userid = msg.group(1).strip()
            if not userid:
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '查不到捏，可能是没绑定')
                    return
            else:
                bind = (1, userid, False)
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{r30(bind[1], bind[2], server, event.user_id)}.png,cache=0]")
            return
        if event.message == "pjskprofile" or event.message == "个人信息":
            bind = getqqbind(event.user_id, server)
            if bind is None:
                sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskprofile(bind[1], bind[2], server, event.user_id, is_force_update=True)
            sendmsg(event, f"[CQ:image,file=file:///{botdir}/piccache/{bind[1]}profile.jpg,cache=0]")
            return
        if event.message[:2] == "查房" or event.message[:2] == "cf":
            if event.group_id in blacklist['sk'] and event.message[:2] == "查房":
                return
            if event.message[:2] == "cf":
                event.message = '查房' + event.message[2:]
            private = False
            if event.message == "查房":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
                private = bind[2]
            else:
                userid = event.message.replace("查房", "").strip()
            try:
                if int(userid) > 10000000:
                    result = chafang(targetid=userid, private=private, server=server)
                else:
                    result = chafang(targetrank=userid, server=server)
                sendmsg(event, result)
                return
            except ValueError:
                return
        graphstart = 0
        if event.message[:4] == '24小时':
            graphstart = time.time() - 60 * 60 * 24
            event.message = event.message[4:]
        if event.message[:3] == "分数线":
            try:
                if event.message == "分数线":
                    bind = getqqbind(event.user_id, server)
                    if bind is None:
                        sendmsg(event, '你没有绑定id！')
                        return
                    userid = bind[1]
                else:
                    userid = event.message.replace("分数线", "")
                if userid == '':
                    return
                userids = userid.split(' ')
                if len(userids) == 1:
                    userid = userid.strip()
                    try:
                        if int(userid) > 10000000:
                            result = drawscoreline(userid, starttime=graphstart, server=server)
                        else:
                            result = drawscoreline(targetrank=userid, starttime=graphstart, server=server)
                        if result:
                            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                        else:
                            sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                        return
                    except ValueError:
                        return
                else:
                    result = drawscoreline(targetrank=userids[0], targetrank2=userids[1], starttime=graphstart, server=server)
                    if result:
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                    else:
                        sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                    return
            except:
                return
        if event.message[:3] == "查水表" or event.message[:3] == "csb":
            if event.group_id in blacklist['sk'] and event.message[:3] == "查水表":
                return
            if event.message[:3] == "csb":
                event.message = '查水表' + event.message[3:]
            private = False
            if event.message == "查水表":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
                private = bind[2]
            else:
                userid = event.message.replace("查水表", "").strip()
            try:
                if int(userid) > 10000000:
                    result = getstoptime(userid, private=private, server=server)
                else:
                    result = getstoptime(targetrank=userid, server=server)
                if result:
                    img = text2image(result, max_width=1000, padding=(30, 30))
                    img.save(f"piccache\csb{userid}.png")
                    sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\csb{userid}.png,cache=0]")
                else:
                    sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                return
            except ValueError:
                return
        if event.message == '5v5人数':
            sendmsg(event, teamcount(server).replace('3-3.dev', '3-3点dev'))
        if event.message[:2] == "rk":
            if event.message == "rk":
                bind = getqqbind(event.user_id, server=server)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                result = rk(bind[1], None, bind[2], server=server)
                sendmsg(event, result)
            else:
                userid = event.message.replace("rk", "").strip()
                try:
                    if int(userid) > 10000000:
                        result = rk(userid, server=server)
                    else:
                        result = rk(None, userid, server=server)
                    sendmsg(event, result)
                except ValueError:
                    return
            return
        # ----------------------- 恢复原命令 ---------------------------
        if server != 'jp':
            event.message = server + event.message
        # -------------------- 结束多服共用功能区 -----------------------
        if re.match('^活动(?:图鉴|列表|总览)|^findevent *all', event.message):
            sendmsg(event, fr"[CQ:image,file=file:///{findevent()},cache=0]")
            return
        if msg := re.match('^(?:findevent|查询?活动)(.*)', event.message):
            arg = msg.group(1).strip()
            if not arg:
                tipdir = r'pics/findevent_tips.jpg'
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{tipdir},cache=0]")
            elif arg.isdigit():
                try:
                    if picdir := geteventpic(int(arg)):
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    else:
                        tipdir = r'pics/findevent_tips.jpg'
                        sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{tipdir},cache=0]")
                    return
                except ValueError:
                    traceback.print_exc()
                    sendmsg(event, f"未找到活动或生成失败")
                    return
                except FileNotFoundError:
                    traceback.print_exc()
                    sendmsg(event, f"未找到活动资源图片，请等待更新")
                    return
            else:
                sendmsg(event, fr"[CQ:image,file=file:///{findevent(arg)},cache=0]")
            return
        if event.message[:5] == 'event':
            eventid = event.message[event.message.find("event") + len("event"):].strip()
            try:
                if eventid == '':
                    picdir = geteventpic(None)
                else:
                    try:
                        picdir = geteventpic(int(eventid))
                    except ValueError:
                        return
            except FileNotFoundError:
                traceback.print_exc()
                sendmsg(event, f"未找到活动资源图片，请等待更新")
                return
            if picdir:
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
            else:
                sendmsg(event, f"未找到活动或生成失败")
            return
        try:
            if event.message[:4] == "难度排行" or event.message[2:6] == "难度排行" or event.message[-4:] == "难度排行":
                fcap = 0
                diff = 'master'
                if 'append' in event.message or 'apd' in event.message:
                    diff = 'append'
                elif 'expert' in event.message or 'ex' in event.message:
                    diff = 'expert'
                elif 'hard' in event.message or 'hd' in event.message:
                    diff = 'hard'
                elif 'normal' in event.message or 'nm' in event.message:
                    diff = 'normal'
                elif 'easy' in event.message or 'ez' in event.message:
                    diff = 'easy'
                try:
                    level = int(re.sub(r'\D', "", event.message))
                except:
                    if event.message == '难度排行' or fcap in [1, 2] or diff in ['append', 'expert', 'hard', 'normal', 'easy']:
                        level = 0
                    else:
                        return
                bind = getqqbind(event.user_id, server)

                if bind is not None:
                    picdir = levelRankPic(level, diff, fcap, userid=bind[1], isprivate=bind[2], qqnum=event.user_id)
                else:
                    picdir = levelRankPic(level, diff, fcap,)
                sendmsg(event, f"[CQ:image,file=file:///{botdir}/{picdir},cache=0]")

                return
        except:
            traceback.print_exc()
            sendmsg(event, '参数错误或无此难度（默认master），指令：/难度排行 定数 难度，'
                           '难度支持的输入: easy, normal, hard, expert, master，如/难度排行 28 expert /ap难度排行 28 expert')

        if event.message[:7] == 'pjskbpm' or (event.message[:3] == 'bpm' and event.self_id == guildbot):
            parm = event.message[event.message.find("bpm") + len("bpm"):].strip()
            resp = aliastomusicid(parm)
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                bpm = parse_bpm(resp['musicid'])
                text = ''
                for bpms in bpm[1]:
                    text = text + ' - ' + str(bpms['bpm']).replace('.0', '')
                text = f"{resp['name']}\n匹配度:{round(resp['match'], 4)}\nBPM: " + text[3:]
                sendmsg(event, text)
            return
        if "谱面预览2" in event.message:
            picdir = aliastochart(event.message.replace("谱面预览2", ''), True)
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    sendmsg(event, picdir[0] + fr"[CQ:image,file=file:///{botdir}\{picdir[1]},cache=0]")
                else:
                    sendmsg(event, picdir + "\n暂无谱面图片 请等待更新"
                                            "\n（温馨提示：谱面预览2只能看master与expert）")
            else:  # 匹配不到歌曲
                sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.message[:8] == 'cardinfo':
            cardid = event.message[event.message.find("cardinfo") + len("cardinfo"):].strip()
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}/piccache/cardinfo/{getcardinfo(int(cardid))},cache=0]")
            return
        if event.message[:4] == 'card':
            cardid = event.message[event.message.find("card") + len("card"):].strip()
            pics = cardidtopic(int(cardid))
            print(pics)
            for pic in pics:
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{pic},cache=0]")
            return
        if event.message[:4] == "谱面预览" or event.message[-4:] == "谱面预览" :
            qun = True
            if event.self_id == guildbot:
                qun = False
            try:
                picdir = aliastochart(event.message.replace("谱面预览", ''), False, qun, getcharttheme(event.user_id))
            except FileNotFoundError:
                sendmsg(event, '没有找到你要的难度')
                return
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    if event.self_id == guildbot:
                        sendmsg(event, picdir[0] + f"\niOS如果图片糊，请将QQ更新到最新版本（9开头），安卓需在群内使用官方bot才能查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                    else:
                        sendmsg(event, picdir[0] + f"\niOS保存后即可查看原图，安卓使用官方Bot才可查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                elif picdir == '':
                    sendmsg(event, f'[CQ:poke,qq={event.user_id}]')
                    return
                else:
                    sendmsg(event, picdir + "\n暂无谱面图片 请等待更新")
            else:  # 匹配不到歌曲
                sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.message[:5] == "theme":
            theme = event.message[event.message.find("theme") + len("theme"):].strip()
            sendmsg(event, setcharttheme(event.user_id, theme))
            return
        if event.message[:3] == "查时间":
            userid = event.message[event.message.find("查时间") + len("查时间"):].strip()
            if userid == '':
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
            userid = re.sub(r'\D', "", userid)
            if userid == '':
                sendmsg(event, '你这id有问题啊')
                return
            if verifyid(userid):
                sendmsg(event, time.strftime('注册时间：%Y-%m-%d %H:%M:%S',
                                             time.localtime(gettime(userid))))
            else:
                sendmsg(event, '你这id有问题啊')
            return
        if event.message[:8] == 'charaset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[8:]
            para = event.message.split('to')
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                sendmsg(event,
                        charaset(para[0], para[1], event.user_id, username, f"{qun['name']}({event.guild_id})内", is_hide=True))
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                sendmsg(event, charaset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.message.startswith('封禁查询'):
            userid = event.message[4:]
            sendmsg(event, cheater_ban_reason(userid))
            return
        if event.message[:10] == 'grcharaset' and 'to' in event.message:
            event.message = event.message[10:]
            para = event.message.split('to')
            if event.self_id == guildbot:
                sendmsg(event, grcharaset(para[0], para[1], event.guild_id, is_hide=True))
            else:
                sendmsg(event, grcharaset(para[0], para[1], event.group_id))
            return
        if event.message[:8] == 'charadel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[8:]
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                sendmsg(event,
                        charadel(event.message, event.user_id, username, f"{qun['name']}({event.guild_id})内"))
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                sendmsg(event, charadel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.message[:10] == 'grcharadel':
            event.message = event.message[10:]
            if event.self_id == guildbot:
                sendmsg(event, grcharadel(event.message, event.guild_id))
            else:
                sendmsg(event, grcharadel(event.message, event.group_id))
            return
        if event.message[:9] == 'charainfo':
            if event.self_id == guildbot:
                sendmsg(event, '频道bot不支持此功能')
                return
            event.message = event.message[9:]
            if event.self_id == guildbot:
                sendmsg(event, charainfo(event.message, event.guild_id))
            else:
                sendmsg(event, charainfo(event.message, event.group_id))
            return
        if event.message[:5] == "白名单添加" and event.user_id in whitelist:
            event.message = event.message[event.message.find("白名单添加") + len("白名单添加"):].strip()
            requestwhitelist.append(int(event.message))
            sendmsg(event, '添加成功: ' + event.message)
            return
        if event.message[:3] == "达成率":
            event.message = event.message[event.message.find("达成率") + len("达成率"):].strip()
            para = event.message.split(' ')
            if len(para) < 5:
                return
            sendmsg(event, tasseiritsu(para))
            return
        if event.message[:4] == '封面匹配':
            global opencvmatch
            if not opencvmatch:
                try:
                    opencvmatch = True
                    sendmsg(event, f'[CQ:reply,id={event.message_id}]了解，查询中（局部封面图匹配歌曲，输出只对有效输入负责，多次有意输入无效图片核实后将会拉黑）')
                    url = event.message[event.message.find('url=') + 4:event.message.find(']')]
                    title, picdir = matchjacket(url=url)
                    if title:
                        if 'assets' in picdir:
                            sendmsg(event, f"[CQ:reply,id={event.message_id}]匹配点过少，该曲为最有可能匹配的封面：\n" + fr"{title}[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                        else:
                            sendmsg(event, fr"[CQ:reply,id={event.message_id}]{title}[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    else:
                        sendmsg(event, f'[CQ:reply,id={event.message_id}]找不到捏')
                except Exception as a:
                    traceback.print_exc()
                    sendmsg(event, '出问题了捏\n' + repr(a))
                opencvmatch = False
            else:
                sendmsg(event, f'当前有正在匹配的进程，请稍后再试')
            return
        if event.message[:3] == '查物量':
            sendmsg(event, notecount(int(event.message[3:])))
            return
        if event.message[:4] == '查bpm':
            sendmsg(event, findbpm(int(event.message[4:])))
            return
        if event.message[-3:] == '排行榜':
            if event.message.startswith('pjsk猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(1, 'pjsk猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk阴间猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(2, 'pjsk阴间猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk猜谱面'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(3, 'pjsk猜谱面', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk猜卡面'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(4, 'pjsk猜卡面', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk听歌猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(5, 'pjsk听歌猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk倒放猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(6, 'pjsk倒放猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('ai猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(7, 'ai猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('ai猜卡面'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(8, 'ai猜卡面', event.user_id)},cache=0]")
                return
            if event.message.startswith('ai阴间猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(9, 'ai阴间猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk音效猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(10, 'pjsk音效猜曲', event.user_id)},cache=0]")
                return
            if event.message.startswith('pjsk歌词猜曲'):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}/{guessRank(11, 'pjsk歌词猜曲', event.user_id)},cache=0]")
                return
        if event.message[:1] == '看' or event.message[:2] == '来点':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            event.message = event.message.replace('看', '', 1)
            event.message = event.message.replace('来点', '', 1)
            resp = aliastocharaid(event.message, event.group_id)
            if resp[0] != 0:
                cardurl = get_card(resp[0])
                if 'cutout' not in cardurl:
                    cardurl = cardurl.replace('png', 'jpg')
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{cardurl},cache=0]")
            return
        if 'pjsk抽卡' in event.message or 'sekai抽卡' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            gachaid = event.message[event.message.find("抽卡") + len("抽卡"):].strip()
            gachaid = re.sub(r'\D', "", gachaid)
            if gachaid == '':
                currentgacha = getcurrentgacha()
                msg = fakegacha(int(currentgacha['id']), 10, False, True)
            else:
                msg = fakegacha(int(gachaid), 10, False, True)
            sendmsg(event, msg[0] + fr"[CQ:image,file=file:///{botdir}\{msg[1]},cache=0]")
            return
        if 'pjsk反抽卡' in event.message or 'sekai反抽卡' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            gachaid = event.message[event.message.find("抽卡") + len("抽卡"):].strip()
            gachaid = re.sub(r'\D', "", gachaid)
            if gachaid == '':
                currentgacha = getcurrentgacha()
                msg = fakegacha(int(currentgacha['id']), 10, True, True)
            else:
                msg = fakegacha(int(gachaid), 10, True, True)
            sendmsg(event, msg[0] + fr"[CQ:image,file=file:///{botdir}\{msg[1]},cache=0]")
            return
        if (event.message[0:5] == 'sekai' or event.message[0:4] == 'pjsk') and '连' in event.message:
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            gachaid = event.message[event.message.find("连") + len("连"):].strip()
            num = event.message[:event.message.find('连')].replace('sekai', '').replace('pjsk', '')
            num = re.sub(r'\D', "", num)
            if int(num) > 200:
                sendmsg(event, '太多了，少抽一点吧！')
                return
            if gachaid == '':
                currentgacha = getcurrentgacha()
                sendmsg(event, fakegacha(int(currentgacha['id']), int(num), False))
            else:
                sendmsg(event, fakegacha(int(gachaid), int(num), False))
            return
        if event.message == '更新日志' and event.user_id in admin:
            writelog()
            sendmsg(event, '更新成功')
            return
        if event.message.startswith('qiu 绑定') or event.message.startswith('qiu绑定'):
            userid = event.message.replace(' ', '').replace(f"qiu绑定", "").strip()
            try:
                int(userid)
            except ValueError:
                sendmsg(event, '卡号应为20位纯数字')
                return
            if len(userid) != 20:
                sendmsg(event, '卡号应为20位纯数字')
                return
            sendmsg(event, qiu_bind_aimeid(event.user_id, userid))
            return
        if event.message in ['qiu b30', 'qiub30', 'qiu b30 lmn', 'qiub30 lmn']:
            bind = getqiubind(event.user_id)
            if bind is None:
                sendmsg(event, f'查不到捏，可能是没绑定，绑定命令：qiu 绑定xxxxx')
                return
            qiu_dir = qiub30(userid=bind, qqnum=event.user_id)
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{qiu_dir},cache=0]")
            return
        def handle_bind(event, command, server=None):
            userid = event.message.replace(' ', '').replace(f"{command}绑定", "").strip()
            try:
                int(userid)
            except ValueError:
                traceback.print_exc()
                sendmsg(event, '卡号应为20位纯数字')
                return
            if len(userid) != 20:
                sendmsg(event, '卡号应为20位纯数字')
                return
            sendmsg(event, bind_aimeid(event.user_id, userid, server))

        def handle_b30(event, command, server=None, version=None):
            bind = getchunibind(event.user_id, server)
            if bind is None:
                sendmsg(event, f'查不到捏，可能是没绑定，绑定命令：{command} 绑定xxxxx')
                return
            b30_dir = chunib30(userid=bind, server=server, version=version, qqnum=event.user_id)
            if re.match(f'^{command} *b30 lmn$', event.message):
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{b30_dir},cache=0]" + '\n查Luminous定数已无需添加lmn')
            else:
                sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{b30_dir},cache=0]")

        commands = [("aqua", "aqua"), ("Super", 'super'), ("super", 'super'), ("林先生", 'lin'),
                     ("na", 'na'), ("lee", 'na'), ("lin", 'lin'), ("rin", "rin"), ("mai", "mobi"), ('mobi', 'mobi')]

        for command, server in commands:
            if event.message.startswith(f"{command} 绑定") or event.message.startswith(f"{command}绑定"):
                handle_bind(event, command, server)
                return
            elif re.match(f'^{command} *b30$', event.message):
                handle_b30(event, command, server, version='2.15')
                return
            elif re.match(f'^{command} *b30 lmn$', event.message):
                handle_b30(event, command, server, version='2.20')
                return
            # elif re.match(f'^{command} *b30 lmnp$', event.message):
            #     handle_b30(event, command, server, version='2.20')
            #     return
    
        # if event.message in ['aqua 中二签到', 'knd 中二签到']:
        #     bind = getchunibind(event.user_id)
        #     if bind is None:
        #         sendmsg(event, '签到不了捏，可能是没绑定，绑定命令：aqua 绑定xxxxx')
        #         return
        #     sendmsg(event, chuni_signin(str(event.user_id), str(bind)))
        #     return
        # if event.message in ['lin 中二签到']:
        #     bind = getchunibind(event.user_id, server='lin')
        #     if bind is None:
        #         sendmsg(event, '签到不了捏，可能是没绑定，绑定命令：lin 绑定xxxxx')
        #         return
        #     sendmsg(event, chuni_signin_lin(str(event.user_id), str(bind)))
        #     return
        if msg := re.match('(?:chusearch)(.*)', event.message):
            query = msg.group(1).strip()
            # 使用查询字符串搜索歌曲
            resp = search_song(query)
            sendmsg(event, resp)
            return
        if msg := re.match('(?:chuinfo)(.*)', event.message):
            song_id = msg.group(1).strip()
            info, image_url = song_details(song_id)
            if image_url is None:
                sendmsg(event, '没有找到你要的歌曲哦')
            else:
                # 输出歌曲信息和图片
                sendmsg(event, info + fr"[CQ:image,file=file:///{botdir}/{image_url},cache=0]")
            return
        if msg := re.match(r'chulevel\s*(\d+\+?)(?:\s+(\w+))?', event.message):
            print(event.message)
            # 获取第一个参数（难度）
            diff = msg.group(1).strip()

            # 检查是否有第二个参数（服务器）
            if server := msg.group(2):
                server_mapping = next((mapping[1] for mapping in commands if mapping[0] == server), None)
                if server_mapping:
                    server = server_mapping
                else:
                    sendmsg(event, '服务器不支持，仅支持aqua，rin，na')
                    return
                # 如果有第二个参数，获取用户ID
                userid = getchunibind(event.user_id, server=server)
                if userid is None:
                    sendmsg(event, f'查不到捏，可能是没绑定，绑定命令：{server} 绑定xxxxx')
                    return
                output_dir = chu_level_rank(diff, userid, server, qqnum=event.user_id)
            else:
                # 如果没有第二个参数，像之前一样调用函数
                output_dir = chu_level_rank(diff)

            sendmsg(event, f"[CQ:image,file=file:///{botdir}/{output_dir},cache=0]")
            return
        if event.message.startswith('chuchart'):
            difficulty = "master"
            if event.message.lower().endswith(("ma", "master")):
                difficulty = "master"
            elif event.message.lower().endswith(("expert", "ex")):
                difficulty = "expert"
            elif event.message.lower().endswith(("ultima", "ult")):
                difficulty = "ultima"
            # 提取musicid
            musicid = re.sub(r"chuchart|\s+", "", event.message, flags=re.I)
            musicid = re.sub(r"(ma|master|expert|ex|ultima|ult)$", "", musicid, flags=re.I)

            # 获取图像并发送
            result = get_chunithm_chart(musicid, difficulty)
            if result is not None:
                title, image_url, match = result
                if event.self_id == guildbot:
                    info = f"{title} {difficulty.upper()}\n匹配度：{round(match, 4)}\n谱面来自sdvx点in\niOS如果图片糊，请将QQ更新到最新版本（9开头），安卓需在群内使用官方bot才能查看原图"
                else:
                    info = f"{title} {difficulty.upper()}\n匹配度：{round(match, 4)}\n谱面来自sdvx点in\niOS保存后即可查看原图，安卓使用官方Bot才可查看原图"
                sendmsg(event, info + fr"[CQ:image,file=file:///{botdir}/{image_url},cache=0]")
            else:
                sendmsg(event, "抱歉，无法生成图像。")
        if event.message[:6] == 'chuset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[6:]
            para = event.message.split('to')
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = chuset(para[0], para[1], event.user_id, username, f"{qun['name']}({event.guild_id})内", is_hide=True)
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = chuset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:6] == 'chudel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[6:]
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = chudel(event.message, event.user_id, username, f"{qun['name']}({event.guild_id})内")
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = chudel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:8] == 'chualias':
            if event.self_id == guildbot:
                sendmsg(event, '频道bot不支持此功能')
                return
            event.message = event.message[8:]
            resp = chualias(event.message)
            sendmsg(event, resp)
            return
        # wds
        if msg := re.match('(?:wdsinfo|wdssong?)(.*)', event.message):
            resp = wds_alias_to_music_id(msg.group(1).strip())
            if resp['musicid'] == 0:
                sendmsg(event, '没有找到你要的歌曲哦')
                return
            else:
                data = wdsinfo(resp['musicid'])
                if data[0]:
                    sendmsg(event,
                        data[1] + f'\n匹配度：{round(resp["match"], 4)}\n' + data[3] + fr"[CQ:image,file=file:///{botdir}/{data[2]},cache=0]")
                else:
                    sendmsg(event, data[1])
            return
        if event.message[:6] == 'wdsset' and 'to' in event.message:
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[6:]
            para = event.message.split('to')
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = wdsset(para[0], para[1], event.user_id, username, f"{qun['name']}({event.guild_id})内", is_hide=True)
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = wdsset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:6] == 'wdsdel':
            if event.user_id in aliasblock:
                sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.message = event.message[6:]
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                resp = wdsdel(event.message, event.user_id, username, f"{qun['name']}({event.guild_id})内")
                sendmsg(event, resp)
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                resp = wdsdel(event.message, event.user_id, username, f"{qun['group_name']}({event.group_id})内")
                sendmsg(event, resp)
            return
        if event.message[:8] == 'wdsalias':
            if event.self_id == guildbot:
                sendmsg(event, '频道bot不支持此功能')
                return
            event.message = event.message[8:]
            resp = wdsalias(event.message)
            sendmsg(event, resp)
            return
        if event.message.startswith("wdschart"):
            qun = True
            if event.self_id == guildbot:
                qun = False
            picdir = wds_alias_to_chart(event.message.replace("wdschart", ''), qun)
            if picdir is False:
                sendmsg(event, "谱面预览暂未更新")
                return
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    if event.self_id == guildbot:
                        sendmsg(event, picdir[0].replace('estertion.win', 'estertion点win') + f"\niOS如果图片糊，请将QQ更新到最新版本（9开头），安卓需在群内使用官方bot才能查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                    else:
                        sendmsg(event, picdir[0].replace('estertion.win', 'estertion点win') + f"\niOS保存后即可查看原图，安卓使用官方Bot才可查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                elif picdir == '':
                    sendmsg(event, f'[CQ:poke,qq={event.user_id}]')
                    return
                else:
                    sendmsg(event, picdir + "\n暂无谱面图片 请等待更新")
            else:  # 匹配不到歌曲
                sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.message == "wds线":
            texttoimg(wds_score_line(), 540, 'wds_score_line')
            sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\wds_score_line.png,cache=0]")
            return
        # 猜曲
        if event.message == 'pjsk猜谱面' or event.message == 'pjsk猜曲 3':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜卡面！')
                    return
            except KeyError:
                pass

            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    musicid = getrandomchart()
                    pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'type': 3,
                                                 'starttime': int(time.time()), 'selfid': event.self_id}
            except KeyError:
                musicid = getrandomchart()
                pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'type': 3,
                                             'starttime': int(time.time()), 'selfid': event.self_id}
            cutchartimg(musicid, event.group_id)
            sendmsg(event, 'PJSK谱面竞猜（随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            return
        if event.message == '给点提示' or event.message == '来点提示':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    if random.random() < 0.5:
                        if os.path.exists(f'moesus/lyrics/{pjskguess[event.group_id]["musicid"]}.txt'):
                            lines = get_two_lines(f'moesus/lyrics/{pjskguess[event.group_id]["musicid"]}.txt')
                            if lines is not None:
                                sendmsg(event, f'歌词节选：\n' + lines)
                                return
                    playLevel = getPlayLevel(pjskguess[event.group_id]['musicid'], 'master')
                    sendmsg(event, f'难度是{playLevel}哦')
                    return
            except:
                pass
            sendmsg(event, '当前没有猜曲哦')
            return
        if event.message == 'pjsk阴间猜谱面':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜卡面！')
                    return
            except KeyError:
                pass

            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    musicid = getrandomchartold()
                    pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'type': 3,
                                                 'starttime': int(time.time()), 'selfid': event.self_id}
            except KeyError:
                musicid = getrandomchartold()
                pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'type': 3,
                                             'starttime': int(time.time()), 'selfid': event.self_id}
            cutchartimgold(musicid, event.group_id)
            sendmsg(event, 'PJSK谱面竞猜（随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            return
        if event.message == 'pjsk猜卡面' or event.message == 'pjsk猜曲 4':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
            except KeyError:
                pass
            # getrandomcard() return characterId, assetbundleName, prefix, cardRarityType
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    cardinfo = getrandomcard()
                    charaguess[event.group_id] = {'isgoing': True, 'charaid': cardinfo[0],
                                                  'assetbundleName': cardinfo[1], 'prefix': cardinfo[2],
                                                  'starttime': int(time.time()), 'selfid': event.self_id, 'type': 1}
            except KeyError:
                cardinfo = getrandomcard()
                charaguess[event.group_id] = {'isgoing': True, 'charaid': cardinfo[0],
                                              'assetbundleName': cardinfo[1],
                                              'prefix': cardinfo[2], 'starttime': int(time.time()),
                                               'selfid': event.self_id, 'type': 1}

            charaguess[event.group_id]['istrained'] = cutcard(cardinfo[1], cardinfo[3], event.group_id)
            sendmsg(event, 'PJSK猜卡面\n你有30秒的时间回答\n艾特我+你的答案（只猜角色）以参加猜曲（不要使用回复）\n发送「结束猜卡面」可退出猜卡面模式'
                    + fr"[CQ:image,file=file:///{botdir}\piccache/{event.group_id}.png,cache=0]")
            return
        if (event.message[-2:] == '猜曲' or event.message[-4:-2] == '猜曲') and event.message[:4] == 'pjsk':
            if event.user_id not in whitelist and event.group_id not in whitelist and event.self_id != guildbot:
                return
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜卡面！')
                    return
            except KeyError:
                pass

            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    sendmsg(event, '已经开启猜曲！')
                    return
                else:
                    if event.message == 'pjsk听歌猜曲' or event.message == 'pjsk倒放猜曲':
                        musicid, assetbundleName = getrandommusic()
                    elif event.message == 'pjsk音效猜曲':
                        musicid = getRandomSE()
                    elif event.message == 'pjsk歌词猜曲' or event.message == 'pjsk猜曲 5':
                        musicid, lyrics = random_lyrics()
                    else:
                        musicid = getrandomjacket()
                    pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid,
                                                 'starttime': int(time.time()), 'selfid': event.self_id}
            except KeyError:
                if event.message == 'pjsk听歌猜曲' or event.message == 'pjsk倒放猜曲':
                    musicid, assetbundleName = getrandommusic()
                elif event.message == 'pjsk音效猜曲':
                    musicid = getRandomSE()
                elif event.message == 'pjsk歌词猜曲' or event.message == 'pjsk猜曲 5':
                    musicid, lyrics = random_lyrics()
                else:
                    musicid = getrandomjacket()
                pjskguess[event.group_id] = {'isgoing': True, 'musicid': musicid, 'starttime': int(time.time()), 'selfid': event.self_id}

            if event.message == 'pjsk猜曲':
                cutjacket(musicid, event.group_id, size=140, isbw=False)
                guessType = 1
            elif event.message == 'pjsk阴间猜曲' or event.message == 'pjsk猜曲 2':
                cutjacket(musicid, event.group_id, size=140, isbw=True)
                guessType = 2
            elif event.message == 'pjsk非人类猜曲':
                cutjacket(musicid, event.group_id, size=30, isbw=False)
                guessType = 2
            elif event.message == 'pjsk听歌猜曲':
                if event.self_id == guildbot:
                    sendmsg(event, "频道bot不支持发送语音，请在开放该功能的群内游玩")
                    return
                cutmusic(assetbundleName, event.group_id)
                sendmsg(event, 'PJSK听歌识曲竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲')
                sendmsg(event, fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}.mp3,cache=0]")
                guessType = 5
                pjskguess[event.group_id]['type'] = guessType
                return
            elif event.message == 'pjsk倒放猜曲':
                if event.self_id == guildbot:
                    sendmsg(event, "频道bot不支持发送语音，请在开放该功能的群内游玩")
                    return
                cutmusic(assetbundleName, event.group_id, True)
                sendmsg(event, 'PJSK倒放识曲竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲')
                sendmsg(event, fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}.mp3,cache=0]")
                guessType = 6
                pjskguess[event.group_id]['type'] = guessType
                return
            elif event.message == 'pjsk音效猜曲':
                if event.self_id == guildbot:
                    sendmsg(event, "频道bot不支持发送语音，请在开放该功能的群内游玩")
                    return
                cutSE(musicid, event.group_id)
                playLevel = getPlayLevel(musicid, 'master')
                if playLevel >= 33:
                    playLevel = '33+'
                sendmsg(event, f'PJSK纯音效识曲竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有90秒的时间回答\n可手动发送“结束猜曲”来结束猜曲\n难度是{playLevel}哦')
                sendmsg(event, fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}.mp3,cache=0]")
                guessType = 10
                pjskguess[event.group_id]['type'] = guessType
                pjskguess[event.group_id]['starttime'] = int(time.time()) + 40
                return
            elif event.message == 'pjsk歌词猜曲' or event.message == 'pjsk猜曲 5':
                sendmsg(event, 'PJSK歌词竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲\n\n' + lyrics)
                guessType = 11
                pjskguess[event.group_id]['type'] = guessType
                return
            else:
                cutjacket(musicid, event.group_id, size=140, isbw=False)
                guessType = 1
            pjskguess[event.group_id]['type'] = guessType
            sendmsg(event, 'PJSK曲绘竞猜 （随机裁切）\n艾特我+你的答案以参加猜曲（不要使用回复）\n\n你有50秒的时间回答\n可手动发送“结束猜曲”来结束猜曲'
                    + fr"[CQ:image,file=file:///{botdir}/piccache/{event.group_id}.png,cache=0]")
            return

        if event.message == '结束猜曲':
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    picdir = f"data/assets/sekai/assetbundle/resources/startapp/music/jacket/" \
                             f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}/" \
                             f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}.png"
                    text = '正确答案：' + idtoname(pjskguess[event.group_id]['musicid'])
                    pjskguess[event.group_id]['isgoing'] = False
                    sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    if pjskguess[event.group_id]['type'] == 10:
                        if event.self_id == guildbot:
                            from modules.ossupload import aliyunOSSUpload
                            sendmsg(event, '混合版(两分钟内有效):\n' + aliyunOSSUpload(f'piccache/{event.group_id}mix.mp3',
                                                                              f'voice/{event.group_id}mix.mp3'))
                        else:
                            sendmsg(event, fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}mix.mp3,cache=0]")
            except KeyError:
                pass
            return
        if event.message == '结束猜卡面':
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    try:
                        if charaguess[event.group_id]['istrained']:
                            picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                     f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_after_training.jpg"
                        else:
                            picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                     f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_normal.jpg"
                        text = f"正确答案：{charaguess[event.group_id]['prefix']} - {getcharaname(charaguess[event.group_id]['charaid'])}"
                        charaguess[event.group_id]['isgoing'] = False

                        sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    except:
                        charaguess[event.group_id]['isgoing'] = False
                        sendmsg(event, "猜卡面出现问题已结束")
            except KeyError:
                pass
            return
        # 判断艾特自己
        if event.message[:len(f'[CQ:at,qq={event.self_id}]')] == f'[CQ:at,qq={event.self_id}]' or event.self_id == guildbot:
            # 判断有没有猜曲
            try:
                isgoing = pjskguess[event.group_id]['isgoing']
                if isgoing:
                    answer = event.message[event.message.find("]") + len("]"):].strip()
                    resp = aliastomusicid(answer)
                    if resp['musicid'] == 0:
                        sendmsg(event, '没有找到你说的歌曲哦')
                        return
                    else:
                        if resp['musicid'] == pjskguess[event.group_id]['musicid']:
                            text = f'[CQ:at,qq={event.user_id}] 您猜对了'
                            if int(time.time()) > pjskguess[event.group_id]['starttime'] + 50:
                                text = text + '，回答已超时'
                            else:
                                if event.sender['card'] == '':
                                    username = event.sender['nickname']
                                else:
                                    username = event.sender['card']
                                recordGuessRank(event.user_id, username, pjskguess[event.group_id]['type'])
                            picdir = f"data/assets/sekai/assetbundle/resources/startapp/music/jacket/" \
                                     f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}/" \
                                     f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}.png"
                            text = text + '\n正确答案：' + idtoname(pjskguess[event.group_id]['musicid'])
                            pjskguess[event.group_id]['isgoing'] = False
                            sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                            if pjskguess[event.group_id]['type'] == 10:
                                if event.self_id == guildbot:
                                    from modules.ossupload import aliyunOSSUpload
                                    sendmsg(event,
                                            '混合版(两分钟内有效):\n' + aliyunOSSUpload(f'piccache/{event.group_id}mix.mp3',
                                                                               f'voice/{event.group_id}mix.mp3'))
                                else:
                                    sendmsg(event, fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}mix.mp3,cache=0]")
                        else:
                            text = f"[CQ:at,qq={event.user_id}] 您猜错了，答案不是{idtoname(resp['musicid'])}哦"
                            if int(time.time()) > pjskguess[event.group_id]['starttime'] + 55:
                                text = text + '，回答已超时'
                                picdir = f"data/assets/sekai/assetbundle/resources/startapp/music/jacket/" \
                                         f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}/" \
                                         f"jacket_s_{str(pjskguess[event.group_id]['musicid']).zfill(3)}.png"
                                text = text + '\n正确答案：' + idtoname(pjskguess[event.group_id]['musicid']) + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]"
                                pjskguess[event.group_id]['isgoing'] = False
                                sendmsg(event, text)
                                if pjskguess[event.group_id]['type'] == 10:
                                    if event.self_id == guildbot:
                                        from modules.ossupload import aliyunOSSUpload
                                        sendmsg(event,
                                                '混合版(两分钟内有效):\n' + aliyunOSSUpload(f'piccache/{event.group_id}mix.mp3',
                                                                                   f'voice/{event.group_id}mix.mp3'))
                                    else:
                                        sendmsg(event,
                                                fr"[CQ:record,file=file:///{botdir}/piccache/{event.group_id}mix.mp3,cache=0]")
                            else:
                                sendmsg(event, text)
                    return
            except KeyError:
                pass
            # 判断有没有猜卡面
            try:
                isgoing = charaguess[event.group_id]['isgoing']
                if isgoing:
                    # {'isgoing', 'charaid', 'assetbundleName', 'prefix', 'starttime'}
                    answer = event.message[event.message.find("]") + len("]"):].strip()
                    if event.self_id == guildbot:
                        resp = aliastocharaid(answer, event.guild_id)
                    else:
                        resp = aliastocharaid(answer, event.group_id)
                    if resp[0] == 0:
                        sendmsg(event, '没有找到你说的角色哦')
                        return
                    else:
                        if resp[0] == charaguess[event.group_id]['charaid']:
                            text = f'[CQ:at,qq={event.user_id}] 您猜对了'
                            if int(time.time()) > charaguess[event.group_id]['starttime'] + 45:
                                text = text + '，回答已超时'
                            else:
                                if event.sender['card'] == '':
                                    username = event.sender['nickname']
                                else:
                                    username = event.sender['card']
                                if charaguess[event.group_id]['type'] == 1:
                                    recordGuessRank(event.user_id, username, 4)
                                else:
                                    recordGuessRank(event.user_id, username, 8)
                            if charaguess[event.group_id]['istrained']:
                                picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                         f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_after_training.jpg"
                            else:
                                picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                         f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_normal.jpg"
                            text = text + f"\n正确答案：{charaguess[event.group_id]['prefix']} - {resp[1]}"
                            charaguess[event.group_id]['isgoing'] = False
                            sendmsg(event, text + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                        else:
                            text = f"[CQ:at,qq={event.user_id}] 您猜错了，答案不是{resp[1]}哦"
                            if int(time.time()) > charaguess[event.group_id]['starttime'] + 45:
                                text = text + '，回答已超时'
                                if charaguess[event.group_id]['istrained']:
                                    picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                             f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_after_training.jpg"
                                else:
                                    picdir = 'data/assets/sekai/assetbundle/resources/startapp/' \
                                             f"character/member/{charaguess[event.group_id]['assetbundleName']}/card_normal.jpg"
                                text = text + f"\n正确答案：{charaguess[event.group_id]['prefix']} - {getcharaname(charaguess[event.group_id]['charaid'])}" + fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]"
                                charaguess[event.group_id]['isgoing'] = False
                            sendmsg(event, text)
                    return
            except KeyError:
                pass
        if event.message == f'[CQ:at,qq={event.self_id}] ':
            sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/')
            return
    except apiCallError:
        sendmsg(event, '查不到数据捏，好像是bot网不好')
    except (JSONDecodeError, requests.exceptions.ConnectionError):
        sendmsg(event, '查不到捏，好像是bot网不好')
    except aiocqhttp.exceptions.NetworkError:
        pass
    except maintenanceIn:
        sendmsg(event, '查不到捏，可能啤酒烧烤在维护')
    except ValueError:
        sendmsg(event, 'ValueError，可能是输入错误')
    except userIdBan:
        sendmsg(event, '该玩家因违反bot使用条款（包括但不限于开挂）已被bot拉黑')
    except LeakContent:
        sendmsg(event, '你要查询的内容还没有实装')
    except QueryBanned as e:
        if e.server == 'jp':
            sendmsg(event, '由于日服限制，数据已无法抓取，该功能已停用')
        elif e.server == 'en':  # 这不就用上了
            sendmsg(event, 'Due to limitations on the international server API, data can no longer be retrieved. This feature has been disabled.')
        elif e.server == 'tw':
            sendmsg(event, '由於台服API限制，資料已無法抓取，該功能已停用。')
        elif e.server == 'kr':
            sendmsg(event, '한국 서버 API 제한으로 인해 데이터를 더 이상 가져올 수 없습니다. 이 기능은 사용 중지되었습니다.')
    except Exception as a:
        traceback.print_exc()
        if repr(a) == "KeyError('status')":
            sendmsg(event, '图片发送失败，请再试一次')
        elif 'OperationalError' in repr(a):
            sendmsg(event, '数据库无法连接，可能是bot维护中')
        else:
            sendmsg(event, '出问题了捏\n' + repr(a))


def sendmsg(event, msg):
    global send1
    global send3
    timeArray = time.localtime(time.time())
    Time = time.strftime("\n[%Y-%m-%d %H:%M:%S]", timeArray)
    try:
        print(Time, botname[event.self_id] + '收到命令', event.group_id, event.user_id, event.message.replace('\n', ''))
        print(botname[event.self_id] + '发送群消息', event.group_id, msg.replace('\n', ''))
    except KeyError:
        print(Time, '测试bot收到命令', event.group_id, event.user_id, event.message.replace('\n', ''))
        print('测试bot发送群消息', event.group_id, msg.replace('\n', ''))



@bot.on_notice('group_increase')  # 群人数增加事件
async def handle_group_increase(event: Event):
    if event.self_id == guildbot:
        return
    if event.user_id == event.self_id:  # 自己被邀请进群
        if event.group_id in requestwhitelist:
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup, message=f'我已加入群{event.group_id}')
        else:
            await bot.send_group_msg(self_id=event.self_id, group_id=event.group_id, message='未经审核的邀请，已自动退群')
            await bot.set_group_leave(self_id=event.self_id, group_id=event.group_id)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'有人邀请我加入群{event.group_id}，已自动退群')


@bot.on_request('group')  # 加群请求或被拉群
async def handle_group_request(event: Event):
    if event.self_id == guildbot:
        return
    print(event.sub_type, event.message)
    if event.sub_type == 'invite':  # 被邀请加群
        if event.group_id in requestwhitelist:
            await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                            approve=True)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'{event.user_id}邀请我加入群{event.group_id}，已自动同意')
        else:
            await bot.set_group_add_request(self_id=event.self_id, flag=event.flag, sub_type=event.sub_type,
                                            approve=False)
            await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                     message=f'{event.user_id}邀请我加入群{event.group_id}，已自动拒绝')


@bot.on_notice('group_ban')
async def handle_group_ban(event: Event):
    if event.self_id == guildbot:
        return
    print(event.group_id, event.operator_id, event.user_id, event.duration)
    if event.user_id == event.self_id:
        await bot.set_group_leave(self_id=event.self_id, group_id=event.group_id)
        await bot.send_group_msg(self_id=event.self_id, group_id=msggroup,
                                 message=f'我在群{event.group_id}内被{event.operator_id}禁言{event.duration / 60}分钟，已自动退群')

async def autopjskguess():
    global pjskguess
    global charaguess
    now = time.time()
    for group in pjskguess:
        if pjskguess[group]['isgoing'] and pjskguess[group]['starttime'] + 50 < now:
            picdir = f"{asseturl}/startapp/music/jacket/" \
                     f"jacket_s_{str(pjskguess[group]['musicid']).zfill(3)}/" \
                     f"jacket_s_{str(pjskguess[group]['musicid']).zfill(3)}.png"
            text = '时间到，正确答案：' + idtoname(pjskguess[group]['musicid'])
            pjskguess[group]['isgoing'] = False
            try:
                await bot.send_group_msg(self_id=pjskguess[group]['selfid'], group_id=group, message=text + fr"[CQ:image,file={picdir},cache=0]")
                if pjskguess[group]['type'] == 10:
                    await bot.send_group_msg(self_id=pjskguess[group]['selfid'], group_id=group, message=fr"[CQ:record,file=file:///{botdir}/piccache/{group}mix.mp3,cache=0]")
            except:
                pass

    for group in charaguess:
        if charaguess[group]['isgoing'] and charaguess[group]['starttime'] + 30 < now:
            try:
                if charaguess[group]['istrained']:
                    picdir = f'{asseturl}/startapp/' \
                             f"character/member/{charaguess[group]['assetbundleName']}/card_after_training.jpg"
                else:
                    picdir = f'{asseturl}/startapp/' \
                             f"character/member/{charaguess[group]['assetbundleName']}/card_normal.jpg"
                text = f"时间到，正确答案：{charaguess[group]['prefix']} - " + \
                       getcharaname(charaguess[group]['charaid'])
                charaguess[group]['isgoing'] = False
                try:
                    await bot.send_group_msg(self_id=charaguess[group]['selfid'], group_id=group, message=text + fr"[CQ:image,file={picdir},cache=0]")
                except:
                    pass
            except:
                charaguess[group]['isgoing'] = False
                try:
                    await bot.send_group_msg(self_id=charaguess[group]['selfid'], group_id=group, message="猜卡面出现问题已结束")
                except:
                    pass


with open('yamls/blacklist.yaml', "r") as f:
    blacklist = yaml.load(f, Loader=yaml.FullLoader)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
scheduler = AsyncIOScheduler()
if os.path.basename(__file__) == 'bot.py':
    scheduler.add_job(autopjskguess, 'interval', seconds=4)
scheduler.start()
if os.path.basename(__file__) == 'bot.py':
    bot.run(host='127.0.0.1', port=1234, debug=False, loop=loop)
else:
    bot.run(host='127.0.0.1', port=11416, debug=False, loop=loop)
