import json
import re

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
        match_rate = len(re.findall(query.lower(), title.lower()))

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


def song_details(song_id):
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
    difficulties_str = f"{difficulties['basic']}/{difficulties['advanced']}/{difficulties['expert']}/{difficulties['master']}"
    
    if 'ultima' in difficulties and difficulties['ultima'] > 0:
        difficulties_str += f"/{difficulties['ultima']}"
        
    if song_music['we_kanji'] and song_music['we_star']:
        title += f"【{song_music['we_kanji']}】"
        difficulties_str = f"WORLD'S END {'★'*int(int(song_music['we_star'])/2)}"

    # 格式化输出信息
    info = f"{song_music['id']}: {title}\n"\
           f"类型：{song_music['catname']}\n"\
           f"艺术家：{song_music['artist']}\n"\
           f"难度：{difficulties_str}\n"

    # 图片地址
    image_url = f"/chunithm/jackets/{song_musics['jaketFile']}"

    return info, image_url



