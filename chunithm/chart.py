import json
import os
import difflib
import re
import traceback
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO


def load_songs(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)


def find_song_id(song_title):
    filename = 'chunithm/sdvxin_chuni.json'
    songs = load_songs(filename)

    # 尝试直接匹配
    if song_title in songs:
        return songs[song_title]

    # 尝试模糊匹配
    close_matches = difflib.get_close_matches(song_title, songs.keys(), n=1, cutoff=0.8)
    if close_matches:
        return songs[close_matches[0]]

    # 正则表达式，用于删除特定的后缀
    pattern = re.compile(r' -.*?-|～.*?～')
    
    # 移除特定的后缀并再次尝试模糊匹配
    cleaned_title = pattern.sub('', song_title).strip()
    close_matches = difflib.get_close_matches(cleaned_title, songs.keys(), n=1, cutoff=0.9)
    if close_matches:
        return songs[close_matches[0]]

    # 尝试匹配标题中的一部分
    parts = re.split(r' -|- |～| ～', song_title)
    for part in parts:
        if part in songs:
            return songs[part]

    return None # 没有找到匹配项


def official_id_to_sdvx_id(official_id):
    # 从music.json文件加载歌曲
    json_filename = "chunithm/music.json"
    with open(json_filename, 'r', encoding='utf-8') as file:
        json_songs = json.load(file)

    song_title = None
    # 从music.json中使用ID找到对应的曲目标题
    for song in json_songs:
        if str(song["id"]) == str(official_id):
            song_title = song["title"]
            break

    if song_title is None:
        return None

    # 使用之前定义的查找方法找到对应的sdvxin_chuni.json中的ID
    return find_song_id(song_title)


# setup proxy
PROXY = {'http': 'http://localhost:7890', 'https': 'http://localhost:7890'}


def download_and_merge_images(musicid, sdvxid, difficulty):
    # 构建URL
    prefix = sdvxid[:2]
    
    base_url = f"https://sdvx.in/chunithm/{prefix}/bg/{sdvxid}bg.png"
    if difficulty == 'master':
        obj_url = f"https://sdvx.in/chunithm/{prefix}/obj/data{sdvxid}mst.png"
    else:
        obj_url = f"https://sdvx.in/chunithm/{prefix}/obj/data{sdvxid}{difficulty[:3]}.png"
    bar_url = f"https://sdvx.in/chunithm/{prefix}/bg/{sdvxid}bar.png"

    # 下载图像
    base_image = Image.open(BytesIO(requests.get(base_url, proxies=PROXY).content))
    obj_image = Image.open(BytesIO(requests.get(obj_url, proxies=PROXY).content))
    bar_image = Image.open(BytesIO(requests.get(bar_url, proxies=PROXY).content))

    # 创建纯黑背景
    black_image = Image.new("RGBA", base_image.size, (0, 0, 0, 255))

    # 合并图像
    merged_image = Image.alpha_composite(black_image, base_image)
    merged_image = Image.alpha_composite(merged_image, obj_image)
    merged_image = Image.alpha_composite(merged_image, bar_image)

    # 保存图像
    directory = os.path.join("charts", "chunithm", str(musicid))
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{difficulty}.jpg")
    # 保存图像为JPEG格式，并选择一个质量设置
    merged_image = merged_image.convert('RGB') # 将图像转换为RGB，因为JPEG不支持透明度
    merged_image.save(output_path, 'JPEG', quality=60) # 你可以调整质量参数来达到所需的文件大小
    
    print(f"图像已保存到 {output_path}")
    return output_path


def get_chunithm_chart(musicid, difficulty):
    print(musicid, difficulty)
    local_path = os.path.join("charts", "chunithm", str(musicid), f"{difficulty}.jpg")
    
    if os.path.exists(local_path):
        return get_song_info(musicid) + (local_path,)

    try:
        sdvxid = official_id_to_sdvx_id(musicid)
        if sdvxid is not None:
            download_and_merge_images(musicid, sdvxid, difficulty)
            return get_song_info(musicid) + (local_path,)
    except Exception as e:
        traceback.print_exc()

    return None

def get_song_info(musicid):
    with open("chunithm/music.json", 'r', encoding='utf-8') as file:
        songs = json.load(file)
        for song in songs:
            if song["id"] == str(musicid):
                return (song["title"],)
    return ("未知歌曲",)


if __name__ == '__main__':
    pass

