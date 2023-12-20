import json
import re
from chunithm.alias import chu_aliastomusicid
import Levenshtein as lev
from chunithm.b30 import sunp_to_lmn

def get_match_rate(query, title):
    # 将查询和标题转换为小写
    query = query.lower()
    title = title.lower()

    # 计算 Levenshtein 距离
    distance = lev.distance(query, title)

    # 计算最大长度以标准化距离
    max_len = max(len(query), len(title))
    if max_len == 0:
        return 1.0  # 避免除以零

    # 计算相似度（1 - (距离/最大长度)）
    similarity = 1 - (distance / max_len)

    return similarity


def search_song(query):
    # 读取数据
    with open('chunithm/music.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []

    for song in data:
        # 根据需求格式化标题
        title = song['title']
        if song['we_kanji'] and song['we_star']:
            title += f"【{song['we_kanji']}】"

        # 计算匹配度
        match_rate = get_match_rate(query, title)

        if match_rate > 0:
            results.append((song['id'], title, match_rate))

    # 根据匹配度排序
    results.sort(key=lambda x: x[2], reverse=True)

    # 取前10个结果
    results = results[:10]

    if len(results) == 0:
        return "没有找到捏"
    else:
        return "\n".join([f"{result[0]}: {result[1]}" for result in results])


def song_details(alias):
    resp = chu_aliastomusicid(alias)
    song_id = str(resp['musicid'])
    reverse_difficulty_mapping = {
        "basic": 0,
        "advanced": 1,
        "expert": 2,
        "master": 3,
        "ultima": 4,
    }
    # 读取数据
    with open('chunithm/music.json', 'r', encoding='utf-8') as f:
        data_music = json.load(f)
        
    with open('chunithm/masterdata/musics.json', 'r', encoding='utf-8') as f:
        data_musics = json.load(f)
        
    # 根据id找到歌曲
    song_music = next((song for song in data_music if song["id"] == song_id), None)
    song_musics = next((song for song in data_musics if song["id"] == song_id), None)

    if not song_music or not song_musics:
        return "没有找到该歌曲", None

    # 格式化标题和难度
    title = song_music['title']
    difficulties = song_musics['difficulties']
    original_difficulties = difficulties.copy()  # 复制原始难度
    modified = False  # 标记是否有修改

    for single in difficulties:
        try:
            new_value = sunp_to_lmn.get((int(song_id), reverse_difficulty_mapping[single]))
            if new_value is not None:
                difficulties[single] = new_value
                modified = True
        except KeyError:
            pass

    # 构建原始难度字符串
    original_difficulties_str = f"{original_difficulties['basic']}/{original_difficulties['advanced']}/{original_difficulties['expert']}/{original_difficulties['master']}"
    if 'ultima' in original_difficulties and original_difficulties['ultima'] > 0:
        original_difficulties_str += f"/{original_difficulties['ultima']}"

    # 构建修改后的难度字符串
    difficulties_str = f"{difficulties['basic']}/{difficulties['advanced']}/{difficulties['expert']}/{difficulties['master']}"
    if 'ultima' in difficulties and difficulties['ultima'] > 0:
        difficulties_str += f"/{difficulties['ultima']}"

    # 根据是否有修改，构建最终输出字符串
    if modified:
        final_str = f"{original_difficulties_str} (SUN PLUS)\n{difficulties_str} (Luminous)"
    else:
        final_str = original_difficulties_str


    if song_music['we_kanji'] and song_music['we_star']:
        title += f"【{song_music['we_kanji']}】"
        final_str = f"WORLD'S END {'★'*int(int(song_music['we_star'])/2)}"

    # 格式化输出信息
    info = f"{song_music['id']}: {title}\n"\
           f"匹配度: {resp['match']}\n"\
           f"类型：{song_music['catname']}\n"\
           f"艺术家：{song_music['artist']}\n"\
           f"难度：{final_str}\n"

    # 图片地址
    image_url = f"/chunithm/jackets/{song_musics['jaketFile']}"

    return info, image_url



