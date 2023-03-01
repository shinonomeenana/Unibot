import csv
import sys
import ujson as json


# 定数填写系统，将难度定数做成csv格式方便填写，填写后转回json给bot用


def get_raw_diff_list(music_id: int, raw_music_difficulties=None):
    if raw_music_difficulties is None:
        with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
            raw_music_difficulties = json.load(f)
    for i in range(len(raw_music_difficulties)):
        if raw_music_difficulties[i]['musicId'] == music_id:
            return [raw_music_difficulties[j]['playLevel'] for j in range(i, i + 5)]
    return None


def get_custom_diff_list(music_id: int, custom_music_difficulties=None):
    if custom_music_difficulties is None:
        with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
            custom_music_difficulties = json.load(f)
    for i in range(len(custom_music_difficulties)):
        if custom_music_difficulties[i]['musicId'] == music_id:
            try:
                return [[custom_music_difficulties[j]['fullComboAdjust'] + custom_music_difficulties[j]['playLevel'] for j in range(i + 3, i + 5)],
                        [custom_music_difficulties[j]['fullPerfectAdjust'] + custom_music_difficulties[j]['playLevel'] for j in range(i + 3, i + 5)]]
            except KeyError:
                return None
    return None


def generate_diff_csv():
    csvdata = []
    with open('masterdata/musics.json', 'r', encoding='utf-8') as f:
        musics = json.load(f)
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        raw_diff_data = json.load(f)
    with open('masterdata/realtime/musicDifficulties.json', 'r', encoding='utf-8') as f:
        custom_diff_data = json.load(f)
    for music in musics:
        raw_diff = get_raw_diff_list(music['id'], raw_diff_data)
        custom_diff = get_custom_diff_list(music['id'], custom_diff_data)
        if custom_diff is not None:
            csvdata.append([music['title'], music['id'], music['publishedAt'], raw_diff[3], custom_diff[0][0], custom_diff[1][0],
                                                        raw_diff[4], custom_diff[0][1], custom_diff[1][1]])
        else:
            csvdata.append([music['title'], music['id'], music['publishedAt'], raw_diff[3], '', '',
                                                        raw_diff[4], '', ''])
    with open("masterdata/realtime/musics.csv", "w", newline='', encoding='utf-8-sig') as csvfile: 
        writer = csv.writer(csvfile)
        writer.writerow(["曲名", "id", "time", 'EXPERT', "FC定数", "AP定数", 'MASTER', "FC定数", "AP定数"])
        writer.writerows(csvdata)


def generate_diff_json():
    with open('masterdata/musicDifficulties.json', 'r', encoding='utf-8') as f:
        diff_data = json.load(f)

    with open("masterdata/realtime/musics.csv", "r", encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            try:
                music_id = int(line[1])
                
                for i in range(len(diff_data)):
                    if diff_data[i]['musicId'] == music_id:
                        break
                if line[4] != '':
                    diff_data[i + 3]['fullComboAdjust'] = round(float(line[4]) - int(line[3]), 3)
                    diff_data[i + 3]['fullPerfectAdjust'] = round(float(line[5]) - int(line[3]), 3)
                    diff_data[i + 3]['playLevelAdjust'] = round((
                        diff_data[i + 3]['fullComboAdjust'] * 2/3 + diff_data[i + 3]['fullPerfectAdjust'] * 1/3
                    ), 3)
                else:
                    diff_data[i + 3]['fullComboAdjust'] = '?'
                    diff_data[i + 3]['fullPerfectAdjust'] = '?'
                    diff_data[i + 3]['playLevelAdjust'] = '?'
                
                diff_data[i + 4]['fullComboAdjust'] = round(float(line[7]) - int(line[6]), 3)
                diff_data[i + 4]['fullPerfectAdjust'] = round(float(line[8]) - int(line[6]), 3)
                diff_data[i + 4]['playLevelAdjust'] = round((
                    diff_data[i + 4]['fullComboAdjust'] * 2/3 + diff_data[i + 4]['fullPerfectAdjust'] * 1/3
                ), 3)
            except ValueError:
                pass

    with open('masterdata/realtime/musicDifficulties.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(diff_data, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1] == 'gencsv':
        generate_diff_csv()
    elif sys.argv[1] == 'genjson':
        generate_diff_json()