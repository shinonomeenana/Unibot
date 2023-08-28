from datetime import datetime, timedelta, timezone
import time
import requests
import ujson as json
from modules.sk import timeremain

from wds.musicinfo import wds_to_unix_timestamp
from wds.config import apiroot

def wds_current_event():
    file_path = 'wds/masterdata/storyEvent.json'
    current_unix_time = time.time()

    with open(file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    for i, event in enumerate(events):
        start_unix_time = wds_to_unix_timestamp(event['startDate'])
        end_unix_time = wds_to_unix_timestamp(event['endDate'])
        
        if start_unix_time <= current_unix_time <= end_unix_time:
            return event['id'], event['title'], "going", wds_to_unix_timestamp(event['endDate'])
        
        elif current_unix_time < start_unix_time:
            # 如果当前时间小于下一个活动的开始时间，则表示前一个活动已结束
            if i > 0:
                return events[i - 1]['id'], events[i - 1]['title'], "end", wds_to_unix_timestamp(event[i - 1]['endDate'])
            else:
                # 如果是第一个活动还未开始
                return event['id'], event['title'], "pending", wds_to_unix_timestamp(event['endDate'])
        
    # 所有活动已结束
    return events[-1]['id'], events[-1]['title'], "end", wds_to_unix_timestamp(event[-1]['endDate'])


def wds_score_line():
    event_id, title, status, end_date = wds_current_event()
    # 请求API获取数据
    url = apiroot + f'/api/Events/GetStoryEventBorderRanking/{event_id}?mStoryEventId={event_id}'
    response = requests.get(url)
    data = response.json()

    text = f'当前活动为：{title}\n当前时间：' + \
            datetime.fromtimestamp(time.time(), timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S (UTC+8)') + \
            '\n结活时间：' + datetime.fromtimestamp(end_date, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S (UTC+8)')
    if status == 'going':
        text += '\n活动还剩' + timeremain(end_date - time.time())
    else:
        text += '\n活动已结束'
    # 提取排名数据
    raw_ranking = data['result']['rawRanking']
    for record in raw_ranking:
        rank = record['rank']
        point = record['point']
        text += f"\n{rank}名：{point/10000}W"
    return text