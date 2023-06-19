from datetime import datetime
import hashlib
import math
import uuid
import pymysql
from modules.mysql_config import *
import numpy as np
from chunithm.chuniapi import aime_to_userid, call_chuniapi
import ujson as json
import traceback
from PIL import Image, ImageFont, ImageDraw, ImageFilter

def process_user_music_list(user_music_list):
    processed_list = []

    for item in user_music_list:
        detail_list = item["userMusicDetailList"]
        processed_list.extend(detail_list)

    return processed_list


def get_all_music(userid):
    uuid_str = str(uuid.uuid4())
    next_index = "0"
    user_music_list = []

    while next_index != "-1":
        params = {
            "userId": userid,
            "nextIndex": next_index,
            "maxCount": "300"
        }

        response = call_chuniapi(uuid_str, 'GetUserMusicApi', params)
        json_data = response.json()

        user_music_list += json_data["userMusicList"]
        next_index = json_data["nextIndex"]

    return process_user_music_list(user_music_list)


def get_user_data(userid):
    params = {
        "userId": userid,
        "segaIdAuthKey": ""
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserPreviewApi', params)
    return response.json()
    

def get_user_team(userid):
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d")
    params = {
        "userId": userid,
        "playDate": formatted_date
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserTeamApi', params)
    return response.json()


def get_user_recent(userid):
    params = {
        "userId": userid
    }
    response = call_chuniapi(str(uuid.uuid4()), 'GetUserRecentRatingApi', params)
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


def process_r10(userid):
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
    music_info = {music['id']: music for music in musics}

    # 解析用户数据
    user_data = get_user_recent(userid)  # assuming user_input is your provided user data
    rating_list = []

    # 遍历用户数据，计算rating，并构造需要的数据结构
    for record in user_data["userRecentRatingList"]:
        music_id = record["musicId"]
        difficult_id = record["difficultId"]
        score = int(record["score"])
        if music_id in music_info:
            music = music_info[music_id]
            difficulty_level = difficulty_mapping[difficult_id]
            if difficulty_level in music['difficulties']:
                difficulty = music['difficulties'][difficulty_level]
                rating = calculate_rating(difficulty, score)
                rating_list.append({
                    'musicName': music['name'],
                    'jacketFile': music['jaketFile'],
                    'playLevel': difficulty,
                    'musicDifficulty': difficulty_level,
                    'score': score,
                    'rating': rating
                })

    # 将rating_list按照rating降序排序
    rating_list.sort(key=lambda x: x['rating'], reverse=True)

    # 计算最高的10个rating的平均值
    top_10_avg_rating = np.mean([x['rating'] for x in rating_list[:10]])

    # print("Sorted rating list: ", rating_list)
    # print("Top 10 average rating: ", top_10_avg_rating)
    return rating_list


def process_b30(userid):
    # 获取用户数据
    user_data = get_all_music(userid)
    
    # 读取音乐数据
    with open('chunithm/masterdata/musics.json', 'r', encoding='utf-8') as f:
        music_data = json.load(f)

    # 创建一个字典，以便于从 musicId 找到对应的音乐信息
    music_dict = {music['id']: music for music in music_data}

    # 存储计算出的 rating
    ratings = []

    for data in user_data:
        music_id = data['musicId']
        level_index = int(data['level'])
        level_dict = {0: "basic", 1: "advanced", 2: "expert", 3: "master", 4: "ultima", 5: "world's end"}
        try:
            music_info = music_dict[music_id]
        except KeyError:
            continue
        music_name = music_info['name']
        jacket_file = music_info['jaketFile']
        try:
            difficulty = music_info['difficulties'][level_dict[level_index]]
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
            'rating': rating
        })

    ratings.sort(key=lambda x: x['rating'], reverse=True)
    
    return ratings



def chunib30(userid):
    pic = Image.open('pics/chub30.png')
    draw = ImageDraw.Draw(pic)

    user_data = get_user_data(userid)

    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 35)
    draw.text((215, 65), user_data['userName'], fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 15)
    try:
        draw.text((218, 118), get_user_team(userid)['teamName'], fill=(0, 0, 0), font=font_style)
    except KeyError:
        draw.text((218, 118), 'CHUNITHM', fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("fonts/FOT-RodinNTLGPro-DB.ttf", 28)
    draw.text((314, 150), str(user_data['level']), fill=(255, 255, 255), font=font_style)
    
    shadow = Image.new("RGBA", (320, 130), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (280, 105), (0, 0, 0, 50)), (5, 5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))

    ratings = process_b30(userid)
    # ratings = [{'musicName': 'SINister Evolution', 'jacketFile': 'CHU_UI_Jacket_2038.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1008040, 'rating': 16.854}, {'musicName': '月の光', 'jacketFile': 'CHU_UI_Jacket_2354.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1007929, 'rating': 16.8429}, {'musicName': '腐れ外道とチョコレゐト', 'jacketFile': 'CHU_UI_Jacket_0118.dds', 'playLevel': 14.7, 'musicDifficulty': 'ultima', 'score': 1008139, 'rating': 16.7639}, {'musicName': 'Last Celebration', 'jacketFile': 'CHU_UI_Jacket_0994.dds', 'playLevel': 14.7, 'musicDifficulty': 'master', 'score': 1007768, 'rating': 16.7268}, {'musicName': '[CRYSTAL_ACCESS]', 'jacketFile': 'CHU_UI_Jacket_1094.dds', 'playLevel': 14.6, 'musicDifficulty': 'master', 'score': 1008204, 'rating': 16.6704}, {'musicName': 'IMPACT', 'jacketFile': 'CHU_UI_Jacket_2135.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1008261, 'rating': 16.5761}, {'musicName': 'AXION', 'jacketFile': 'CHU_UI_Jacket_0863.dds', 'playLevel': 14.6, 'musicDifficulty': 'master', 'score': 1006946, 'rating': 16.4892}, {'musicName': 'POTENTIAL', 'jacketFile': 'CHU_UI_Jacket_2161.dds', 'playLevel': 14.3, 'musicDifficulty': 'expert', 'score': 1009823, 'rating': 16.45}, {'musicName': 'X7124', 'jacketFile': 'CHU_UI_Jacket_1079.dds', 'playLevel': 14.4, 'musicDifficulty': 'expert', 'score': 1007994, 'rating': 16.449399999999997}, {'musicName': "DA'AT -The First Seeker of Souls-", 'jacketFile': 'CHU_UI_Jacket_2241.dds', 'playLevel': 14.6, 'musicDifficulty': 'expert', 'score': 1006734, 'rating': 16.446800000000003}, {'musicName': 'のぼれ！すすめ！高い塔', 'jacketFile': 'CHU_UI_Jacket_0448.dds', 'playLevel': 14.3, 'musicDifficulty': 'master', 'score': 1007988, 'rating': 16.3488}, {'musicName': 'サドマミホリック', 'jacketFile': 'CHU_UI_Jacket_0628.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1008416, 'rating': 16.2916}, {'musicName': 'Jade Star', 'jacketFile': 'CHU_UI_Jacket_0966.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1008359, 'rating': 16.285899999999998}, {'musicName': 'U&iVERSE -銀河鸞翔-', 'jacketFile': 'CHU_UI_Jacket_2326.dds', 'playLevel': 14.4, 'musicDifficulty': 'master', 'score': 1006782, 'rating': 16.2564}, {'musicName': 'グラ ウンドスライダー協奏曲第一番「風唄」', 'jacketFile': 'CHU_UI_Jacket_2279.dds', 'playLevel': 14.1, 'musicDifficulty': 'expert', 'score': 1009496, 'rating': 16.25}, {'musicName': 'レータイス パークEx', 'jacketFile': 'CHU_UI_Jacket_0980.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1007745, 'rating': 16.2245}, {'musicName': 'Elemental Creation', 'jacketFile': 'CHU_UI_Jacket_0232.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1006070, 'rating': 16.214}, {'musicName': 'Insane Gamemode', 'jacketFile': 'CHU_UI_Jacket_1015.dds', 'playLevel': 14.4, 'musicDifficulty': 'master', 'score': 1006556, 'rating': 16.2112}, {'musicName': 'Name of oath', 'jacketFile': 'CHU_UI_Jacket_0389.dds', 'playLevel': 14.5, 'musicDifficulty': 'master', 'score': 1006045, 'rating': 16.209}, {'musicName': '真千年女王', 'jacketFile': 'CHU_UI_Jacket_1092.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1004047, 'rating': 16.2047}, {'musicName': 'エンドマークに希望と涙を添えて', 'jacketFile': 'CHU_UI_Jacket_0103.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1003759, 'rating': 16.175900000000002}, {'musicName': 'ヒバナ', 'jacketFile': 'CHU_UI_Jacket_0818.dds', 'playLevel': 14.0, 'musicDifficulty': 'ultima', 'score': 1009809, 'rating': 16.15}, {'musicName': '宵闇の月に抱かれて', 'jacketFile': 'CHU_UI_Jacket_2158.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008818, 'rating': 16.1318}, {'musicName': 'Athlete Killer "Meteor"', 'jacketFile': 'CHU_UI_Jacket_1065.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008811, 'rating': 16.1311}, {'musicName': '二次元ドリームフィーバー', 'jacketFile': 'CHU_UI_Jacket_2037.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008691, 'rating': 16.1191}, {'musicName': '天火明命', 'jacketFile': 'CHU_UI_Jacket_2144.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1008194, 'rating': 16.0694}, {'musicName': 'ENDYMION', 'jacketFile': 'CHU_UI_Jacket_2184.dds', 'playLevel': 14.4, 'musicDifficulty': 'expert', 'score': 1005841, 'rating': 16.0682}, {'musicName': 'Taiko Drum Monster', 'jacketFile': 'CHU_UI_Jacket_0671.dds', 'playLevel': 14.3, 'musicDifficulty': 'master', 'score': 1006288, 'rating': 16.0576}, {'musicName': 'Aleph-0', 'jacketFile': 'CHU_UI_Jacket_0428.dds', 'playLevel': 14.1, 'musicDifficulty': 'expert', 'score': 1007247, 'rating': 16.0494}, {'musicName': '再生不能', 'jacketFile': 'CHU_UI_Jacket_1105.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1007977, 'rating': 16.0477}, {'musicName': 'フューチャー・イヴ', 'jacketFile': 'CHU_UI_Jacket_2344.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008964, 'rating': 16.046400000000002}, {'musicName': 'こちら、幸福安心委員会です。', 'jacketFile': 'CHU_UI_Jacket_1068.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008927, 'rating': 16.0427}, {'musicName': 'Rule the World!!', 'jacketFile': 'CHU_UI_Jacket_2109.dds', 'playLevel': 14.0, 'musicDifficulty': 'master', 'score': 1007899, 'rating': 16.0399}, {'musicName': 'FLUFFY FLASH', 'jacketFile': 'CHU_UI_Jacket_2346.dds', 'playLevel': 14.8, 'musicDifficulty': 'master', 'score': 1002058, 'rating': 16.0058}, {'musicName': '電脳少女は歌姫の夢を見るか？', 'jacketFile': 'CHU_UI_Jacket_2019.dds', 'playLevel': 14.2, 'musicDifficulty': 'master', 'score': 1006509, 'rating': 16.0018}, {'musicName': '迷える音色は恋の唄', 'jacketFile': 'CHU_UI_Jacket_2350.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008486, 'rating': 15.9986}, {'musicName': 'トンデモワンダーズ', 'jacketFile': 'CHU_UI_Jacket_2264.dds', 'playLevel': 13.9, 'musicDifficulty': 'master', 'score': 1008285, 'rating': 15.9785}, {'musicName': 'SON OF SUN', 'jacketFile': 'CHU_UI_Jacket_0887.dds', 'playLevel': 13.8, 'musicDifficulty': 'expert', 'score': 1009937, 'rating': 15.950000000000001}, {'musicName': 'Ascension to Heaven', 'jacketFile': 'CHU_UI_Jacket_0978.dds', 'playLevel': 13.8, 'musicDifficulty': 'expert', 'score': 1009842, 'rating': 15.950000000000001}, {'musicName': 'Fracture Ray', 'jacketFile': 'CHU_UI_Jacket_0749.dds', 'playLevel': 14.7, 'musicDifficulty': 'master', 'score': 1002027, 'rating': 15.9027}]
    
    rating_sum = 0
    for i in range(0, 30):
        single = b30single(ratings[i])
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(52 + (i % 5) * 290)), int(287 + int(i / 5) * 127)), mask)
        pic.paste(single, ((int(53+(i%5)*290)), int(289+int(i/5)*127)))
        rating_sum += math.floor(ratings[i]['rating'] * 100) / 100
    b30 = math.floor(rating_sum / 30 * 100) / 100
    font_style = ImageFont.truetype("fonts/SourceHanSansCN-Bold.otf", 37)
    draw.text((208, 205), str(b30), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")

    ratings = process_r10(userid)
    rating_sum = 0
    for i in range(0, 10):
        single = b30single(ratings[i])
        r, g, b, mask = shadow.split()
        pic.paste(shadow, ((int(1582 + (i % 2) * 290)), int(287 + int(i / 2) * 127)), mask)
        pic.paste(single, ((int(1582+(i%2)*290)), int(289+int(i/2)*127)))
        rating_sum += math.floor(ratings[i]['rating'] * 100) / 100
    r10 = math.floor(rating_sum / 10 * 100) / 100
    draw.text((1726, 205), str(r10), fill=(255,255,255,255), font=font_style, stroke_width=2, stroke_fill="#38809A")
    
    rank = math.floor((b30 * 3 + r10) / 4 * 100) / 100

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
    # pic.show()

def b30single(single_data):
    color = {
        'master': (187, 51, 238),
        'expert': (238, 67, 102),
        'hard': (254, 170, 0),
        'ultima': (0, 0, 0),
        'basic': (102, 221, 17),
    }
    musictitle = single_data['musicName']
    
    pic = Image.new("RGB", (620, 240), (255, 255, 255))
    
    jacket = Image.open(f'chunithm/jackets/{single_data["jacketFile"]}')
    jacket = jacket.resize((186, 186))
    pic.paste(jacket, (32, 28))

    draw = ImageDraw.Draw(pic)
    font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 35)
    size = font.getsize(musictitle)
    if size[0] > 365:
        musictitle = musictitle[:int(len(musictitle)*(345/size[0]))] + '...'
    draw.text((238, 25), musictitle, '#000000', font)

    font = ImageFont.truetype('fonts/FOT-RodinNTLGPro-DB.ttf', 58)
    draw.text((234, 87), str(single_data['score']), '#000000', font)

    font = ImageFont.truetype('fonts/SourceHanSansCN-Bold.otf', 38)
    draw.ellipse((242, 165, 286, 209), fill=color[single_data['musicDifficulty']])
    draw.rectangle((262, 165, 334, 209), fill=color[single_data['musicDifficulty']])
    draw.ellipse((312, 165, 356, 209), fill=color[single_data['musicDifficulty']])
    draw.text((259, 157), str(single_data['playLevel']), (255, 255, 255), font)
    draw.text((370, 157), '→ ' + str(math.floor(single_data['rating'] * 100) / 100), (0, 0, 0), font)

    pic = pic.resize((280, 105))
    return pic


def get_connection():
    return pymysql.connect(
        host=host, 
        port=port, 
        user='pjsk', 
        password=password,
        database='pjsk', 
        charset='utf8mb4'
    )


def getchunibind(qqnum):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * from chunibind where qqnum=%s', (qqnum,))
            data = cursor.fetchone()
            return data[2] if data else None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.close()


def bind_aimeid(qqnum, aimeid):
    userid = str(aime_to_userid(aimeid))
    if userid is None:
        return '卡号不存在'
    user_data = get_user_data(userid)
    print(user_data)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO chunibind (qqnum, aimeid) VALUES (%s, %s) ON DUPLICATE KEY UPDATE aimeid=%s"
            val = (str(qqnum), str(userid), str(userid))
            cursor.execute(sql, val)
            conn.commit()
            return f"绑定成功！记得撤回卡号哦\n游戏昵称：{user_data['userName']}\n等级：{user_data['level']}"
    except Exception as e:
        traceback.print_exc()
        return "绑定失败！"
    finally:
        conn.close()