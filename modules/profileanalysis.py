import io
import random
import ujson as json
import os.path
import time
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import requests
from modules.config import proxies, env, rank_query_ban_servers, suite_uploader_path
from modules.getdata import QueryBanned, callapi
from modules.sk import verifyid, recordname, currentevent, recordhitokoto
from modules.texttoimg import texttoimg
from ujson import JSONDecodeError

assetpath = 'data/assets/sekai/assetbundle/resources'

rankmatchgrades = {
    1: 'ビギナー(Beginner)',
    2: 'ブロンズ(Bronze)',
    3: 'シルバー(Silver)',
    4: 'ゴールド(Gold)',
    5: 'プラチナ(Platinum)',
    6: 'ダイヤモンド(Diamond)',
    7: 'マスター(Master)'
}

def idtoname(musicid):
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for i in musics:
        if i['id'] == musicid:
            return i['title']
    return ''



class userprofile(object):

    def __init__(self):
        self.name = ''
        self.rank = 0
        self.userid = ''
        self.twitterId = ''
        self.word = ''
        self.userDecks = [0, 0, 0, 0, 0]
        self.special_training = [False, False, False, False, False]
        self.full_perfect = [0, 0, 0, 0, 0, 0]
        self.full_combo = [0, 0, 0, 0, 0, 0]
        self.clear = [0, 0, 0, 0, 0, 0]
        self.mvpCount = 0
        self.superStarCount = 0
        self.userProfileHonors = {}
        self.userHonorMissions = []
        self.characterRank = {}
        self.characterId = 0
        self.highScore = 0
        self.masterscore = {}
        self.expertscore = {}
        self.appendscore = {}
        self.musicResult = {}
        self.isNewData = False
        for i in range(25, 38):
            self.masterscore[i] = [0, 0, 0, 0]
        for i in range(21, 32):
            self.expertscore[i] = [0, 0, 0, 0]
        for i in range(23, 39):
            self.appendscore[i] = [0, 0, 0, 0]

    def getprofile(self, userid, server, qqnum='未知', data=None, query_type='unknown', is_force_update=False):
        if server == 'jp':
            masterdatadir = 'masterdata'
        elif server == 'en':
            masterdatadir = '../enapi/masterdata'
        elif server == 'tw':
            masterdatadir = '../twapi/masterdata'
        elif server == 'kr':
            masterdatadir = '../krapi/masterdata'

        if data is None:
            data = callapi(f'/user/{userid}/profile', server=server, query_type=query_type,
                            is_force_update=is_force_update)
        
        self.isNewData = 'totalPower' in data
        self.twitterId = data.get('userProfile', {}).get('twitterId', "")
        self.userid = userid
        self.word = data.get('userProfile', {}).get('word', "")

        try:
            if server in rank_query_ban_servers:
                if self.isNewData:
                    self.characterId = data['userChallengeLiveSoloResult']['characterId']
                    self.highScore = data['userChallengeLiveSoloResult']['highScore']
                else:
                    for i in data['userChallengeLiveSoloResults']:
                        if i['highScore'] > self.highScore:
                            self.characterId = i['characterId']
                            self.highScore = i['highScore']
            else:
                self.characterId = data['userChallengeLiveSoloResults'][0]['characterId']
                self.highScore = data['userChallengeLiveSoloResults'][0]['highScore']
        except:
            # 可能存在没打过挑战live，对应字段不存在的情况
            pass

        self.characterRank = data.get('userCharacters')
        self.userProfileHonors = data.get('userProfileHonors')
        self.userHonorMissions = data.get('userHonorMissions', [])

        if server in rank_query_ban_servers and self.isNewData:
            self.name = data['user']['name']
            self.rank = data['user']['rank']
            count_data = data['userMusicDifficultyClearCount']
            self.full_perfect = [count_data[i].get('allPerfect', 'no data') if i < len(count_data) else 0 for i in range(6)]
            self.full_combo = [count_data[i]['fullCombo'] if i < len(count_data) else 0 for i in range(6)]
            self.clear = [count_data[i]['liveClear'] if i < len(count_data) else 0 for i in range(6)]
            self.mvpCount = data['userMultiLiveTopScoreCount']['mvp']
            self.superStarCount = data['userMultiLiveTopScoreCount']['superStar']
        else:
            try:
                self.name = data['user']['userGamedata']['name']
                self.rank = data['user']['userGamedata']['rank']
            except KeyError:
                self.name = data['userGamedata']['name']
                self.rank = data['userGamedata']['rank']
            with open(f'{masterdatadir}/musics.json', 'r', encoding='utf-8') as f:
                allmusic = json.load(f)
            with open(f'{masterdatadir}/musicDifficulties.json', 'r', encoding='utf-8') as f:
                musicDifficulties = json.load(f)
            result = {}
            now = int(time.time() * 1000)
            self.masterscore['33+musicId'] = []
            for music in allmusic:
                result[music['id']] = [0, 0, 0, 0, 0, 0]
                if music['publishedAt'] < now:
                    found = [0, 0, 0]
                    for diff in musicDifficulties:
                        if music['id'] == diff['musicId'] and diff['musicDifficulty'] == 'expert':
                            playLevel = diff['playLevel']
                            self.expertscore[playLevel][3] = self.expertscore[playLevel][3] + 1
                            found[0] = 1
                        elif music['id'] == diff['musicId'] and diff['musicDifficulty'] == 'master':
                            playLevel = diff['playLevel']
                            if playLevel >= 34:
                                self.masterscore['33+musicId'].append(music['id'])
                            self.masterscore[playLevel][3] = self.masterscore[playLevel][3] + 1
                            found[1] = 1
                        elif music['id'] == diff['musicId'] and diff['musicDifficulty'] == 'append':
                            playLevel = diff['playLevel']
                            self.appendscore[playLevel][3] = self.appendscore[playLevel][3] + 1
                            found[2] = 1
                        if found == [1, 1, 1]:
                            break
            for music in data['userMusicResults']:
                musicId = music['musicId']
                musicDifficulty = music['musicDifficulty']
                playResult = music['playResult']
                self.mvpCount = self.mvpCount + music['mvpCount']
                self.superStarCount = self.superStarCount + music['superStarCount']
                if musicDifficulty == 'easy':
                    diffculty = 0
                elif musicDifficulty == 'normal':
                    diffculty = 1
                elif musicDifficulty == 'hard':
                    diffculty = 2
                elif musicDifficulty == 'expert':
                    diffculty = 3
                elif musicDifficulty == 'master':
                    diffculty = 4
                elif musicDifficulty == 'append':
                    diffculty = 5
                try:
                    if playResult == 'full_perfect':
                        if result[musicId][diffculty] < 3:
                            result[musicId][diffculty] = 3
                    elif playResult == 'full_combo':
                        if result[musicId][diffculty] < 2:
                            result[musicId][diffculty] = 2
                    elif playResult == 'clear':
                        if result[musicId][diffculty] < 1:
                            result[musicId][diffculty] = 1
                except KeyError:
                    # 韩服删除了on the rocks等歌曲 但这些歌曲成绩还保留在用户profile数据中 匹配不到歌曲会造成KeyError
                    pass
            for music in result:
                for i in range(0, 6):
                    if result[music][i] == 3:
                        self.full_perfect[i] = self.full_perfect[i] + 1
                        self.full_combo[i] = self.full_combo[i] + 1
                        self.clear[i] = self.clear[i] + 1
                    elif result[music][i] == 2:
                        self.full_combo[i] = self.full_combo[i] + 1
                        self.clear[i] = self.clear[i] + 1
                    elif result[music][i] == 1:
                        self.clear[i] = self.clear[i] + 1
                    if i == 5:
                        for diff in musicDifficulties:
                            if music == diff['musicId'] and diff['musicDifficulty'] == 'append':
                                playLevel = diff['playLevel']
                                break
                        if result[music][i] == 3:
                            self.appendscore[playLevel][0] += 1
                            self.appendscore[playLevel][1] += 1
                            self.appendscore[playLevel][2] += 1
                        elif result[music][i] == 2:
                            self.appendscore[playLevel][1] += 1
                            self.appendscore[playLevel][2] += 1
                        elif result[music][i] == 1:
                            self.appendscore[playLevel][2] += 1
                    elif i == 4:
                        for diff in musicDifficulties:
                            if music == diff['musicId'] and diff['musicDifficulty'] == 'master':
                                playLevel = diff['playLevel']
                                break
                        if result[music][i] == 3:
                            self.masterscore[playLevel][0] += 1
                            self.masterscore[playLevel][1] += 1
                            self.masterscore[playLevel][2] += 1
                        elif result[music][i] == 2:
                            self.masterscore[playLevel][1] += 1
                            self.masterscore[playLevel][2] += 1
                        elif result[music][i] == 1:
                            self.masterscore[playLevel][2] += 1
                    elif i == 3:
                        for diff in musicDifficulties:
                            if music == diff['musicId'] and diff['musicDifficulty'] == 'expert':
                                playLevel = diff['playLevel']
                                break
                        if result[music][i] == 3:
                            self.expertscore[playLevel][0] += 1
                            self.expertscore[playLevel][1] += 1
                            self.expertscore[playLevel][2] += 1
                        elif result[music][i] == 2:
                            self.expertscore[playLevel][1] += 1
                            self.expertscore[playLevel][2] += 1
                        elif result[music][i] == 1:
                            self.expertscore[playLevel][2] += 1
            self.musicResult = result
        for i in range(0, 5):
            if server in rank_query_ban_servers:
                if self.isNewData:
                    self.userDecks[i] = data['userDeck'][f'member{i + 1}']
                else:
                    try:
                        decknum = data['user']['userGamedata']['deck']
                    except KeyError:
                        decknum = data['userGamedata']['deck']
                    for deck in data['userDecks']:
                        if deck['deckId'] == decknum:
                            self.userDecks[i] = deck[f'member{i + 1}']
                            break
            else:
                self.userDecks[i] = data['userDecks'][0][f'member{i + 1}']
            for userCards in data['userCards']:
                if userCards['cardId'] != self.userDecks[i]:
                    continue
                if userCards['defaultImage'] == "special_training":
                    self.special_training[i] = True
        if not recordname(qqnum, userid, self.name, server=server):
            self.name = ''


def currentrankmatch(server='jp'):
    try:
        if server == 'jp':
            with open('masterdata/rankMatchSeasons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif server == 'tw':
            with open('../twapi/masterdata/rankMatchSeasons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif server == 'en':
            with open('../enapi/masterdata/rankMatchSeasons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif server == 'kr':
            with open('../krapi/masterdata/rankMatchSeasons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
    except FileNotFoundError:
        return None

    for i in range(0, len(data)):
        startAt = data[i]['startAt']
        endAt = data[i]['closedAt']
        now = int(round(time.time() * 1000))
        if startAt < now < endAt:
            return data[i]['id']

    if len(data) == 1:  # 如果只有一个数据，有可能是开第一次排位之前，也有可能是第一次排位之后，排除第一个排位之前的
        if now < data[0]['startAt']:
            return None
    return data[len(data) - 1]['id']


def r30(userid, private=False, server='jp', qqnum='未知'):
    if int(userid) < 10000000:
        event = currentevent('jp')
        eventid = event['id']
        ranking = callapi(f'/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={userid}', server=server)
        userid = ranking['rankings'][0]['userId']
        private = True
    data = callapi(f'/user/{userid}/profile', server)
    name = data['user']['userGamedata']['name']
    if not recordname(qqnum, userid, name):
        name = ''
    userMusicResults = data['userMusicResults']
    userMusicResults.sort(key=lambda x: x["updatedAt"], reverse=True)
    text = f'{name} - {userid}\n'
    if private:
        text = f'{name}\n'
    count = 0
    for musics in userMusicResults:
        count += 1
        timeArray = time.localtime(musics['updatedAt'] / 1000)
        otherStyleTime = time.strftime("%m-%d %H:%M", timeArray)
        if musics['updatedAt'] == musics["createdAt"]:
            if musics["fullPerfectFlg"]:
                addText = '初见AP'
            elif musics["fullComboFlg"]:
                addText = '初见FC'
            else:
                addText = 'Clear'
        else:
            addText = ''

        text += f"{otherStyleTime}: {idtoname(musics['musicId'])} [{musics['musicDifficulty'].upper()}] {musics['playType']} {addText}\n"
        if count == 30:
            break
    text += '由于pjsk统计机制的问题会导致统计不全'
    from imageutils import text2image
    infopic = text2image(text=text, max_width=1400, padding=(20, 10))
    infopic.save(f'piccache/{userid}r30.png')
    if env != 'prod':
        infopic.show()
    return f'{userid}r30'


def daibu(targetid=None, secret=False, server='jp', qqnum='未知'):
    if not verifyid(targetid, server):
        return '你这ID有问题啊'
    try:
        profile = userprofile()
        profile.getprofile(targetid, server, qqnum, query_type='daibu')
    except (JSONDecodeError, IndexError):
        return '未找到玩家'
    if secret:
        text = f"{profile.name}\n"
    else:
        text = f"{profile.name} - {targetid}\n"
    text = text + f"expert进度:FC {profile.full_combo[3]}/{profile.clear[3]}," \
                  f" AP{profile.full_perfect[3]}/{profile.clear[3]}\n" \
                  f"master进度:FC {profile.full_combo[4]}/{profile.clear[4]}," \
                  f" AP{profile.full_perfect[4]}/{profile.clear[4]}\n"
    # 32ap = profile.masterscore[32][0]
    # 32fc = profile.masterscore[32][1]
    ap33plus = profile.masterscore[33][0] + profile.masterscore[34][0] + profile.masterscore[35][0] + \
               profile.masterscore[36][0] + profile.masterscore[37][0]
    fc33plus = profile.masterscore[33][1] + profile.masterscore[34][1] + profile.masterscore[35][1] + \
               profile.masterscore[36][1] + profile.masterscore[37][1]
    if ap33plus != 0:
        text = text + f"\nLv.33及以上AP进度：{ap33plus}/{profile.masterscore[33][3] + profile.masterscore[34][3] + profile.masterscore[35][3] + profile.masterscore[36][3] + profile.masterscore[37][3]}"
    if fc33plus != 0:
        text = text + f"\nLv.33及以上FC进度：{fc33plus}/{profile.masterscore[33][3] + profile.masterscore[34][3] + profile.masterscore[35][3] + profile.masterscore[36][3] + profile.masterscore[37][3]}"
    if profile.masterscore[32][0] != 0:
        text = text + f"\nLv.32AP进度：{profile.masterscore[32][0]}/{profile.masterscore[32][3]}"
    if profile.masterscore[32][1] != 0:
        text = text + f"\nLv.32FC进度：{profile.masterscore[32][1]}/{profile.masterscore[32][3]}"
    # if server == 'jp':
    #     text = text + "\n\n" + rk(targetid, None, secret, True)
    
    return text


def rk(targetid=None, targetrank=None, secret=False, isdaibu=False, qqnum="未知", server='jp'):
    if server in rank_query_ban_servers:
        raise QueryBanned(server)
    rankmatchid = currentrankmatch(server)
    print(rankmatchid)
    if rankmatchid is None:
        return 'no rank match now'
    if targetid is not None:
        if not verifyid(targetid, server):
            return 'wrong id, please check'
        data = callapi(f'/user/%7Buser_id%7D/rank-match-season/{rankmatchid}/'
                            f'ranking?targetUserId={targetid}', server)
    else:
        data = callapi(f'/user/%7Buser_id%7D/rank-match-season/{rankmatchid}/'
                            f'ranking?targetRank={targetrank}', server)
    try:
        ranking = data['rankings'][0]['userRankMatchSeason']
        grade = int((ranking['rankMatchTierId'] - 1) / 4) + 1
        if not recordname(qqnum, data['rankings'][0]['userId'], data['rankings'][0]['name']):
            data['rankings'][0]['name'] = ''
    except IndexError:
        return 'Not participating in current rank match'
    if grade > 7:
        grade = 7
    gradename = rankmatchgrades[grade]
    kurasu = ranking['rankMatchTierId'] - 4 * (grade - 1)
    if not kurasu:
        kurasu = 4
    winrate = ranking['winCount'] / (ranking['winCount'] + ranking['loseCount'])
    if not isdaibu:
        if targetid is None:
            text = data['rankings'][0]['name'] + '\n'
        else:
            if secret:
                text = f"{data['rankings'][0]['name']}\n"
            else:
                text = f"{data['rankings'][0]['name']} - {data['rankings'][0]['userId']}\n"
    else:
        text = ''
    if grade == 7:
        text = text + f"{gradename}🎵×{ranking['tierPoint']}\nrank：{data['rankings'][0]['rank']}\n"
    else:
        text = text + f"{gradename}Class {kurasu}({ranking['tierPoint']}/5)\nrank：{data['rankings'][0]['rank']}\n"
    text = text + f"Win {ranking['winCount']} | Draw {ranking['drawCount']} | "
    if ranking['penaltyCount'] == 0:
        text = text + f"Lose {ranking['loseCount']}\n"
    else:
        text = text + f"Lose {ranking['loseCount'] - ranking['penaltyCount']}+{ranking['penaltyCount']}\n"
    text = text + f'Winning rate (excluding draws)：{round(winrate * 100, 2)}%\n'
    text = text + f"Highest winning streak：{ranking['maxConsecutiveWinCount']}\n"
    return text


def jinduChart(score):
    try:
        del score['33+musicId']
    except KeyError:
        pass

    delLevel = []
    for level in score:
        if score[level][3] == 0:
            delLevel.append(level)

    for level in delLevel:
        del score[level]

    pic = Image.new("RGBA", (50 + 40 * len(score), 220), (0, 0, 0, 0))
    i = 0

    font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 18)
    draw = ImageDraw.Draw(pic)
    for level in score:
        draw.text((34 + 40 * i, 185), str(level), (0, 0, 0), font)

        # 画总曲数
        draw.rectangle((28 + 40 * i, 40, 60 + 40 * i, 180), fill=(68, 68, 102))
        w = int(font.getsize(str(score[level][3]))[0] / 2)
        draw.text((43 + 40 * i - w, 12), str(score[level][3]), (68, 68, 102), font, stroke_width=2,
                  stroke_fill=(255, 255, 255))

        # Clear
        ratio = score[level][2] / score[level][3]
        draw.rectangle((28 + 40 * i, 180 - int(140 * ratio), 60 + 40 * i, 180), fill=(255, 183, 77))
        if score[level][2] != 0:
            w = int(font.getsize(str(score[level][2]))[0] / 2)
            draw.text((43 + 40 * i - w, 152 - int(140 * ratio)), str(score[level][2]), (255, 183, 77), font,
                      stroke_width=2, stroke_fill=(255, 255, 255))

        # FC
        ratio = score[level][1] / score[level][3]
        draw.rectangle((28 + 40 * i, 180 - int(140 * ratio), 60 + 40 * i, 180), fill=(240, 98, 146))
        if score[level][1] != 0:
            w = int(font.getsize(str(score[level][1]))[0] / 2)
            draw.text((43 + 40 * i - w, 152 - int(140 * ratio)), str(score[level][1]), (240, 98, 146), font,
                      stroke_width=2, stroke_fill=(255, 255, 255))

        # AP
        ratio = score[level][0] / score[level][3]
        draw.rectangle((28 + 40 * i, 180 - int(140 * ratio), 60 + 40 * i, 180), fill=(251, 217, 221))
        if score[level][0] != 0:
            w = int(font.getsize(str(score[level][0]))[0] / 2)
            draw.text((43 + 40 * i - w, 152 - int(140 * ratio)), str(score[level][0]), (100, 181, 246), font,
                      stroke_width=2, stroke_fill=(255, 255, 255))

        i += 1
    return pic


def pjskjindu(userid, private=False, diff='master', server='jp', qqnum='未知'):
    if server in ['tw', 'kr']:
        raise QueryBanned(server)
    profile = userprofile()
    profile.getprofile(userid, server, qqnum, query_type='jindu')
    if private:
        id = '保密'
    else:
        id = userid
    if diff == 'master':
        img = Image.open('pics/bgmaster.png')
    elif diff == 'expert':
        img = Image.open('pics/bgexpert.png')
    elif diff == 'append':
        img = Image.open('pics/bgappend.png')
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    try:
        assetbundleName = ''
        for i in cards:
            if i['id'] == profile.userDecks[0]:
                assetbundleName = i['assetbundleName']
        if profile.special_training[0]:
            cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
        else:
            cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_normal.png')
        cardimg = cardimg.resize((117, 117))
        r, g, b, mask = cardimg.split()
        img.paste(cardimg, (67, 57), mask)
    except FileNotFoundError:
        pass
    draw = ImageDraw.Draw(img)

    if server == 'kr':
        font_style = ImageFont.truetype("fonts/SourceHanSansKR-Bold.otf", 31)
    else:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 31)
    draw.text((216, 55), profile.name, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 15)
    draw.text((216, 105), 'id:' + id, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 26)
    draw.text((314, 138), str(profile.rank), fill=(255, 255, 255), font=font_style)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    if diff == 'master':
        levelmin = 25
    elif diff == 'expert':
        levelmin = 21
        profile.masterscore = profile.expertscore
    elif diff == 'append':
        levelmin = 23
        profile.masterscore = profile.appendscore

    if diff == 'master':
        firstRawCount = 6
    elif diff == 'expert':
        firstRawCount = 5
    elif diff == 'append':
        firstRawCount = 7

    for i in range(0, firstRawCount):
        text_width = font_style.getsize(str(profile.masterscore[i + levelmin][0]))
        text_coordinate = (int(183 - text_width[0] / 2), int(295 + 97 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin][0]), fill=(228, 159, 251), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin][1]))
        text_coordinate = (int(183 + 78 - text_width[0] / 2), int(295 + 97 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin][1]), fill=(254, 143, 249), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin][2]))
        text_coordinate = (int(183 + 2 * 78 - text_width[0] / 2), int(295 + 97 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin][2]), fill=(255, 227, 113), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin][3]))
        text_coordinate = (int(183 + 3 * 78 - text_width[0] / 2), int(295 + 97 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin][3]), fill=(108, 237, 226), font=font_style)


    if diff == 'master':
        secondRawCount = 7
    elif diff == 'expert':
        secondRawCount = 6
    elif diff == 'append':
        secondRawCount = 9
    for i in range(0, secondRawCount):
        text_width = font_style.getsize(str(profile.masterscore[i + levelmin + firstRawCount][0]))
        text_coordinate = (int(683 - text_width[0] / 2), int(300 + 96.4 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin + firstRawCount][0]), fill=(228, 159, 251), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin + firstRawCount][1]))
        text_coordinate = (int(683 + 78 - text_width[0] / 2), int(300 + 96.4 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin + firstRawCount][1]), fill=(254, 143, 249), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin + firstRawCount][2]))
        text_coordinate = (int(683 + 2 * 78 - text_width[0] / 2), int(300 + 96.4 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin + firstRawCount][2]), fill=(255, 227, 113), font=font_style)

        text_width = font_style.getsize(str(profile.masterscore[i + levelmin + firstRawCount][3]))
        text_coordinate = (int(683 + 3 * 78 - text_width[0] / 2), int(300 + 96.4 * i - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.masterscore[i + levelmin + firstRawCount][3]), fill=(108, 237, 226), font=font_style)
    chart = jinduChart(profile.masterscore)
    r,g,b,mask = chart.split()
    if diff == 'expert':
        img.paste(chart, (280 - int(chart.size[0] / 2), 732), mask)
    elif diff == 'append':
        img.paste(chart, (280 - int(chart.size[0] / 2), 920), mask)
    elif diff == 'master':
        img.paste(chart, (280 - int(chart.size[0] / 2), 824), mask)
        

    if server in rank_query_ban_servers and not profile.isNewData:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 25)
        updatetime = time.localtime(os.path.getmtime(f'{suite_uploader_path}{userid}.json'))
        draw.text((68, 10), '数据上传时间：' + time.strftime("%Y-%m-%d %H:%M:%S", updatetime),
                   fill=(100, 100, 100), font=font_style)
    if env != 'prod':
        img.show()
    img.save(f'piccache/{userid}jindu.png')


def pjskprofile(userid, private=False, server='jp', qqnum='未知', is_force_update=False, group_id=None):
    new_profile_servers = ['jp', 'tw', 'kr']
    profile = userprofile()
    profile.getprofile(userid, server, qqnum, is_force_update=is_force_update)
    if not recordhitokoto(qqnum, userid, profile.word):
        profile.word = ''
    if not recordname(qqnum, userid, profile.twitterId):
        profile.twitterId = ''
    if private:
        id = '保密'
    else:
        id = userid
    if server in new_profile_servers:
        img = Image.open('pics/pjskprofile_new.png')
    else:
        img = Image.open('pics/bg.png')
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    try:
        assetbundleName = ''
        for i in cards:
            if i['id'] == profile.userDecks[0]:
                assetbundleName = i['assetbundleName']
        if profile.special_training[0]:
            cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
        else:
            cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_normal.png')
        cardimg = cardimg.resize((151, 151))
        r, g, b, mask = cardimg.split()
        img.paste(cardimg, (118, 51), mask)
    except FileNotFoundError:
        pass
    draw = ImageDraw.Draw(img)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 45)
    draw.text((295, 45), profile.name, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 20)
    draw.text((298, 116), 'id:' + id, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 34)
    draw.text((415, 157), str(profile.rank), fill=(255, 255, 255), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 22)
    draw.text((182, 318), str(profile.twitterId), fill=(0, 0, 0), font=font_style)

    if server == 'kr':
        font_style = ImageFont.truetype("fonts/SourceHanSansKR-Medium.otf", 24)
    else:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Medium.otf", 24)
    size = font_style.getsize(profile.word)
    if size[0] > 480:
        draw.text((132, 388), profile.word[:int(len(profile.word) * (460 / size[0]))], fill=(0, 0, 0), font=font_style)
        draw.text((132, 424), profile.word[int(len(profile.word) * (460 / size[0])):], fill=(0, 0, 0), font=font_style)
    else:
        draw.text((132, 388), profile.word, fill=(0, 0, 0), font=font_style)

    for i in range(0, 5):
        try:
            assetbundleName = ''
            for j in cards:
                if j['id'] == profile.userDecks[i]:
                    assetbundleName = j['assetbundleName']
            if profile.special_training[i]:
                cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                     f'/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
            else:
                cardimg = Image.open('data/assets/sekai/assetbundle/resources'
                                     f'/startapp/thumbnail/chara/{assetbundleName}_normal.png')
            # cardimg = cardimg.resize((151, 151))
            r, g, b, mask = cardimg.split()
            img.paste(cardimg, (111 + 128 * i, 488), mask)
        except FileNotFoundError:
            pass
    
    if server in new_profile_servers:
        font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 24)
        for i in range(0, 5):
            text_width = font_style.getsize(str(profile.clear[i]))
            text_coordinate = (int(167 + 105 * i - text_width[0] / 2), int(732 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.clear[i]), fill=(0, 0, 0), font=font_style)

            text_width = font_style.getsize(str(profile.full_combo[i]))
            text_coordinate = (int(167 + 105 * i - text_width[0] / 2), int(732 + 133 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.full_combo[i]), fill=(0, 0, 0), font=font_style)

            text_width = font_style.getsize(str(profile.full_perfect[i]))
            text_coordinate = (int(167 + 105 * i - text_width[0] / 2), int(732 + 2 * 133 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.full_perfect[i]), fill=(0, 0, 0), font=font_style)

        text_width = font_style.getsize(str(profile.clear[5]))
        text_coordinate = (int(707 - text_width[0] / 2), int(732 - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.clear[5]), fill=(0, 0, 0), font=font_style)

        text_width = font_style.getsize(str(profile.full_combo[5]))
        text_coordinate = (int(707 - text_width[0] / 2), int(732 + 133 - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.full_combo[5]), fill=(0, 0, 0), font=font_style)

        text_width = font_style.getsize(str(profile.full_perfect[5]))
        text_coordinate = (int(707 - text_width[0] / 2), int(732 + 2 * 133 - text_width[1] / 2))
        draw.text(text_coordinate, str(profile.full_perfect[5]), fill=(0, 0, 0), font=font_style)
        

    else:
        font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 27)
        for i in range(0, 5):
            text_width = font_style.getsize(str(profile.clear[i]))
            text_coordinate = (int(170 + 132 * i - text_width[0] / 2), int(735 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.clear[i]), fill=(0, 0, 0), font=font_style)

            text_width = font_style.getsize(str(profile.full_combo[i]))
            text_coordinate = (int(170 + 132 * i - text_width[0] / 2), int(735 + 133 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.full_combo[i]), fill=(0, 0, 0), font=font_style)

            text_width = font_style.getsize(str(profile.full_perfect[i]))
            text_coordinate = (int(170 + 132 * i - text_width[0] / 2), int(735 + 2 * 133 - text_width[1] / 2))
            draw.text(text_coordinate, str(profile.full_perfect[i]), fill=(0, 0, 0), font=font_style)

    character = 0
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 29)
    if server in new_profile_servers:
        for i in range(0, 5):
            for j in range(0, 4):
                character = character + 1
                characterRank = 0
                for charas in profile.characterRank:
                    if charas['characterId'] == character:
                        characterRank = charas['characterRank']
                        break
                text_width = font_style.getsize(str(characterRank))
                text_coordinate = (int(916 + 184 * j - text_width[0] / 2), int(688 + 87.5 * i - text_width[1] / 2))
                draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
        for i in range(0, 2):
            for j in range(0, 4):
                character = character + 1
                characterRank = 0
                for charas in profile.characterRank:
                    if charas['characterId'] == character:
                        characterRank = charas['characterRank']
                        break
                text_width = font_style.getsize(str(characterRank))
                text_coordinate = (int(916 + 184 * j - text_width[0] / 2), int(512 + 88 * i - text_width[1] / 2))
                draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
                if character == 26:
                    break
    else:
        for i in range(0, 5):
            for j in range(0, 4):
                character = character + 1
                characterRank = 0
                for charas in profile.characterRank:
                    if charas['characterId'] == character:
                        characterRank = charas['characterRank']
                        break
                text_width = font_style.getsize(str(characterRank))
                text_coordinate = (int(920 + 183 * j - text_width[0] / 2), int(686 + 88 * i - text_width[1] / 2))
                draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
        for i in range(0, 2):
            for j in range(0, 4):
                character = character + 1
                characterRank = 0
                for charas in profile.characterRank:
                    if charas['characterId'] == character:
                        characterRank = charas['characterRank']
                        break
                text_width = font_style.getsize(str(characterRank))
                text_coordinate = (int(920 + 183 * j - text_width[0] / 2), int(510 + 88 * i - text_width[1] / 2))
                draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
                if character == 26:
                    break

    draw.text((952, 141), f'{profile.mvpCount}回', fill=(0, 0, 0), font=font_style)
    draw.text((1259, 141), f'{profile.superStarCount}回', fill=(0, 0, 0), font=font_style)
    try:
        chara = Image.open(f'chara/chr_ts_{profile.characterId}.png')
        chara = chara.resize((70, 70))
        r, g, b, mask = chara.split()
        img.paste(chara, (952, 293), mask)
        draw.text((1032, 315), str(profile.highScore), fill=(0, 0, 0), font=font_style)
    except:
        pass
    for i in profile.userProfileHonors:
        if i['seq'] == 1:
            try:
                honorpic = generatehonor(i, True, server, profile.userHonorMissions)
                honorpic = honorpic.resize((266, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (104, 228), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 2:
            try:
                honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                honorpic = honorpic.resize((126, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (375, 228), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 3:
            try:
                honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                honorpic = honorpic.resize((126, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (508, 228), mask)
            except:
                pass
    if server in rank_query_ban_servers and not profile.isNewData:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 25)
        updatetime = time.localtime(os.path.getmtime(f'{suite_uploader_path}{userid}.json'))
        draw.text((118, 10), '数据上传时间：' + time.strftime("%Y-%m-%d %H:%M:%S", updatetime) + '  实时数据可使用“pjskprofile2”',
                   fill=(100, 100, 100), font=font_style)
    img = img.convert('RGB')
    if env != 'prod':
        img.show()
    img.save(f'piccache/{userid}profile.jpg', quality=80)
    return


def generatehonor(honor, ismain=True, server='jp', userHonorMissions=None):
    star = False
    backgroundAssetbundleName = ''
    frameName = ''
    assetbundleName = ''
    groupId = 0
    honorRarity = 0
    honorType = ''
    honor['profileHonorType'] = honor.get('profileHonorType', 'normal')

    is_live_master = False
    if server == 'jp':
        masterdatadir = 'masterdata'
    elif server == 'en':
        masterdatadir = '../enapi/masterdata'
    elif server == 'tw':
        masterdatadir = 'masterdata'
    if honor['profileHonorType'] == 'normal':
        # 普通牌子
        with open(f'{masterdatadir}/honors.json', 'r', encoding='utf-8') as f:
            honors = json.load(f)
        with open(f'{masterdatadir}/honorGroups.json', 'r', encoding='utf-8') as f:
            honorGroups = json.load(f)
        for i in honors:
            if i['id'] == honor['honorId']:
                try:
                    assetbundleName = i['assetbundleName']
                    honorRarity = i['honorRarity']
                    try:
                        level2 = i['levels'][1]['level']
                        star = True
                    except IndexError:
                        pass

                    for j in honorGroups:
                        if j['id'] == i['groupId']:
                            try:
                                backgroundAssetbundleName = j['backgroundAssetbundleName']
                            except KeyError:
                                backgroundAssetbundleName = ''
                            
                            try:
                                frameName = j['frameName']
                            except KeyError:
                                pass
                            honorType = j['honorType']
                            break
                    filename = 'honor'
                    mainname = 'rank_main.png'
                    subname = 'rank_sub.png'
                except KeyError:
                    honorMissionType = i['honorMissionType']
                    for level in i['levels']:
                        if honor['honorLevel'] == level['level']:
                            assetbundleName = level['assetbundleName']
                            honorRarity = level['honorRarity']
                    filename = 'honor'
                    mainname = 'scroll.png'
                    subname = 'scroll.png'
                    is_live_master = True
        if honorType == 'rank_match':
            filename = 'rank_live/honor'
            mainname = 'main.png'
            subname = 'sub.png'
        # 数据读取完成
        if ismain:
            # 大图
            if honorRarity == 'low':
                path = 'pics/frame_degree_m_1.png'
            elif honorRarity == 'middle':
                path = 'pics/frame_degree_m_2.png'
            elif honorRarity == 'high':
                path = 'pics/frame_degree_m_3.png'
            else:
                path = 'pics/frame_degree_m_4.png'

            # 检查带 frameName 的路径是否存在
            full_path = 'data/assets/sekai/assetbundle/resources/startapp/honor_frame/' + frameName + path[4:]
            print(full_path, os.path.exists(full_path))
            if os.path.exists(full_path):
                frame = Image.open(full_path)
            else:
                frame = Image.open(path)  # 如果文件不存在，只打开默认图片
            if backgroundAssetbundleName == '':
                rankpic = None
                pic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{assetbundleName}/degree_main.png')
                try:
                    rankpic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                         f'/startapp/{filename}/{assetbundleName}/{mainname}')
                except FileNotFoundError:
                    pass
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                if rankpic is not None:
                    r, g, b, mask = rankpic.split()
                    if is_live_master:
                        pic.paste(rankpic, (218, 3), mask)
                        for i in userHonorMissions:
                            if honorMissionType == i['honorMissionType']:
                                progress = i['progress']
                        draw = ImageDraw.Draw(pic)
                        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 20)
                        text_width = font_style.getsize(str(progress))
                        text_coordinate = (int(270 - text_width[0] / 2), int(58 - text_width[1] / 2))
                        draw.text(text_coordinate, str(progress), fill=(255, 255, 255), font=font_style)
                        
                        star_count = (progress // 10) % 10 + 1
                        stars_pos = [
                            (223, 68), (216, 56), (208, 42), (216, 27), (223, 13),
                            (295, 68), (304, 56), (311, 42), (303, 27), (295, 13)
                        ]

                        with_star = Image.open('pics/live_master_honor_star_1.png')
                        with_star_alpha = with_star.split()[3]
                        without_star = Image.open('pics/live_master_honor_star_2.png')
                        without_star_alpha = without_star.split()[3]

                        for i in range(10):
                            if star_count <= i:
                                star_pic, star_alpha = without_star, without_star_alpha
                            else:
                                star_pic, star_alpha = with_star, with_star_alpha
                            pic.paste(star_pic, (stars_pos[i][0], stars_pos[i][1] - 8), star_alpha)
                    else:
                        pic.paste(rankpic, (190, 0), mask)
            else:
                pic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{backgroundAssetbundleName}/degree_main.png')
                rankpic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                     f'/startapp/{filename}/{assetbundleName}/{mainname}')
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                r, g, b, mask = rankpic.split()
                if rankpic.width == 380:
                    pic.paste(rankpic, (0, 0), mask)
                else:
                    pic.paste(rankpic, (190, 0), mask)
            if honorType == 'character' or honorType == 'achievement':
                honorlevel = honor['honorLevel']
                if star is True:
                    if honorlevel > 10:
                        honorlevel = honorlevel - 10
                    if honorlevel < 5:
                        for i in range(0, honorlevel):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                    else:
                        for i in range(0, 5):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                        for i in range(0, honorlevel - 5):
                            lv = Image.open('pics/icon_degreeLv6.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
        else:
            # 小图         
            if honorRarity == 'low':
                path = 'pics/frame_degree_s_1.png'
            elif honorRarity == 'middle':
                path = 'pics/frame_degree_s_2.png'
            elif honorRarity == 'high':
                path = 'pics/frame_degree_s_3.png'
            else:
                path = 'pics/frame_degree_s_4.png'

            # 检查带 frameName 的路径是否存在
            full_path = 'data/assets/sekai/assetbundle/resources/startapp/honor_frame/' + frameName + path[4:]
            if os.path.exists(full_path):
                frame = Image.open(full_path)
            else:
                frame = Image.open(path)  # 如果文件不存在，只打开默认图片
            if backgroundAssetbundleName == '':
                rankpic = None
                pic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{assetbundleName}/degree_sub.png')
                try:
                    rankpic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                         f'/startapp/{filename}/{assetbundleName}/{subname}')
                except FileNotFoundError:
                    pass
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                if rankpic is not None:
                    r, g, b, mask = rankpic.split()
                    if is_live_master:
                        pic.paste(rankpic, (40, 3), mask)
                        for i in userHonorMissions:
                            if honorMissionType == i['honorMissionType']:
                                progress = i['progress']
                        draw = ImageDraw.Draw(pic)
                        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 20)
                        text_width = font_style.getsize(str(progress))
                        text_coordinate = (int(90 - text_width[0] / 2), int(58 - text_width[1] / 2))
                        draw.text(text_coordinate, str(progress), fill=(255, 255, 255), font=font_style)
                    else:
                        pic.paste(rankpic, (34, 42), mask)
            else:
                pic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{backgroundAssetbundleName}/degree_sub.png')
                rankpic = gethonorasset(server, 'data/assets/sekai/assetbundle/resources'
                                     f'/startapp/{filename}/{assetbundleName}/{subname}')
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                r, g, b, mask = rankpic.split()
                print(rankpic.height)
                if rankpic.height == 80:
                    pic.paste(rankpic, (0, 0), mask)
                else:
                    pic.paste(rankpic, (34, 42), mask)
            if honorType == 'character' or honorType == 'achievement':
                if star is True:
                    honorlevel = honor['honorLevel']
                    if honorlevel > 10:
                        honorlevel = honorlevel - 10
                    if honorlevel < 5:
                        for i in range(0, honorlevel):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                    else:
                        for i in range(0, 5):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                        for i in range(0, honorlevel - 5):
                            lv = Image.open('pics/icon_degreeLv6.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
    elif honor['profileHonorType'] == 'bonds':
        # cp牌子
        with open(f'{masterdatadir}/bondsHonors.json', 'r', encoding='utf-8') as f:
            bondsHonors = json.load(f)
            for i in bondsHonors:
                if i['id'] == honor['honorId']:
                    gameCharacterUnitId1 = i['gameCharacterUnitId1']
                    gameCharacterUnitId2 = i['gameCharacterUnitId2']
                    honorRarity = i['honorRarity']
                    break
        if ismain:
            # 大图
            if honor['bondsHonorViewType'] == 'reverse':
                pic = bondsbackground(gameCharacterUnitId2, gameCharacterUnitId1)
            else:
                pic = bondsbackground(gameCharacterUnitId1, gameCharacterUnitId2)
            chara1 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId1).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId1).zfill(2)}_01.png')
            chara2 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId2).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId2).zfill(2)}_01.png')
            if honor['bondsHonorViewType'] == 'reverse':
                chara1, chara2 = chara2, chara1
            r, g, b, mask = chara1.split()
            pic.paste(chara1, (0, -40), mask)
            r, g, b, mask = chara2.split()
            pic.paste(chara2, (220, -40), mask)
            maskimg = Image.open('pics/mask_degree_main.png')
            r, g, b, mask = maskimg.split()
            pic.putalpha(mask)
            if honorRarity == 'low':
                frame = Image.open('pics/frame_degree_m_1.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_m_2.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_m_3.png')
            else:
                frame = Image.open('pics/frame_degree_m_4.png')
            r, g, b, mask = frame.split()
            if honorRarity == 'low':
                pic.paste(frame, (8, 0), mask)
            else:
                pic.paste(frame, (0, 0), mask)
            wordbundlename = f"honorname_{str(gameCharacterUnitId1).zfill(2)}" \
                             f"{str(gameCharacterUnitId2).zfill(2)}_{str(honor['bondsHonorWordId']%100).zfill(2)}_01"
            word = Image.open('data/assets/sekai/assetbundle/resources/startapp'
                                 f'/bonds_honor/word/{wordbundlename}.png')
            r, g, b, mask = word.split()
            pic.paste(word, (int(190-(word.size[0]/2)), int(40-(word.size[1]/2))), mask)
            if honor['honorLevel'] < 5:
                for i in range(0, honor['honorLevel']):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
            else:
                for i in range(0, 5):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
                for i in range(0, honor['honorLevel'] - 5):
                    lv = Image.open('pics/icon_degreeLv6.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
        else:
            # 小图
            if honor['bondsHonorViewType'] == 'reverse':
                pic = bondsbackground(gameCharacterUnitId2, gameCharacterUnitId1, False)
            else:
                pic = bondsbackground(gameCharacterUnitId1, gameCharacterUnitId2, False)
            chara1 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId1).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId1).zfill(2)}_01.png')
            chara2 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId2).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId2).zfill(2)}_01.png')
            if honor['bondsHonorViewType'] == 'reverse':
                chara1, chara2 = chara2, chara1
            chara1 = chara1.resize((120, 102))
            r, g, b, mask = chara1.split()
            pic.paste(chara1, (-5, -20), mask)
            chara2 = chara2.resize((120, 102))
            r, g, b, mask = chara2.split()
            pic.paste(chara2, (60, -20), mask)
            maskimg = Image.open('pics/mask_degree_sub.png')
            r, g, b, mask = maskimg.split()
            pic.putalpha(mask)
            if honorRarity == 'low':
                frame = Image.open('pics/frame_degree_s_1.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_s_2.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_s_3.png')
            else:
                frame = Image.open('pics/frame_degree_s_4.png')
            r, g, b, mask = frame.split()
            if honorRarity == 'low':
                pic.paste(frame, (8, 0), mask)
            else:
                pic.paste(frame, (0, 0), mask)
            if honor['honorLevel'] < 5:
                for i in range(0, honor['honorLevel']):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
            else:
                for i in range(0, 5):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
                for i in range(0, honor['honorLevel'] - 5):
                    lv = Image.open('pics/icon_degreeLv6.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
    return pic

def gethonorasset(server, path):
    if server == 'jp':
        return Image.open(path)
    if 'bonds_honor' in path:  # 没解出来 之后再改
        return Image.open(path)
    else:
        path = path.replace('startapp/honor', f'startapp/{server}honor').replace('startapp/honor', f'startapp/{server}honor')
        if os.path.exists(path):
            return Image.open(path)
        else:
            dirs = os.path.abspath(os.path.join(path, ".."))
            foldername = dirs[dirs.find(f'{server}honor') + len(f'{server}honor') + 1:]
            filename = path[path.find(foldername) + len(foldername) + 1:]
            try:
                if server == 'tw':
                    print(f'download from https://storage.sekai.best/sekai-tc-assets/honor/{foldername}_rip/{filename}')
                    resp = requests.get(f"https://storage.sekai.best/sekai-tc-assets/honor/{foldername}_rip/{filename}",
                                       proxies=proxies, timeout=3)
                elif server == 'en':
                    print(f'download from https://storage.sekai.best/sekai-en-assets/honor/{foldername}_rip/{filename}')
                    resp = requests.get(f"https://storage.sekai.best/sekai-en-assets/honor/{foldername}_rip/{filename}",
                                        proxies=proxies, timeout=3)
            except:
                return Image.open(path.replace('{server}honor', 'honor'))
            if resp.status_code == 200:  # 下载到了
                pic = Image.open(io.BytesIO(resp.content))
                if not os.path.exists(dirs):
                    os.makedirs(dirs)
                pic.save(path)
                return pic
            else:
                return Image.open(path)


def bondsbackground(chara1, chara2, ismain=True):
    if ismain:
        pic1 = Image.open(f'bonds/{str(chara1)}.png')
        pic2 = Image.open(f'bonds/{str(chara2)}.png')
        pic2 = pic2.crop((190, 0, 380, 80))
        pic1.paste(pic2, (190, 0))
    else:
        pic1 = Image.open(f'bonds/{str(chara1)}_sub.png')
        pic2 = Image.open(f'bonds/{str(chara2)}_sub.png')
        pic2 = pic2.crop((90, 0, 380, 80))
        pic1.paste(pic2, (90, 0))
    return pic1


def fcrank(playlevel, rank):
    if playlevel <= 32:
        return rank - 1.5
    # elif rank == 33:
    #     return rank - 0.5
    else:
        return rank - 1

def pjskb30(userid, private=False, returnpic=False, server='jp', qqnum='未知'):
    if server in ['tw', 'kr']:
        raise QueryBanned(server)
    data = callapi(f'/user/{userid}/profile', server, query_type='b30')

    profile = userprofile()
    profile.getprofile(userid, server, qqnum, data)
    pic = Image.open('pics/b30.png')
    if private:
        id = '保密'
    else:
        id = userid
    with open('masterdata/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    try:
        assetbundleName = ''
        for i in cards:
            if i['id'] == profile.userDecks[0]:
                assetbundleName = i['assetbundleName']
        try:
            if profile.special_training[0]:
                cardimg = Image.open(f'{assetpath}/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
                cutoutimg = Image.open(f'{assetpath}/startapp/character/member_cutout_trm/{assetbundleName}/after_training.png')
            else:
                cardimg = Image.open(f'{assetpath}/startapp/thumbnail/chara/{assetbundleName}_normal.png')
                cutoutimg = Image.open(f'{assetpath}/startapp/character/member_cutout_trm/{assetbundleName}/normal.png')
            cutoutimg = cutoutimg.resize((int(cutoutimg.size[0]*0.47), int(cutoutimg.size[1]*0.47)))
            r, g, b, mask = cutoutimg.split()
            pic.paste(cutoutimg, (770, 15), mask)
        except FileNotFoundError:
            pass

        cardimg = cardimg.resize((116, 116))
        r, g, b, mask = cardimg.split()
        pic.paste(cardimg, (68, 70), mask)
    except FileNotFoundError:
        pass
    draw = ImageDraw.Draw(pic)
    if server == 'kr':
        font_style = ImageFont.truetype("fonts/SourceHanSansKR-Bold.otf", 35)
    else:
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    draw.text((215, 65), profile.name, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 15)
    draw.text((218, 118), 'id:' + id, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 28)
    draw.text((314, 150), str(profile.rank), fill=(255, 255, 255), font=font_style)


    for i in profile.userProfileHonors:
        if i['seq'] == 1:
            try:
                honorpic = generatehonor(i, True, server, profile.userHonorMissions)
                honorpic = honorpic.resize((226, 48))
                r, g, b, mask = honorpic.split()
                pic.paste(honorpic, (59, 226), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 2:
            try:
                honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                honorpic = honorpic.resize((107, 48))
                r, g, b, mask = honorpic.split()
                pic.paste(honorpic, (290, 226), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 3:
            try:
                honorpic = generatehonor(i, False, server, profile.userHonorMissions)
                honorpic = honorpic.resize((107, 48))
                r, g, b, mask = honorpic.split()
                pic.paste(honorpic, (403, 226), mask)
            except:
                pass

    with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
        diff = json.load(f)
    for i in range(0, len(diff)):
        try:
            diff[i]['playLevelAdjust']
        except KeyError:
            diff[i]['playLevelAdjust'] = None
            diff[i]['fullComboAdjust'] = None
            diff[i]['fullPerfectAdjust'] = None
    for i in range(0, len(diff)):
        diff[i]['result'] = 0
        diff[i]['rank'] = 0
        if diff[i]['fullComboAdjust'] is not None:
            diff[i]['fclevel+'] = diff[i]['playLevel'] + diff[i]['fullComboAdjust']
            diff[i]['aplevel+'] = diff[i]['playLevel'] + diff[i]['fullPerfectAdjust']
        else:
            diff[i]['fclevel+'] = diff[i]['playLevel']
            diff[i]['aplevel+'] = diff[i]['playLevel']
    if server == 'jp':
        diff.sort(key=lambda x: x["aplevel+"], reverse=True)
        highest = 0
        for i in range(0, 30):
            highest = highest + diff[i]['aplevel+']
        highest = round(highest / 30, 2)
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    for music in data['userMusicResults']:
        playResult = music['playResult']
        musicId = music['musicId']
        musicDifficulty = music['musicDifficulty']
        i = 0
        found = False
        for i in range(0, len(diff)):
            if diff[i]['musicId'] == musicId and diff[i]['musicDifficulty'] == musicDifficulty:
                found = True
                break
        if found:
            if playResult == 'full_perfect':
                diff[i]['result'] = 2
                diff[i]['rank'] = diff[i]['aplevel+']
            elif playResult == 'full_combo':
                if diff[i]['result'] < 1:
                    diff[i]['result'] = 1
                    diff[i]['rank'] = fcrank(diff[i]['playLevel'], diff[i]['fclevel+'])

    diff.sort(key=lambda x: x["rank"], reverse=True)
    rank = 0
    shadow = Image.new("RGBA", (320, 130), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (310, 120), (0, 0, 0, 50)), (5, 5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    if server == 'en':
        with open('../enapi/masterdata/musics.json', 'r', encoding='utf-8') as f:
            musics = json.load(f)
    for i in range(0, 30):
        rank = rank + diff[i]['rank']
        single = b30single(diff[i], musics)
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(52 + (i % 3) * 342)), int(307 + int(i / 3) * 142)), mask)
        pic.paste(single, ((int(53+(i%3)*342)), int(309+int(i/3)*142)))
    rank = round(rank / 30, 2)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Medium.otf", 16)
    if server == 'jp':
        textadd = f'，当前理论值为{highest}'
    else:
        textadd = ''
    draw.text((50, 1722), f'注：33+FC权重减1，其他减1.5，非官方算法，仅供参考娱乐{textadd}', fill='#00CCBB',
              font=font_style)
    draw.text((50, 1752), '定数非官方，可能在之后会有改变', fill='#00CCBB',
              font=font_style)
    
    # 创建一个单独的图层用于绘制rank阴影
    rankimg = Image.new("RGBA", (120, 55), (100, 110, 180, 0))
    draw = ImageDraw.Draw(rankimg)
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    text_width = font_style.getsize(str(rank))
    draw.text((int(60 - text_width[0] / 2), int(20 - text_width[1] / 2)), str(rank), fill=(61, 74, 162, 210),
              font=font_style, stroke_width=2, stroke_fill=(61, 74, 162, 210))
    rankimg = rankimg.filter(ImageFilter.GaussianBlur(1.2))
    draw = ImageDraw.Draw(rankimg)
    draw.text((int(60 - text_width[0] / 2), int(20 - text_width[1] / 2)), str(rank), fill=(255, 255, 255), font=font_style)
    r, g, b, mask = rankimg.split()
    pic.paste(rankimg, (565, 142), mask)

    if server in rank_query_ban_servers and not profile.isNewData:
        draw = ImageDraw.Draw(pic)
        font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 25)
        updatetime = time.localtime(os.path.getmtime(f'{suite_uploader_path}{userid}.json'))
        draw.text((68, 20), '数据上传时间：' + time.strftime("%Y-%m-%d %H:%M:%S", updatetime),
                   fill=(100, 100, 100), font=font_style)

    pic = pic.convert("RGB")
    if returnpic:
        return pic
    pic = pic.convert('RGB')
    pic.save(f'piccache/{userid}b30.jpg')
    if env != 'prod':
        pic.show()

def b30single(diff, musics):
    color = {
        'master': (187, 51, 238),
        'expert': (238, 67, 102),
        'hard': (254, 170, 0),
        'normal': (51, 187, 238),
        'easy': (102, 221, 17),
        'append': (0, 0, 0)
    }
    musictitle = ''
    for j in musics:
        if j['id'] == diff['musicId']:
            musictitle = j['title']
    pic = Image.new("RGB", (620, 240), (255, 255, 255))
    if diff['result'] == 2 or diff['result'] == 1:
        draw = ImageDraw.Draw(pic)
        font = ImageFont.truetype('fonts/YuGothicUI-Semibold.ttf', 48)
        size = font.getsize(musictitle)
        if size[0] > 365:
            musictitle = musictitle[:int(len(musictitle)*(345/size[0]))] + '...'
        draw.text((238, 84), musictitle, '#000000', font)
        # print(musictitle, font.getsize(musictitle))
        jacket = Image.open('%s/startapp/music/jacket/jacket_s_%03d/jacket_s_%03d.png' % (assetpath, diff['musicId'], diff['musicId']))
        jacket = jacket.resize((186, 186))
        pic.paste(jacket, (32, 28))

        draw.ellipse((5, 5, 5+60, 5+60), fill=color[diff['musicDifficulty']])
        font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 38)
        text_width = font.getsize(str(diff['playLevel']))
        text_coordinate = (int(36 - text_width[0] / 2), int(28 - text_width[1] / 2))
        draw.text(text_coordinate, str(diff['playLevel']), (255, 255, 255), font)

        draw.ellipse((242, 32, 286, 76), fill=color[diff['musicDifficulty']])
        draw.rectangle((262, 32, 334, 76), fill=color[diff['musicDifficulty']])
        draw.ellipse((312, 32, 356, 76), fill=color[diff['musicDifficulty']])


        if diff['playLevelAdjust'] is not None:
            if diff['result'] == 2:
                resultpic = Image.open('pics/AllPerfect.png')
                draw.text((259, 24), str(round(diff['aplevel+'], 1)), (255, 255, 255), font)
                draw.text((370, 24), '→ ' + str(round(diff['aplevel+'], 1)), (0, 0, 0), font)
            if diff['result'] == 1:
                resultpic = Image.open('pics/FullCombo.png')
                draw.text((259, 24), str(round(diff['fclevel+'], 1)), (255, 255, 255), font)
                draw.text((370, 24), '→ ' + str(round(fcrank(diff['playLevel'], diff["fclevel+"]), 1)), (0, 0, 0), font)
        else:
            if diff["aplevel+"] < 26 or diff["aplevel+"] > 33:
                draw.text((259, 24), f'  {diff["aplevel+"]}', (255, 255, 255), font)
            else:
                draw.text((259, 24), f'{round(diff["fclevel+"], 1)}.?', (255, 255, 255), font)

            if diff['result'] == 2:
                resultpic = Image.open('pics/AllPerfect.png')
                draw.text((370, 24), f'→ {round(diff["aplevel+"], 1)}.0', (0, 0, 0), font)
            elif diff['result'] == 1:
                resultpic = Image.open('pics/FullCombo.png')
                draw.text((370, 24), f'→ {round(fcrank(diff["playLevel"], diff["fclevel+"]), 1)}', (0, 0, 0), font)
        r, g, b, mask = resultpic.split()
        pic.paste(resultpic, (238, 154), mask)
    pic = pic.resize((310, 120))
    return pic

if __name__ == '__main__':
    pass