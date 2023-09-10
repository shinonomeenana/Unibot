import json
from datetime import datetime, timezone, timedelta

def wds_to_unix_timestamp(wds_timestamp):
    return wds_timestamp + 32400

def sort_music_by_time(music_data):
    return sorted(music_data, key=lambda x: x['releasedAt'], reverse=True)

if __name__ == "__main__":
    with open('wds/masterdata/music.json', 'r', encoding='utf-8') as f:
        music_data = json.load(f)

    sorted_music = sort_music_by_time(music_data)

    for music in sorted_music:
        name = music.get('name', '未知')
        musicid = music.get('id', 0)
        released_at_unix = wds_to_unix_timestamp(music.get('releasedAt', 0))
        released_at_utc8 = datetime.fromtimestamp(released_at_unix, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{musicid}:{name}  发布时间: {released_at_utc8}")