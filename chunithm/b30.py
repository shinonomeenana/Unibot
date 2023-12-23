from datetime import datetime
import hashlib
import uuid
import pymysql
from modules.mysql_config import *
import numpy as np
from chunithm.chuniapi import aime_to_userid, call_chuniapi
import ujson as json
import traceback
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from modules.config import env


def process_user_music_list(user_music_list):
    processed_list = []

    for item in user_music_list:
        detail_list = item["userMusicDetailList"]
        processed_list.extend(detail_list)

    return processed_list


def truncate_two_decimal_places(number):
    str_number = str(number + 0.00000002)
    decimal_index = str_number.find('.')
    if decimal_index != -1:
        str_number = str_number[:decimal_index + 3]  # 保留两位小数
    return float(str_number)


def get_all_music(userid, server):
    uuid_str = str(uuid.uuid4())
    next_index = "0"
    user_music_list = []

    while int(next_index) != -1:
        params = {
            "userId": userid,
            "nextIndex": next_index,
            "maxCount": "300"
        }

        response = call_chuniapi(uuid_str, 'GetUserMusicApi', params, server)
        json_data = response.json()

        user_music_list += json_data["userMusicList"]
        next_index = json_data["nextIndex"]

    return process_user_music_list(user_music_list)


def get_user_data(userid, server):
    params = {
        "userId": userid,
        "segaIdAuthKey": ""
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserPreviewApi', params, server)
    return response.json()
    

def get_user_team(userid, server):
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d")
    params = {
        "userId": userid,
        "playDate": formatted_date
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserTeamApi', params, server)
    return response.json()


def get_user_recent(userid, server):
    params = {
        "userId": userid
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserRecentRatingApi', params, server)
    return response.json()


def calculate_rating(constant, score):
    if score >= 1009000:
        return constant + 2.15
    elif 1007500 <= score < 1009000:
        return constant + 2.0 + 0.15 * (score - 1007500) / 1500
    elif 1005000 <= score < 1007500:
        return constant + 1.5 + 0.5 * (score - 1005000) / 2500
    elif 1000000 <= score < 1005000:
        return constant + 1.0 + 0.5 * (score - 1000000) / 5000
    elif 975000 <= score < 1000000:
        return constant + (score - 975000) / 25000
    elif 925000 <= score < 975000:
        return constant - 3.0 + 3.0 * (score - 925000) / 50000
    elif 900000 <= score < 925000:
        return constant - 5.0 + 2.0 * (score - 900000) / 25000
    elif 800000 <= score < 900000:
        return (constant - 5.0) / 2 + (constant - 5.0) / 2 * (score - 800000) / 100000
    else:
        return 0


# 不全且可能有错，持续更新中
sunp_to_lmn = {
    (2338, 3): 15.1,  # Disruptor Array 15.2-15.1
    (2400, 3): 15.0,  # LAMIA 15.1-15.0
    (428 , 4): 15.2,  # Aleph-0 ULT 15.1-15.2
    (1017, 3): 15.1,  # ANU 15.0-15.1
    (2039, 3): 14.8,  # ]-[|/34<#! 14.9-14.8
    (2336, 3): 14.8,  # 盟月 14.9-14.8
    (2346, 3): 14.7,  # FLUFFY FLASH 14.8-14.7
    (2401, 3): 14.7,  # オンソクデイズ!! 14.8-14.7
    (2351, 3): 14.8,  # Sheriruth 14.7-14.8
    (2353, 3): 14.9,  # 幻想即興曲 14.8-14.9
    (2194, 3): 14.3,  # 蒼穹舞楽 14.5-14.3
    (2338, 2): 14.4,  # Disruptor Array EXP 14.5-14.4
    (2416, 4): 14.4,  # Snow Colored Score ULT 14.2-14.4
    (2242, 3): 14.0,  # キルミーのベイベー！ 13.9-14.0
    (159 , 4): 14.8,  # ジングルベル ULT 14.9-14.8
    (233 , 4): 14.5,  # アルストロメリア ULT 14.4-14.5
    (1079, 2): 14.3,  # X7124 EXP 14.4-14.3
    (2400, 2): 14.1,  # LAMIA EXP 13.9-14.1
    (2407, 2): 14.0,  # Makear EXP 13.9-14.0
    (2364, 3): 14.3,  # MAXRAGE 14.2-14.3
    (2193, 3): 14.1,  # モ°ルモ°ル 14.2-14.1
    (152 , 3): 14.1,  # Gustav Battle 14.2-14.1
    (2406, 3): 14.0,  # ASH 14.1-14.0
    (2356, 3): 14.4,  # Moon of Noon 14.3-14.4
    (141 , 2): 13.5,  # 閃鋼のブリューナク EXP 13.1-13.5
    (2445, 3): 13.1,  # Night Spider 12.9-13.1
    (2336, 2): 12.5,  # 盟月 EXP 12.0-12.5
    (2343, 3): 12.0,  # ワールドイズマイン 11.6-12.0
    (2130, 3): 13.8,  # 崩壊歌姫 -disruptive diva- 13.9-13.8
    (18  , 4): 13.7,  # 千本桜 ULT 13.9-13.7
    (76  , 2): 13.3,  # luna blu EXP 13.1-13.3
    (2254, 3): 13.2,  # 1 13.1-13.2
    (2401, 2): 12.6,  # オンソクデイズ!! EXP 12.3-12.6
    (2078, 3): 11.8,  # I believe what you said 11.7-11.8
    # Pris-Magic! 12.2-12+ 未确认
    # ネトゲ廃人シュプレヒコール 11.9-12+ 未确认
    # MAXRAGE EXP 11.9-12 未确认
    # Snow Colored Score 11.1-11+ 未确认
}


def process_r10(userid, server, version='2.15', sort=True):
    difficulty_mapping = {
        "0": "basic",
        "1": "advanced",
        "2": "expert",
        "3": "master",
        "4": "ultima",
        "5": "worldsend"
    }

    # 读取歌曲信息
    with open("chunithm/masterdata/musics.json", "r", encoding='utf-8') as f:
        musics = json.load(f)
    with open('chunithm/masterdata/musics_local.json', 'r', encoding='utf-8') as f:
        sdhd_music_data = json.load(f)
    music_info = {music['id']: music for music in musics}
    sdhd_music_info = {music['id']: music for music in sdhd_music_data}
    # 解析用户数据
    user_data = get_user_recent(userid, server)  # assuming user_input is your provided user data
    rating_list = []

    if user_data["userRecentRatingList"] == []:
        return rating_list
    # 遍历用户数据，计算rating，并构造需要的数据结构
    for record in user_data["userRecentRatingList"]:
        music_id = record["musicId"]
        difficult_id = record["difficultId"]
        score = int(record["score"])
        isdeleted = False
        try:
            music = music_info[music_id]
        except KeyError:
            try:
                music = sdhd_music_info[music_id]
                isdeleted = True
            except KeyError:
                continue
        difficulty_level = difficulty_mapping[difficult_id]
        if difficulty_level in music['difficulties']:
            difficulty = music['difficulties'][difficulty_level]
            if version == '2.20':
                difficulty = sunp_to_lmn.get((int(music_id), int(difficult_id)), difficulty)
            
            rating = calculate_rating(difficulty, score)
            rating_list.append({
                'musicName': music['name'],
                'jacketFile': music['jaketFile'],
                'playLevel': difficulty,
                'musicDifficulty': difficulty_level,
                'score': score,
                'rating': rating,
                'isdeleted': isdeleted,
            })

    # 将rating_list按照rating降序排序
    if sort:
        rating_list.sort(key=lambda x: x['rating'], reverse=True)
    return rating_list


def process_b30(userid, server, version='2.15'):
    # 获取用户数据
    user_data = get_all_music(userid, server)
    # 读取音乐数据
    with open('chunithm/masterdata/musics.json', 'r', encoding='utf-8') as f:
        music_data = json.load(f)
    
    with open('chunithm/masterdata/musics_local.json', 'r', encoding='utf-8') as f:
        sdhd_music_data = json.load(f)

    # 创建一个字典，以便于从 musicId 找到对应的音乐信息
    music_dict = {music['id']: music for music in music_data}
    sdhd_music_dict = {music['id']: music for music in sdhd_music_data}
    # 存储计算出的 rating
    ratings = []

    for data in user_data:
        music_id = str(data['musicId'])
        level_index = int(data['level'])
        level_dict = {0: "basic", 1: "advanced", 2: "expert", 3: "master", 4: "ultima", 5: "world's end"}
        isdeleted = False
        try:
            music_info = music_dict[music_id]
        except KeyError:
            try:
                music_info = sdhd_music_dict[music_id]
                isdeleted = True
            except KeyError:
                continue
        music_name = music_info['name']
        jacket_file = music_info['jaketFile']
        try:
            difficulty = music_info['difficulties'][level_dict[level_index]]
            if version == '2.20':
                difficulty = sunp_to_lmn.get((int(music_id), int(level_index)), difficulty)
        except KeyError:
            continue
        score = int(data['scoreMax'])
        rating = calculate_rating(difficulty, score)

        ratings.append({
            'musicName': music_name,
            'jacketFile': jacket_file,
            'playLevel': difficulty,
            'musicDifficulty': level_dict[level_index],
            'score': score,
            'rating': rating,
            'isFullCombo': data['isFullCombo'],
            'isAllJustice': data['isAllJustice'],
            'isdeleted': isdeleted,
        })

    ratings.sort(key=lambda x: x['rating'], reverse=True)
    
    return ratings



def chunib30(userid, server='aqua', version='2.15'):
    if version == '2.15':
        pic = Image.open('pics/chub30sunp.png')
    elif version == '2.20':
        pic = Image.open('pics/chub30lmn.png')

    draw = ImageDraw.Draw(pic)

    user_data = get_user_data(userid, server)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    draw.text((215, 65), user_data['userName'], fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 15)
    try:
        if server == 'na':
            draw.text((218, 118), 'CHUNITHM', fill=(0, 0, 0), font=font_style)
        else:
            draw.text((218, 118), get_user_team(userid, server)['teamName'], fill=(0, 0, 0), font=font_style)
    except KeyError:
        draw.text((218, 118), 'CHUNITHM', fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 28)
    draw.text((314, 150), str(int(user_data['level']) + int(user_data['reincarnationNum']) * 100), fill=(255, 255, 255), font=font_style)
    
    shadow = Image.new("RGBA", (320, 130), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (280, 105), (0, 0, 0, 50)), (5, 5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))

    ratings = process_b30(userid, server, version)
    # ratings = [{'musicName': 'SINister Evolution', 'jacketFile': 'CHU_UI_Jacket_2038.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1008040, 'rating': 16.854}, {'musicName': '月の光', 'jacketFile': 'CHU_UI_Jacket_2354.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1007929, 'rating': 16.8429}, {'musicName': '腐れ外道とチョコレゐト', 'jacketFile': 'CHU_UI_Jacket_0118.dds', 'playLevel': 14.7, 'musicDifficulty': 'ultima', 'score': 1008139, 'rating': 16.7639}, {'musicName': 'Last Celebration', 'jacketFile': 'CHU_UI_Jacket_0994.dds', 'playLevel': 14.7, 'musicDifficulty': 'master', 'score': 1007768, 'rating': 16.7268}, {'musicName': '[CRYSTAL_ACCESS]', 'jacketFile': 'CHU_UI_Jacket_1094.dds', 'playLevel': 14.6, 'musicDifficulty': 'master', 'score': 1008204, 'rating': 16.6704}, {'musicName': 'IMPACT', 'jacketFile': 'CHU_UI_Jacket_2135.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1008261, 'rating': 16.5761}, {'musicName': 'AXION', 'jacketFile': 'CHU_UI_Jacket_0863.dds', 'playLevel': 14.6, 'musicDifficulty': 'master', 'score': 1006946, 'rating': 16.4892}, {'musicName': 'POTENTIAL', 'jacketFile': 'CHU_UI_Jacket_2161.dds', 'playLevel': 14.3, 'musicDifficulty': 'expert', 'score': 1009823, 'rating': 16.45}, {'musicName': 'X7124', 'jacketFile': 'CHU_UI_Jacket_1079.dds', 'playLevel': 14.4, 'musicDifficulty': 'expert', 'score': 1007994, 'rating': 16.449399999999997}, {'musicName': "DA'AT -The First Seeker of Souls-", 'jacketFile': 'CHU_UI_Jacket_2241.dds', 'playLevel': 14.6, 'musicDifficulty': 'expert', 'score': 1006734, 'rating': 16.446800000000003}, {'musicName': 'のぼれ！すすめ！高い塔', 'jacketFile': 'CHU_UI_Jacket_0448.dds', 'playLevel': 14.3, 'musicDifficulty': 'master', 'score': 1007988, 'rating': 16.3488}, {'musicName': 'サドマミホリック', 'jacketFile': 'CHU_UI_Jacket_0628.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1008416, 'rating': 16.2916}, {'musicName': 'Jade Star', 'jacketFile': 'CHU_UI_Jacket_0966.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1008359, 'rating': 16.285899999999998}, {'musicName': 'U&iVERSE -銀河鸞翔-', 'jacketFile': 'CHU_UI_Jacket_2326.dds', 'playLevel': 14.4, 'musicDifficulty': 'master', 'score': 1006782, 'rating': 16.2564}, {'musicName': 'グラ ウンドスライダー協奏曲第一番「風唄」', 'jacketFile': 'CHU_UI_Jacket_2279.dds', 'playLevel': 14.1, 'musicDifficulty': 'expert', 'score': 1009496, 'rating': 16.25}, {'musicName': 'レータイス パークEx', 'jacketFile': 'CHU_UI_Jacket_0980.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1007745, 'rating': 16.2245}, {'musicName': 'Elemental Creation', 'jacketFile': 'CHU_UI_Jacket_0232.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1006070, 'rating': 16.214}, {'musicName': 'Insane Gamemode', 'jacketFile': 'CHU_UI_Jacket_1015.dds', 'playLevel': 14.4, 'musicDifficulty': 'master', 'score': 1006556, 'rating': 16.2112}, {'musicName': 'Name of oath', 'jacketFile': 'CHU_UI_Jacket_0389.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1006045, 'rating': 16.209}, {'musicName': '真千年女王', 'jacketFile': 'CHU_UI_Jacket_1092.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1004047, 'rating': 16.2047}, {'musicName': 'エンドマークに希望と涙を添えて', 'jacketFile': 'CHU_UI_Jacket_0103.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1003759, 'rating': 16.175900000000002}, {'musicName': 'ヒバナ', 'jacketFile': 'CHU_UI_Jacket_0818.dds', 'playLevel': 14.0, 'musicDifficulty': 'ultima', 'score': 1009809, 'rating': 16.15}, {'musicName': '宵闇の月に抱かれて', 'jacketFile': 'CHU_UI_Jacket_2158.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008818, 'rating': 16.1318}, {'musicName': 'Athlete Killer "Meteor"', 'jacketFile': 'CHU_UI_Jacket_1065.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008811, 'rating': 16.1311}, {'musicName': '二次元ドリームフィーバー', 'jacketFile': 'CHU_UI_Jacket_2037.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008691, 'rating': 16.1191}, {'musicName': '天火明命', 'jacketFile': 'CHU_UI_Jacket_2144.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008194, 'rating': 16.0694}, {'musicName': 'ENDYMION', 'jacketFile': 'CHU_UI_Jacket_2184.dds', 'playLevel': 14.4, 'musicDifficulty': 'expert', 'score': 1005841, 'rating': 16.0682}, {'musicName': 'Taiko Drum Monster', 'jacketFile': 'CHU_UI_Jacket_0671.dds', 'playLevel': 14.3, 'musicDifficulty': 'master', 'score': 1006288, 'rating': 16.0576}, {'musicName': 'Aleph-0', 'jacketFile': 'CHU_UI_Jacket_0428.dds', 'playLevel': 14.1, 'musicDifficulty': 'expert', 'score': 1007247, 'rating': 16.0494}, {'musicName': '再生不能', 'jacketFile': 'CHU_UI_Jacket_1105.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1007977, 'rating': 16.0477}, {'musicName': 'フューチャー・イヴ', 'jacketFile': 'CHU_UI_Jacket_2344.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008964, 'rating': 16.046400000000002}, {'musicName': 'こちら、幸福安心委員会です。', 'jacketFile': 'CHU_UI_Jacket_1068.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008927, 'rating': 16.0427}, {'musicName': 'Rule the World!!', 'jacketFile': 'CHU_UI_Jacket_2109.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1007899, 'rating': 16.0399}, {'musicName': 'FLUFFY FLASH', 'jacketFile': 'CHU_UI_Jacket_2346.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1002058, 'rating': 16.0058}, {'musicName': '電脳少女は歌姫の夢を見るか？', 'jacketFile': 'CHU_UI_Jacket_2019.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1006509, 'rating': 16.0018}, {'musicName': '迷える音色は恋の唄', 'jacketFile': 'CHU_UI_Jacket_2350.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008486, 'rating': 15.9986}, {'musicName': 'トンデモワンダーズ', 'jacketFile': 'CHU_UI_Jacket_2264.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008285, 'rating': 15.9785}, {'musicName': 'SON OF SUN', 'jacketFile': 'CHU_UI_Jacket_0887.dds', 'playLevel': 13.8, 'musicDifficulty': 'expert', 'score': 1009937, 'rating': 15.950000000000001}, {'musicName': 'Ascension to Heaven', 'jacketFile': 'CHU_UI_Jacket_0978.dds', 'playLevel': 13.8, 'musicDifficulty': 'expert', 'score': 1009842, 'rating': 15.950000000000001}, {'musicName': 'Fracture Ray', 'jacketFile': 'CHU_UI_Jacket_0749.dds', 'playLevel': 14.7, 'musicDifficulty': 'master', 'score': 1002027, 'rating': 15.9027}]
    
    rating_sum = 0
    for i in range(0, 30):
        try:
            single = b30single(ratings[i], version)
        except IndexError:
            break
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(52 + (i % 5) * 290)), int(287 + int(i / 5) * 127)), mask)
        pic.paste(single, ((int(53+(i%5)*290)), int(289+int(i/5)*127)))
        rating_sum += ratings[i]['rating']
    b30 = truncate_two_decimal_places(rating_sum / 30)
    b30_accurate = rating_sum / 30
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 37)
    draw.text((208, 205), str(b30), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")

    ratings = process_r10(userid, server, version)
    rating_sum = 0
    for i in range(0, 10):
        try:
            single = b30single(ratings[i], version)
        except IndexError:
            break
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(1582 + (i % 2) * 290)), int(287 + int(i / 2) * 127)), mask)
        pic.paste(single, ((int(1582+(i%2)*290)), int(289+int(i/2)*127)))
        rating_sum += ratings[i]['rating']
    r10 = truncate_two_decimal_places(rating_sum / 10)
    r10_accurate = rating_sum / 10
    draw.text((1726, 205), str(r10), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")
    
    rank = truncate_two_decimal_places((b30_accurate * 3 + r10_accurate) / 4)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Medium.otf", 16)
    
    
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
    pic.paste(rankimg, (492, 110), mask)

    pic = pic.convert("RGB")
    pic.save(f'piccache/{hashlib.sha256(userid.encode()).hexdigest()}b30.jpg')
    if env != 'prod':
        pic.show()

def b30single(single_data, version):
    color = {
        'master': (187, 51, 238),
        'expert': (238, 67, 102),
        'advanced': (254, 170, 0),
        'ultima': (0, 0, 0),
        'basic': (102, 221, 17),
    }
    musictitle = single_data['musicName']
    
    if version == '2.15':
        pic = Image.new("RGB", (620, 240), (255, 250, 243))
    else:
        pic = Image.new("RGB", (620, 240), (255, 255, 255))
    
    jacket = Image.open(f'chunithm/jackets/{single_data["jacketFile"]}')
    jacket = jacket.resize((186, 186))
    pic.paste(jacket, (32, 28))

    draw = ImageDraw.Draw(pic)
    font = ImageFont.truetype('fonts/YuGothicUI-Semibold.ttf', 36)
    size = font.getsize(musictitle)
    if version == '2.20' and single_data['isdeleted']:
        musictitle = '(配信停止)' + musictitle
    if size[0] > 365:
        musictitle = musictitle[:int(len(musictitle)*(345/size[0]))] + '...'
    draw.text((240, 27), musictitle, '#000000', font)

    font = ImageFont.truetype('fonts/FOT-RodinNTLGPro-DB.ttf', 58)
    draw.text((234, 87), str(single_data['score']), '#000000', font)

    font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 38)
    draw.ellipse((242, 165, 286, 209), fill=color[single_data['musicDifficulty']])
    draw.rectangle((262, 165, 334, 209), fill=color[single_data['musicDifficulty']])
    draw.ellipse((312, 165, 356, 209), fill=color[single_data['musicDifficulty']])
    draw.text((259, 157), str(single_data['playLevel']), (255, 255, 255), font)
    draw.text((370, 157), '→ ' + str(truncate_two_decimal_places(single_data['rating'])), (0, 0, 0), font)

    if 'isAllJustice' in single_data:
        font = ImageFont.truetype('fonts/FOT-RodinNTLGPro-DB.ttf', 35)
        if single_data['isAllJustice'] == 'true' or single_data['isAllJustice'] is True:
            draw.text((530, 105), "AJ", '#000000', font)
        elif single_data['isFullCombo'] == 'true' or single_data['isFullCombo'] is True:
            draw.text((530, 105), "FC", '#000000', font)
    pic = pic.resize((280, 105))
    return pic


def chuni_r30(userid, server='aqua', version='2.15'):
    # TODO: r30施工中
    if version == '2.15':
        pic = Image.open('pics/chub30sunp.png')
    else:
        pic = Image.open('pics/chub30.png')
    draw = ImageDraw.Draw(pic)

    user_data = get_user_data(userid, server)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    draw.text((215, 65), user_data['userName'], fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 15)
    try:
        draw.text((218, 118), get_user_team(userid, server)['teamName'], fill=(0, 0, 0), font=font_style)
    except KeyError:
        draw.text((218, 118), 'CHUNITHM', fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 28)
    draw.text((314, 150), str(int(user_data['level']) + int(user_data['reincarnationNum']) * 100), fill=(255, 255, 255), font=font_style)
    
    shadow = Image.new("RGBA", (320, 130), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (280, 105), (0, 0, 0, 50)), (5, 5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))

    # ratings = process_b30(userid, server, version)
    
    # rating_sum = 0
    # for i in range(0, 30):
    #     try:
    #         single = b30single(ratings[i], version)
    #     except IndexError:
    #         break
    #     r, g, b, mask = shadow.split()
    #     pic.paste(shadow, ((int(52 + (i % 5) * 290)), int(287 + int(i / 5) * 127)), mask)
    #     pic.paste(single, ((int(53+(i%5)*290)), int(289+int(i/5)*127)))
    #     rating_sum += ratings[i]['rating']
    # b30 = truncate_two_decimal_places(rating_sum / 30)
    # font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 37)
    # draw.text((208, 205), str(b30), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")

    ratings = process_r10(userid, server, version, sort=False)
    rating_sum = 0
    for i in range(0, 30):
        try:
            single = b30single(ratings[i], version)
        except IndexError:
            break
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(52 + (i % 5) * 290)), int(287 + int(i / 5) * 127)), mask)
        pic.paste(single, ((int(53+(i%5)*290)), int(289+int(i/5)*127)))
        rating_sum += ratings[i]['rating']
    r10 = truncate_two_decimal_places(rating_sum / 10)
    draw.text((1726, 205), str(r10), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")
    
    # rank = truncate_two_decimal_places((b30 * 3 + r10) / 4)

    # font_style = ImageFont.truetype("fonts/SourceHanSansCN-Medium.otf", 16)
    
    
    # # 创建一个单独的图层用于绘制rank阴影
    # rankimg = Image.new("RGBA", (120, 55), (100, 110, 180, 0))
    # draw = ImageDraw.Draw(rankimg)
    # font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    # text_width = font_style.getsize(str(rank))
    # draw.text((int(60 - text_width[0] / 2), int(20 - text_width[1] / 2)), str(rank), fill=(61, 74, 162, 210),
    #           font=font_style, stroke_width=2, stroke_fill=(61, 74, 162, 210))
    # rankimg = rankimg.filter(ImageFilter.GaussianBlur(1.2))
    # draw = ImageDraw.Draw(rankimg)
    # draw.text((int(60 - text_width[0] / 2), int(20 - text_width[1] / 2)), str(rank), fill=(255, 255, 255), font=font_style)
    # r, g, b, mask = rankimg.split()
    # pic.paste(rankimg, (492, 110), mask)

    pic = pic.convert("RGB")
    pic.save(f'piccache/{hashlib.sha256(userid.encode()).hexdigest()}r30.jpg')
    


def get_connection():
    return pymysql.connect(
        host=host, 
        port=port, 
        user='pjsk', 
        password=password,
        database='pjsk', 
        charset='utf8mb4'
    )


database_list = {
        'aqua': 'chunibind',
        'lin': 'linbind',
        'super': 'superbind',
        'na': 'leebind',
        'rin': 'rinbind',
        'mobi': 'mobibind'
    }
# database_list硬编码防止注入。%s会导致表名被加入引号报错

def getchunibind(qqnum, server='aqua'):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT * from {database_list[server]} where qqnum=%s', (qqnum, ))
            data = cursor.fetchone()
            return data[2] if data else None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.close()


def bind_aimeid(qqnum, aimeid, server='aqua'):
    userid = str(aime_to_userid(aimeid, server))
    if userid is None:
        return '卡号不存在'
    user_data = get_user_data(userid, server)
    print(user_data)
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            sql = f"INSERT INTO {database_list[server]} (qqnum, aimeid) VALUES (%s, %s) ON DUPLICATE KEY UPDATE aimeid=%s"
            val = (str(qqnum), str(userid), str(userid))
            cursor.execute(sql, val)
            conn.commit()
            return f"绑定成功！记得撤回卡号哦\n游戏昵称：{user_data['userName']}\n等级：{user_data['level']}"
    except Exception as e:
        traceback.print_exc()
        return "绑定失败！"
    finally:
        conn.close()