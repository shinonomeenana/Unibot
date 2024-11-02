import base64
import os
import ujson as json
import random
from datetime import datetime
from ujson import JSONDecodeError
import asyncio
# import aiocqhttp
import aiofiles
import aiohttp
import requests
import re
import time
import traceback
import yaml
from aiocqhttp import CQHttp, Event
# from chunithm.alias import chualias, chudel, chuset
# from chunithm.daily_bonus import chuni_signin, chuni_signin_lin
from modules.chara import charaset, grcharaset, charadel, charainfo, grcharadel, aliastocharaid, get_card, cardidtopic, \
    findcard, getvits, getcardinfo
# from chunithm.qiu import getqiubind, qiu_bind_aimeid, qiub30
from modules.config import whitelist, msggroup, groupban, asseturl, verifyurl, distributedurl
from modules.blacklist import *
# from modules.getdata import apiCallError, maintenanceIn, userIdBan, QueryBanned
# from modules.getdata import LeakContent
from modules.findevent import findevent
from modules.opencv import matchjacket
from modules.otherpics import geteventpic
from modules.gacha import getcharaname, getcurrentgacha, fakegacha
from modules.musics import parse_bpm, aliastochart, idtoname, notecount, tasseiritsu, findbpm, \
    getcharttheme, setcharttheme, getPlayLevel, levelRankPic
# from modules.pjskguess import get_two_lines, getrandomjacket, cutjacket, getrandomchart, cutchartimg, getrandomcard, cutcard, random_lyrics,\
#     getrandommusic, cutmusic, getrandomchartold, cutchartimgold, recordGuessRank, guessRank, getRandomSE, cutSE
# from modules.pjskinfo import aliastomusicid, pjskset, pjskdel, pjskalias, pjskinfo, writelog
from modules.profileanalysis import daibu, rk, pjskjindu, pjskprofile, pjskb30, r30
from modules.sk import sk, getqqbind, bindid, setprivate, skyc, verifyid, gettime, teamcount, chafang, \
    getstoptime, ss, drawscoreline, cheaterFound, cheater_ban_reason, score_line
from modules.texttoimg import texttoimg, blank
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from imageutils import text2image
import hashlib
# from chunithm.b30 import chunib30, getchunibind, bind_aimeid
# from chunithm.info import search_song, song_details, chu_level_rank
# from chunithm.chart import get_chunithm_chart
# from wds.musicinfo import wds_alias_to_music_id, wdsinfo, wdsset, wdsdel, wdsalias, wds_alias_to_chart
# from wds.event import wds_score_line

# if os.path.basename(__file__) == 'bot.py':
#     bot = CQHttp()
#     botdebug = False
# else:
#     guildhttpport = 1988
#     bot = CQHttp(api_root=f'http://127.0.0.1:{guildhttpport}')
#     botdebug = True
guildhttpport = 1234
bot = CQHttp(api_root=f'http://0.0.0.0:{guildhttpport}')
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
    492632068: '一号机'
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
async def sync_handle_msg(event):
    if event.self_id == guildbot:
        event.raw_message = event.raw_message[event.raw_message.find(f"qq={guildbot}") + len(f"qq={guildbot}]"):].strip()
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
            print(Time, botname[event.self_id] + '收到消息', event.group_id, event.user_id, event.raw_message.replace('\n', ''))
        except KeyError:
            print(Time, '测试bot收到消息', event.group_id, event.user_id, event.raw_message.replace('\n', ''))
    if event.group_id in groupban:
        # print('黑名单群已拦截')
        return
    if event.user_id in block:
        # print('黑名单成员已拦截')
        return
    if event.raw_message[0:1] == '/':
        event.raw_message = event.raw_message[1:]

    try:
        # -----------------------功能测试-----------------------------
        # if event.raw_message == 'test':
        #     await sendmsg(event, event.sender['nickname'] + event.sender['card'])
        # -----------------------结束测试-----------------------------
        if event.raw_message == 'help':
            msg = "本bot功能与原版Unibot相同，不过指令需要加上uni前缀区分。例如：findevent -> unifindevent。\n代码基于Unibot开源项目修改，本bot与原作者无任何关系。"
            await sendmsg(event, msg)
            return

        if event.raw_message == "时速":
            texttoimg(ss(), 300, 'ss')
            msg = fr"[CQ:image,file=file:///{botdir}\piccache\ss.png,cache=0]"
            await sendmsg(event, msg)
        if event.raw_message.startswith("时速"):
            charaname = event.raw_message[2:].strip()
            charaid = aliastocharaid(charaname, event.group_id)
            if charaid[0] != 0:
                texttoimg(ss(charaid[0]), 300, 'ss')
                await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\ss.png,cache=0]")
                return
        if event.raw_message == "sk预测":
            texttoimg(skyc(), 540, 'skyc')
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\skyc.png,cache=0]")
            return
        elif msg := re.match('^(?:uni查询?uni卡面?|unifindcard)(.*)', event.raw_message):
            msg = msg.group(1).strip()
            if msg.isdigit():
                await sendmsg(event, fr"[CQ:image,file=base64://{get_base64_img(getcardinfo(int(msg), event.group_id))},cache=0]")
                return
            para = msg.split(' ')
            resp = aliastocharaid(para[0], event.group_id)
            if resp[0] != 0:
                if len(para) == 1:
                    await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], None)},cache=0]")
                elif len(para) == 2:
                    if para[1] == '一星' or para[1] == '1':
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_1')},cache=0]")
                    elif para[1] == '二星' or para[1] == '2':
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_2')},cache=0]")
                    elif para[1] == '三星' or para[1] == '3':
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_3')},cache=0]")
                    elif para[1] == '四星' or para[1] == '4':
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_4')},cache=0]")
                    elif '生日' in para[1] or 'birthday' in para[1]:
                        await sendmsg(event,
                                fr"[CQ:image,file=file:///{botdir}\piccache\{findcard(resp[0], 'rarity_birthday')},cache=0]")
                    else:
                        await sendmsg(event, '命令不正确')
            else:
                await sendmsg(event, '找不到你说的角色哦')
            return
        # ---------------------- 服务器判断 -------------------------
        server = 'jp'
        if event.raw_message[:2] == "jp":
            event.raw_message = event.raw_message[2:]
        elif event.raw_message[:2] == "tw":
            event.raw_message = event.raw_message[2:]
            server = 'tw'
        elif event.raw_message[:2] == "en":
            event.raw_message = event.raw_message[2:]
            server = 'en'
        elif event.raw_message[:2] == "kr":
            event.raw_message = event.raw_message[2:]
            server = 'kr'
        # -------------------- 多服共用功能区 -----------------------
        if event.raw_message == "sk线" or event.raw_message == "skline":
            texttoimg(score_line(server), 540, f'score_line_{server}')
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\score_line_{server}.png,cache=0]")
            return
        if event.raw_message[:2] == "sk":
            if event.group_id in blacklist['sk'] and server == 'jp':
                return
            if event.raw_message == "sk":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '你没有绑定id！')
                    return
                result = sk(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                if 'piccache' in result:
                    await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                else:
                    await sendmsg(event, result)
            else:
                event.raw_message = event.raw_message[event.raw_message.find("sk") + len("sk"):].strip()
                userids = event.raw_message.split(' ')
                if len(userids) > 8:
                    await sendmsg(event, '少查一点吧')
                    return
                if len(userids) == 1:
                    userid = event.raw_message.strip()
                    if '[CQ:at' in userid:
                        userid = re.sub(r'\D', "", userid)
                    if not userid.isdigit():
                        # 新增world link单独榜线查询
                        charaid = aliastocharaid(userid, event.group_id)
                        if charaid[0] != 0:
                            bind = getqqbind(event.user_id, server)
                            if bind is None:
                                await sendmsg(event, '你没有绑定id！')
                                return
                            result = sk(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id, world_link_chara_id=charaid[0])
                            if 'piccache' in result:
                                await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                            else:
                                await sendmsg(event, result)
                    try:
                        if int(userid) > 10000000:
                            result = sk(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                        else:
                            result = sk(targetrank=userid, secret=True, server=server, qqnum=event.user_id)
                        if 'piccache' in result:
                            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                        else:
                            await sendmsg(event, result)
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
                                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                                    else:
                                        await sendmsg(event, result)
                                    return
                                except ValueError:
                                    return
                    result = ''
                    for userid in userids:
                        userid = re.sub(r'\D', "", userid)
                        if userid == '':
                            await sendmsg(event, '你这id有问题啊')
                            return
                        if int(userid) > 10000000:
                            result += sk(targetid=userid, secret=False, server=server, simple=True, qqnum=event.user_id)
                        else:
                            result += sk(targetrank=userid, secret=True, server=server, simple=True, qqnum=event.user_id)
                        result += '\n\n'
                    await sendmsg(event, result[:-2])
                    return
        if event.raw_message[:2] == "绑定":
            userid = event.raw_message.replace("绑定", "").strip()
            try:
                int(userid)
                await sendmsg(event, bindid(event.user_id, userid, server))
                return
            except ValueError:
                return
        if event.raw_message == "不给看":
            if setprivate(event.user_id, 1, server):
                await sendmsg(event, '不给看！')
            else:
                await sendmsg(event, '你还没有绑定哦')
            return
        if event.raw_message == "给看":
            if setprivate(event.user_id, 0, server):
                await sendmsg(event, '给看！')
            else:
                await sendmsg(event, '你还没有绑定哦')
            return
        if event.raw_message[:2] == "逮捕":
            if event.group_id in blacklist['sk'] and server == 'jp':
                return
            if event.raw_message == "逮捕":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '查不到捏，可能是没绑定')
                    return
                result = daibu(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                await sendmsg(event, result)
            else:
                userid = event.raw_message.replace("逮捕", "").strip()
                if userid == '':
                    return
                if '[CQ:at' in userid:
                    qq = re.sub(r'\D', "", userid)
                    bind = getqqbind(qq, server)
                    if bind is None:
                        await sendmsg(event, '查不到捏，可能是没绑定')
                        return
                    elif bind[2] and qq != str(event.user_id):
                        await sendmsg(event, '查不到捏，可能是不给看')
                        return
                    else:
                        result = daibu(targetid=bind[1], secret=bind[2], server=server, qqnum=event.user_id)
                        await sendmsg(event, result)
                        return
                try:
                    if int(userid) > 10000000:
                        result = daibu(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                    else:
                        # 本来想写逮捕排位排名的 后来忘了 之后有时间看看
                        result = daibu(targetid=userid, secret=False, server=server, qqnum=event.user_id)
                    await sendmsg(event, result)
                except ValueError:
                    return
            return
        if event.raw_message == "pjsk进度":
            bind = getqqbind(event.user_id, server)
            if bind is None:
                await sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'master', server, event.user_id)
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.raw_message in ["pjsk进度ex", "pjsk进度expert"]:
            bind = getqqbind(event.user_id, server)
            if bind is None:
                await sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'expert', server, event.user_id)
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if event.raw_message in ["pjsk进度ap", "pjsk进度apd", "pjsk进度append"]:
            bind = getqqbind(event.user_id, server)
            if bind is None:
                await sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskjindu(bind[1], bind[2], 'append', server, event.user_id)
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{bind[1]}jindu.png,cache=0]")
            return
        if re.match('^pjsk *b30$', event.raw_message):
            bind = getqqbind(event.user_id, server)
            if bind is None:
                await sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskb30(userid=bind[1], private=bind[2], server=server, qqnum=event.user_id)
            await sendmsg(event, fr"同等级下已按实装顺序排序[CQ:image,file=file:///{botdir}\piccache\{bind[1]}b30.jpg,cache=0]")
            return
        if msg := re.match('^pjsk *r30(.*)', event.raw_message):
            # 给冲色段的朋友打5v5看对手情况用的 不冲5v5色段看这个没用
            if event.user_id not in whitelist and event.group_id not in whitelist:
                return
            userid = msg.group(1).strip()
            if not userid:
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '查不到捏，可能是没绑定')
                    return
            else:
                bind = (1, userid, False)
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\{r30(bind[1], bind[2], server, event.user_id)}.png,cache=0]")
            return
        if event.raw_message == "pjskprofile" or event.raw_message == "个人信息":
            bind = getqqbind(event.user_id, server)
            if bind is None:
                await sendmsg(event, '查不到捏，可能是没绑定')
                return
            pjskprofile(bind[1], bind[2], server, event.user_id, is_force_update=True)
            await sendmsg(event, f"[CQ:image,file=file:///{botdir}/piccache/{bind[1]}profile.jpg,cache=0]")
            return
        if event.raw_message[:2] == "查房" or event.raw_message[:2] == "cf":
            if event.group_id in blacklist['sk'] and event.raw_message[:2] == "查房":
                return
            if event.raw_message[:2] == "cf":
                event.raw_message = '查房' + event.raw_message[2:]
            private = False
            if event.raw_message == "查房":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
                private = bind[2]
            else:
                userid = event.raw_message.replace("查房", "").strip()
            try:
                if int(userid) > 10000000:
                    result = chafang(targetid=userid, private=private, server=server)
                else:
                    result = chafang(targetrank=userid, server=server)
                await sendmsg(event, result)
                return
            except ValueError:
                return
        graphstart = 0
        if event.raw_message[:4] == '24小时':
            graphstart = time.time() - 60 * 60 * 24
            event.raw_message = event.raw_message[4:]
        if event.raw_message[:3] == "分数线":
            try:
                if event.raw_message == "分数线":
                    bind = getqqbind(event.user_id, server)
                    if bind is None:
                        await sendmsg(event, '你没有绑定id！')
                        return
                    userid = bind[1]
                else:
                    userid = event.raw_message.replace("分数线", "")
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
                            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                        else:
                            await sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                        return
                    except ValueError:
                        return
                else:
                    result = drawscoreline(targetrank=userids[0], targetrank2=userids[1], starttime=graphstart, server=server)
                    if result:
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{result},cache=0]")
                    else:
                        await sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                    return
            except:
                return
        if event.raw_message[:3] == "查水表" or event.raw_message[:3] == "csb":
            if event.group_id in blacklist['sk'] and event.raw_message[:3] == "查水表":
                return
            if event.raw_message[:3] == "csb":
                event.raw_message = '查水表' + event.raw_message[3:]
            private = False
            if event.raw_message == "查水表":
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
                private = bind[2]
            else:
                userid = event.raw_message.replace("查水表", "").strip()
            try:
                if int(userid) > 10000000:
                    result = getstoptime(userid, private=private, server=server)
                else:
                    result = getstoptime(targetrank=userid, server=server)
                if result:
                    img = text2image(result, max_width=1000, padding=(30, 30))
                    img.save(f"piccache\csb{userid}.png")
                    await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\piccache\csb{userid}.png,cache=0]")
                else:
                    await sendmsg(event, "你要查询的玩家未进入前200，暂无数据")
                return
            except ValueError:
                return
        if event.raw_message == '5v5人数':
            await sendmsg(event, teamcount(server).replace('3-3.dev', '3-3点dev'))
        if event.raw_message[:2] == "rk":
            if event.raw_message == "rk":
                bind = getqqbind(event.user_id, server=server)
                if bind is None:
                    await sendmsg(event, '你没有绑定id！')
                    return
                result = rk(bind[1], None, bind[2], server=server)
                await sendmsg(event, result)
            else:
                userid = event.raw_message.replace("rk", "").strip()
                try:
                    if int(userid) > 10000000:
                        result = rk(userid, server=server)
                    else:
                        result = rk(None, userid, server=server)
                    await sendmsg(event, result)
                except ValueError:
                    return
            return
        # ----------------------- 恢复原命令 ---------------------------
        if server != 'jp':
            event.raw_message = server + event.raw_message
        # -------------------- 结束多服共用功能区 -----------------------
        if re.match('^uni活动(?:图鉴|列表|总览)|^unifindevent *all', event.raw_message):
            await sendmsg(event, fr"[CQ:image,file=base64://{get_base64_img(findevent())},cache=0]")
            return
        if msg := re.match('^(?:unifindevent|uni查询?活动)(.*)', event.raw_message):
            arg = msg.group(1).strip()
            if not arg:
                tipdir = r'pics/findevent_tips.jpg'
                await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{tipdir},cache=0]")
            elif arg.isdigit():
                try:
                    if picdir := geteventpic(int(arg)):
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    else:
                        tipdir = r'pics/findevent_tips.jpg'
                        await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{tipdir},cache=0]")
                    return
                except ValueError:
                    traceback.print_exc()
                    await sendmsg(event, f"未找到活动或生成失败")
                    return
                except FileNotFoundError:
                    traceback.print_exc()
                    await sendmsg(event, f"未找到活动资源图片，请等待更新")
                    return
            else:
                await sendmsg(event, fr"[CQ:image,file=base64://{get_base64_img(findevent(arg))},cache=0]")
            return
        if event.raw_message[:5] == 'event':
            eventid = event.raw_message[event.raw_message.find("event") + len("event"):].strip()
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
                await sendmsg(event, f"未找到活动资源图片，请等待更新")
                return
            if picdir:
                await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
            else:
                await sendmsg(event, f"未找到活动或生成失败")
            return
        try:
            if event.raw_message[:4] == "难度排行" or event.raw_message[2:6] == "难度排行" or event.raw_message[-4:] == "难度排行":
                fcap = 0
                diff = 'master'
                if 'append' in event.raw_message or 'apd' in event.raw_message:
                    diff = 'append'
                elif 'expert' in event.raw_message or 'ex' in event.raw_message:
                    diff = 'expert'
                elif 'hard' in event.raw_message or 'hd' in event.raw_message:
                    diff = 'hard'
                elif 'normal' in event.raw_message or 'nm' in event.raw_message:
                    diff = 'normal'
                elif 'easy' in event.raw_message or 'ez' in event.raw_message:
                    diff = 'easy'
                try:
                    level = int(re.sub(r'\D', "", event.raw_message))
                except:
                    if event.raw_message == '难度排行' or fcap in [1, 2] or diff in ['append', 'expert', 'hard', 'normal', 'easy']:
                        level = 0
                    else:
                        return
                bind = getqqbind(event.user_id, server)

                if bind is not None:
                    picdir = levelRankPic(level, diff, fcap, userid=bind[1], isprivate=bind[2], qqnum=event.user_id)
                else:
                    picdir = levelRankPic(level, diff, fcap,)
                await sendmsg(event, f"[CQ:image,file=file:///{botdir}/{picdir},cache=0]")

                return
        except:
            traceback.print_exc()
            await sendmsg(event, '参数错误或无此难度（默认master），指令：/难度排行 定数 难度，'
                           '难度支持的输入: easy, normal, hard, expert, master，如/难度排行 28 expert /ap难度排行 28 expert')

        if "谱面预览2" in event.raw_message:
            picdir = aliastochart(event.raw_message.replace("谱面预览2", ''), True)
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    await sendmsg(event, picdir[0] + fr"[CQ:image,file=file:///{botdir}\{picdir[1]},cache=0]")
                else:
                    await sendmsg(event, picdir + "\n暂无谱面图片 请等待更新"
                                            "\n（温馨提示：谱面预览2只能看master与expert）")
            else:  # 匹配不到歌曲
                await sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.raw_message[:8] == 'cardinfo':
            cardid = event.raw_message[event.raw_message.find("cardinfo") + len("cardinfo"):].strip()
            await sendmsg(event, fr"[CQ:image,file=file:///{botdir}/piccache/cardinfo/{getcardinfo(int(cardid))},cache=0]")
            return
        if event.raw_message[:4] == 'card':
            cardid = event.raw_message[event.raw_message.find("card") + len("card"):].strip()
            pics = cardidtopic(int(cardid))
            print(pics)
            for pic in pics:
                await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{pic},cache=0]")
            return
        if event.raw_message[:4] == "谱面预览" or event.raw_message[-4:] == "谱面预览" :
            qun = True
            if event.self_id == guildbot:
                qun = False
            try:
                picdir = aliastochart(event.raw_message.replace("谱面预览", ''), False, qun, getcharttheme(event.user_id))
            except FileNotFoundError:
                await sendmsg(event, '没有找到你要的难度')
                return
            if picdir is not None:  # 匹配到歌曲
                if len(picdir) == 2:  # 有图片
                    if event.self_id == guildbot:
                        await sendmsg(event, picdir[0] + f"\niOS如果图片糊，请将QQ更新到最新版本（9开头），安卓需在群内使用官方bot才能查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                    else:
                        await sendmsg(event, picdir[0] + f"\niOS保存后即可查看原图，安卓使用官方Bot才可查看原图[CQ:image,file=file:///{botdir}/{picdir[1]},cache=0]")
                elif picdir == '':
                    await sendmsg(event, f'[CQ:poke,qq={event.user_id}]')
                    return
                else:
                    await sendmsg(event, picdir + "\n暂无谱面图片 请等待更新")
            else:  # 匹配不到歌曲
                await sendmsg(event, "没有找到你说的歌曲哦")
            return
        if event.raw_message[:5] == "theme":
            theme = event.raw_message[event.raw_message.find("theme") + len("theme"):].strip()
            await sendmsg(event, setcharttheme(event.user_id, theme))
            return
        if event.raw_message[:3] == "查时间":
            userid = event.raw_message[event.raw_message.find("查时间") + len("查时间"):].strip()
            if userid == '':
                bind = getqqbind(event.user_id, server)
                if bind is None:
                    await sendmsg(event, '你没有绑定id！')
                    return
                userid = bind[1]
            userid = re.sub(r'\D', "", userid)
            if userid == '':
                await sendmsg(event, '你这id有问题啊')
                return
            if verifyid(userid):
                await sendmsg(event, time.strftime('注册时间：%Y-%m-%d %H:%M:%S',
                                             time.localtime(gettime(userid))))
            else:
                await sendmsg(event, '你这id有问题啊')
            return
        if event.raw_message[:8] == 'charaset' and 'to' in event.raw_message:
            if event.user_id in aliasblock:
                await sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.raw_message = event.raw_message[8:]
            para = event.raw_message.split('to')
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                await sendmsg(event,
                        charaset(para[0], para[1], event.user_id, username, f"{qun['name']}({event.guild_id})内", is_hide=True))
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                await sendmsg(event, charaset(para[0], para[1], event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.raw_message.startswith('封禁查询'):
            userid = event.raw_message[4:]
            await sendmsg(event, cheater_ban_reason(userid))
            return
        if event.raw_message[:10] == 'grcharaset' and 'to' in event.raw_message:
            event.raw_message = event.raw_message[10:]
            para = event.raw_message.split('to')
            if event.self_id == guildbot:
                await sendmsg(event, grcharaset(para[0], para[1], event.guild_id, is_hide=True))
            else:
                await sendmsg(event, grcharaset(para[0], para[1], event.group_id))
            return
        if event.raw_message[:8] == 'charadel':
            if event.user_id in aliasblock:
                await sendmsg(event, '你因乱设置昵称已无法使用此功能')
                return
            event.raw_message = event.raw_message[8:]
            if event.sender['card'] == '':
                username = event.sender['nickname']
            else:
                username = event.sender['card']
            if event.self_id == guildbot:
                resp = requests.get(f'http://127.0.0.1:{guildhttpport}/get_guild_info?guild_id={event.guild_id}')
                qun = resp.json()
                await sendmsg(event,
                        charadel(event.raw_message, event.user_id, username, f"{qun['name']}({event.guild_id})内"))
            else:
                qun = bot.sync.get_group_info(self_id=event.self_id, group_id=event.group_id)
                await sendmsg(event, charadel(event.raw_message, event.user_id, username, f"{qun['group_name']}({event.group_id})内"))
            return
        if event.raw_message[:10] == 'grcharadel':
            event.raw_message = event.raw_message[10:]
            if event.self_id == guildbot:
                await sendmsg(event, grcharadel(event.raw_message, event.guild_id))
            else:
                await sendmsg(event, grcharadel(event.raw_message, event.group_id))
            return
        if event.raw_message[:9] == 'charainfo':
            if event.self_id == guildbot:
                await sendmsg(event, '频道bot不支持此功能')
                return
            event.raw_message = event.raw_message[9:]
            if event.self_id == guildbot:
                await sendmsg(event, charainfo(event.raw_message, event.guild_id))
            else:
                await sendmsg(event, charainfo(event.raw_message, event.group_id))
            return
        if event.raw_message[:5] == "白名单添加" and event.user_id in whitelist:
            event.raw_message = event.raw_message[event.raw_message.find("白名单添加") + len("白名单添加"):].strip()
            requestwhitelist.append(int(event.raw_message))
            await sendmsg(event, '添加成功: ' + event.raw_message)
            return
        if event.raw_message[:3] == "达成率":
            event.raw_message = event.raw_message[event.raw_message.find("达成率") + len("达成率"):].strip()
            para = event.raw_message.split(' ')
            if len(para) < 5:
                return
            await sendmsg(event, tasseiritsu(para))
            return
        if event.raw_message[:4] == '封面匹配':
            global opencvmatch
            if not opencvmatch:
                try:
                    opencvmatch = True
                    await sendmsg(event, f'[CQ:reply,id={event.raw_message_id}]了解，查询中（局部封面图匹配歌曲，输出只对有效输入负责，多次有意输入无效图片核实后将会拉黑）')
                    url = event.raw_message[event.raw_message.find('url=') + 4:event.raw_message.find(']')]
                    title, picdir = matchjacket(url=url)
                    if title:
                        if 'assets' in picdir:
                            await sendmsg(event, f"[CQ:reply,id={event.raw_message_id}]匹配点过少，该曲为最有可能匹配的封面：\n" + fr"{title}[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                        else:
                            await sendmsg(event, fr"[CQ:reply,id={event.raw_message_id}]{title}[CQ:image,file=file:///{botdir}\{picdir},cache=0]")
                    else:
                        await sendmsg(event, f'[CQ:reply,id={event.raw_message_id}]找不到捏')
                except Exception as a:
                    traceback.print_exc()
                    await sendmsg(event, '出问题了捏\n' + repr(a))
                opencvmatch = False
            else:
                await sendmsg(event, f'当前有正在匹配的进程，请稍后再试')
            return
        if event.raw_message[:3+3] == 'uni查物量':
            await sendmsg(event, notecount(int(event.raw_message[3+3:])))
            return
        if event.raw_message[:4+3] == 'uni查bpm':
            await sendmsg(event, findbpm(int(event.raw_message[4+3:])))
            return

        def handle_bind(event, command, server=None):
            # userid = event.raw_message.replace(' ', '').replace(f"{command}绑定", "").strip()
            # try:
            #     int(userid)
            # except ValueError:
            #     traceback.print_exc()
            #     await sendmsg(event, '卡号应为20位纯数字')
            #     return
            # if len(userid) != 20:
            #     await sendmsg(event, '卡号应为20位纯数字')
            #     return
            # await sendmsg(event, bind_aimeid(event.user_id, userid, server))
            return None

        def handle_b30(event, command, server=None, version=None):
            # bind = getchunibind(event.user_id, server)
            # if bind is None:
            #     await sendmsg(event, f'查不到捏，可能是没绑定，绑定命令：{command} 绑定xxxxx')
            #     return
            # b30_dir = chunib30(userid=bind, server=server, version=version, qqnum=event.user_id)
            # if re.match(f'^{command} *b30 lmn$', event.raw_message):
            #     await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{b30_dir},cache=0]" + '\n查Luminous定数已无需添加lmn')
            # else:
            #     await sendmsg(event, fr"[CQ:image,file=file:///{botdir}\{b30_dir},cache=0]")
            return None

        commands = [("aqua", "aqua"), ("Super", 'super'), ("super", 'super'), ("林先生", 'lin'),
                     ("na", 'na'), ("lee", 'na'), ("lin", 'lin'), ("rin", "rin"), ("mai", "mobi"), ('mobi', 'mobi')]

        for command, server in commands:
            if event.raw_message.startswith(f"{command} 绑定") or event.raw_message.startswith(f"{command}绑定"):
                handle_bind(event, command, server)
                return
            elif re.match(f'^{command} *b30$', event.raw_message):
                handle_b30(event, command, server, version='2.15')
                return
            elif re.match(f'^{command} *b30 lmn$', event.raw_message):
                handle_b30(event, command, server, version='2.20')
                return
            # elif re.match(f'^{command} *b30 lmnp$', event.raw_message):
            #     handle_b30(event, command, server, version='2.20')
            #     return

        if event.raw_message == f'[CQ:at,qq={event.self_id}] ':
            await sendmsg(event, 'bot帮助文档：https://docs.unipjsk.com/')
            return
    # except apiCallError:
    #     await sendmsg(event, '查不到数据捏，好像是bot网不好')
    # except (JSONDecodeError, requests.exceptions.ConnectionError):
    #     await sendmsg(event, '查不到捏，好像是bot网不好')
    # except aiocqhttp.exceptions.NetworkError:
    #     pass
    # except maintenanceIn:
    #     await sendmsg(event, '查不到捏，可能啤酒烧烤在维护')
    # except ValueError:
    #     await sendmsg(event, 'ValueError，可能是输入错误')
    # except userIdBan:
    #     await sendmsg(event, '该玩家因违反bot使用条款（包括但不限于开挂）已被bot拉黑')
    # except LeakContent:
    #     await sendmsg(event, '你要查询的内容还没有实装')
    # except QueryBanned as e:
    #     if e.server == 'jp':
    #         await sendmsg(event, '由于日服限制，数据已无法抓取，该功能已停用')
    #     elif e.server == 'en':  # 这不就用上了
    #         await sendmsg(event, 'Due to limitations on the international server API, data can no longer be retrieved. This feature has been disabled.')
    #     elif e.server == 'tw':
    #         await sendmsg(event, '由於台服API限制，資料已無法抓取，該功能已停用。')
    #     elif e.server == 'kr':
    #         await sendmsg(event, '한국 서버 API 제한으로 인해 데이터를 더 이상 가져올 수 없습니다. 이 기능은 사용 중지되었습니다.')
    except Exception as a:
        traceback.print_exc()
        if repr(a) == "KeyError('status')":
            await sendmsg(event, '图片发送失败，请再试一次')
        elif 'OperationalError' in repr(a):
            await sendmsg(event, '数据库无法连接，可能是bot维护中')
        else:
            await sendmsg(event, '出问题了捏\n' + repr(a))


async def sendmsg(event, msg):
    global send1
    global send3
    timeArray = time.localtime(time.time())
    Time = time.strftime("\n[%Y-%m-%d %H:%M:%S]", timeArray)
    try:
        print(Time, botname[event.self_id] + '收到命令', event.group_id, event.user_id, event.raw_message.replace('\n', ''))
        print(botname[event.self_id] + '发送群消息', event.group_id, msg.replace('\n', ''))
        await bot.send(event, msg)
    except KeyError:
        print(Time, '测试bot收到命令', event.group_id, event.user_id, event.raw_message.replace('\n', ''))
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
    print(event.sub_type, event.raw_message)
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

def get_base64_img(img_path: str) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# with open('yamls/blacklist.yaml', "r") as f:
#     blacklist = yaml.load(f, Loader=yaml.FullLoader)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
scheduler = AsyncIOScheduler()
# if os.path.basename(__file__) == 'bot.py':
#     scheduler.add_job(autopjskguess, 'interval', seconds=4)
scheduler.start()
if os.path.basename(__file__) == 'bot.py':
    bot.run(host='0.0.0.0', port=1234, debug=True, loop=loop)
else:
    bot.run(host='127.0.0.1', port=11416, debug=False, loop=loop)
