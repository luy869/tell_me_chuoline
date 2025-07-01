import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 設定
# -----------------------------------------------------------------------------
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# リアルタイム列車情報API
REALTIME_API_URL = "https://api.odpt.org/api/v4/odpt:Train"

# -----------------------------------------------------------------------------
# 手動で作成した時刻表データ (八王子駅・平日・上り方面)
# 実際の時刻表を元に、始発から終電までを記述
# 重要: "train_number" がリアルタイム情報と結びつけるキーになります
# -----------------------------------------------------------------------------
HACHIOJI_TIMETABLE_UP_WEEKDAY = [
    # 4時台
    {"time": "04:33", "type": "快速", "destination": "東京", "train_number": "433T"},
    # 5時台
    {"time": "05:04", "type": "快速", "destination": "東京", "train_number": "504T"},
    {"time": "05:14", "type": "快速", "destination": "東京", "train_number": "514T"},
    {"time": "05:30", "type": "快速", "destination": "東京", "train_number": "530T"},
    {"time": "05:45", "type": "快速", "destination": "東京", "train_number": "545T"},
    {"time": "05:54", "type": "快速", "destination": "東京", "train_number": "554T"},
    # 6時台
    {"time": "06:04", "type": "中央特快", "destination": "東京", "train_number": "604C"},
    {"time": "06:13", "type": "快速", "destination": "東京", "train_number": "613T"},
    {"time": "06:18", "type": "中央特快", "destination": "東京", "train_number": "618C"},
    {"time": "06:30", "type": "快速", "destination": "東京", "train_number": "630T"},
    {"time": "06:34", "type": "快速", "destination": "東京", "train_number": "634T"},
    {"time": "06:40", "type": "快速", "destination": "東京", "train_number": "640T"},
    {"time": "06:44", "type": "快速", "destination": "東京", "train_number": "644T"},
    {"time": "06:49", "type": "かいじ", "destination": "東京", "train_number": "649K"},
    {"time": "06:53", "type": "快速", "destination": "東京", "train_number": "653T"},
    {"time": "06:58", "type": "快速", "destination": "東京", "train_number": "658T"},
    # 7時台
    {"time": "07:02", "type": "快速", "destination": "東京", "train_number": "702T"},
    {"time": "07:06", "type": "快速", "destination": "東京", "train_number": "706T"},
    {"time": "07:10", "type": "通勤特別快速", "destination": "東京", "train_number": "710S"},
    {"time": "07:13", "type": "快速", "destination": "東京", "train_number": "713T"},
    {"time": "07:17", "type": "快速", "destination": "東京", "train_number": "717T"},
    {"time": "07:21", "type": "快速", "destination": "東京", "train_number": "721T"},
    {"time": "07:25", "type": "快速", "destination": "東京", "train_number": "725T"},
    {"time": "07:32", "type": "快速", "destination": "東京", "train_number": "732T"},
    {"time": "07:35", "type": "快速", "destination": "東京", "train_number": "735T"},
    {"time": "07:38", "type": "快速", "destination": "東京", "train_number": "738T"},
    {"time": "07:40", "type": "快速", "destination": "東京", "train_number": "740T"},
    {"time": "07:46", "type": "快速", "destination": "東京", "train_number": "746T"},
    {"time": "07:53", "type": "快速", "destination": "東京", "train_number": "753T"},
    {"time": "07:56", "type": "快速", "destination": "東京", "train_number": "756T"},
    {"time": "07:59", "type": "快速", "destination": "東京", "train_number": "759T"},
    # 8時台
    {"time": "08:03", "type": "かいじ", "destination": "東京", "train_number": "803K"},
    {"time": "08:07", "type": "快速", "destination": "東京", "train_number": "807T"},
    {"time": "08:10", "type": "快速", "destination": "東京", "train_number": "810T"},
    {"time": "08:13", "type": "快速", "destination": "東京", "train_number": "813T"},
    {"time": "08:18", "type": "快速", "destination": "東京", "train_number": "818T"},
    {"time": "08:21", "type": "快速", "destination": "東京", "train_number": "821T"},
    {"time": "08:25", "type": "普通", "destination": "立川", "train_number": "825L"},
    {"time": "08:29", "type": "快速", "destination": "東京", "train_number": "829T"},
    {"time": "08:34", "type": "あずさ", "destination": "東京", "train_number": "834A"},
    {"time": "08:39", "type": "快速", "destination": "東京", "train_number": "839T"},
    {"time": "08:43", "type": "通勤特別快速", "destination": "東京", "train_number": "843S"},
    {"time": "08:47", "type": "快速", "destination": "東京", "train_number": "847T"},
    {"time": "08:49", "type": "快速", "destination": "東京", "train_number": "849T"},
    {"time": "08:53", "type": "かいじ", "destination": "東京", "train_number": "853K"},
    {"time": "08:58", "type": "快速", "destination": "東京", "train_number": "858T"},
    # 9時台
    {"time": "09:05", "type": "快速", "destination": "東京", "train_number": "905T"},
    {"time": "09:11", "type": "快速", "destination": "東京", "train_number": "911T"},
    {"time": "09:14", "type": "あずさ", "destination": "東京", "train_number": "914A"},
    {"time": "09:19", "type": "中央特快", "destination": "東京", "train_number": "919C"},
    {"time": "09:26", "type": "快速", "destination": "東京", "train_number": "926T"},
    {"time": "09:35", "type": "快速", "destination": "東京", "train_number": "935T"},
    {"time": "09:39", "type": "中央特快", "destination": "東京", "train_number": "939C"},
    {"time": "09:45", "type": "快速", "destination": "東京", "train_number": "945T"},
    {"time": "09:49", "type": "かいじ", "destination": "東京", "train_number": "949K"},
    {"time": "09:58", "type": "快速", "destination": "東京", "train_number": "958T"},
    # 10時台
    {"time": "10:04", "type": "快速", "destination": "東京", "train_number": "1004T"},
    {"time": "10:12", "type": "中央特快", "destination": "東京", "train_number": "1012C"},
    {"time": "10:21", "type": "あずさ", "destination": "東京", "train_number": "1021A"},
    {"time": "10:24", "type": "快速", "destination": "東京", "train_number": "1024T"},
    {"time": "10:32", "type": "中央特快", "destination": "東京", "train_number": "1032C"},
    {"time": "10:40", "type": "中央特快", "destination": "東京", "train_number": "1040C"},
    {"time": "10:46", "type": "快速", "destination": "東京", "train_number": "1046T"},
    {"time": "10:51", "type": "かいじ", "destination": "東京", "train_number": "1051K"},
    {"time": "10:54", "type": "快速", "destination": "東京", "train_number": "1054T"},
    # 11時台
    {"time": "11:05", "type": "快速", "destination": "東京", "train_number": "1105T"},
    {"time": "11:11", "type": "快速", "destination": "東京", "train_number": "1111T"},
    {"time": "11:21", "type": "あずさ", "destination": "東京", "train_number": "1121A"},
    {"time": "11:25", "type": "中央特快", "destination": "東京", "train_number": "1125C"},
    {"time": "11:34", "type": "中央特快", "destination": "東京", "train_number": "1134C"},
    {"time": "11:41", "type": "快速", "destination": "東京", "train_number": "1141T"},
    {"time": "11:49", "type": "中央特快", "destination": "東京", "train_number": "1149C"},
    # 12時台
    {"time": "12:00", "type": "中央特快", "destination": "東京", "train_number": "1200C"},
    {"time": "12:06", "type": "快速", "destination": "東京", "train_number": "1206T"},
    {"time": "12:12", "type": "あずさ", "destination": "新宿", "train_number": "1212A"},
    {"time": "12:21", "type": "中央特快", "destination": "東京", "train_number": "1221C"},
    {"time": "12:31", "type": "快速", "destination": "東京", "train_number": "1231T"},
    {"time": "12:35", "type": "かいじ", "destination": "新宿", "train_number": "1235K"},
    {"time": "12:39", "type": "中央特快", "destination": "東京", "train_number": "1239C"},
    {"time": "12:49", "type": "中央特快", "destination": "東京", "train_number": "1249C"},
    {"time": "12:53", "type": "快速", "destination": "東京", "train_number": "1253T"},
    # 13時台
    {"time": "13:01", "type": "中央特快", "destination": "東京", "train_number": "1301C"},
    {"time": "13:06", "type": "快速", "destination": "東京", "train_number": "1306T"},
    {"time": "13:11", "type": "あずさ", "destination": "新宿", "train_number": "1311A"},
    {"time": "13:15", "type": "快速", "destination": "東京", "train_number": "1315T"},
    {"time": "13:27", "type": "中央特快", "destination": "東京", "train_number": "1327C"},
    {"time": "13:37", "type": "かいじ", "destination": "新宿", "train_number": "1337K"},
    {"time": "13:41", "type": "中央特快", "destination": "東京", "train_number": "1341C"},
    {"time": "13:51", "type": "中央特快", "destination": "東京", "train_number": "1351C"},
    {"time": "13:58", "type": "中央特快", "destination": "東京", "train_number": "1358C"},
    # 14時台
    {"time": "14:05", "type": "快速", "destination": "東京", "train_number": "1405T"},
    {"time": "14:11", "type": "あずさ", "destination": "新宿", "train_number": "1411A"},
    {"time": "14:14", "type": "快速", "destination": "東京", "train_number": "1414T"},
    {"time": "14:24", "type": "中央特快", "destination": "東京", "train_number": "1424C"},
    {"time": "14:30", "type": "快速", "destination": "東京", "train_number": "1430T"},
    {"time": "14:33", "type": "かいじ", "destination": "新宿", "train_number": "1433K"},
    {"time": "14:37", "type": "中央特快", "destination": "東京", "train_number": "1437C"},
    {"time": "14:49", "type": "中央特快", "destination": "東京", "train_number": "1449C"},
    {"time": "14:59", "type": "中央特快", "destination": "東京", "train_number": "1459C"},
    # 15時台
    {"time": "15:05", "type": "快速", "destination": "東京", "train_number": "1505T"},
    {"time": "15:10", "type": "あずさ", "destination": "新宿", "train_number": "1510A"},
    {"time": "15:14", "type": "快速", "destination": "東京", "train_number": "1514T"},
    {"time": "15:20", "type": "中央特快", "destination": "東京", "train_number": "1520C"},
    {"time": "15:28", "type": "快速", "destination": "東京", "train_number": "1528T"},
    {"time": "15:34", "type": "かいじ", "destination": "新宿", "train_number": "1534K"},
    {"time": "15:34", "type": "富士回遊", "destination": "新宿", "train_number": "1534F"},
    {"time": "15:38", "type": "中央特快", "destination": "東京", "train_number": "1538C"},
    {"time": "15:44", "type": "快速", "destination": "東京", "train_number": "1544T"},
    {"time": "15:49", "type": "あずさ", "destination": "新宿", "train_number": "1549A"},
    {"time": "15:54", "type": "中央特快", "destination": "東京", "train_number": "1554C"},
    # 16時台
    {"time": "16:01", "type": "快速", "destination": "東京", "train_number": "1601T"},
    {"time": "16:08", "type": "中央特快", "destination": "東京", "train_number": "1608C"},
    {"time": "16:13", "type": "快速", "destination": "東京", "train_number": "1613T"},
    {"time": "16:17", "type": "快速", "destination": "東京", "train_number": "1617T"},
    {"time": "16:21", "type": "快速", "destination": "東京", "train_number": "1621T"},
    {"time": "16:24", "type": "かいじ", "destination": "新宿", "train_number": "1624K"},
    {"time": "16:24", "type": "富士回遊", "destination": "新宿", "train_number": "1624F"},
    {"time": "16:29", "type": "快速", "destination": "東京", "train_number": "1629T"},
    {"time": "16:38", "type": "中央特快", "destination": "東京", "train_number": "1638C"},
    {"time": "16:44", "type": "快速", "destination": "東京", "train_number": "1644T"},
    {"time": "16:50", "type": "あずさ", "destination": "新宿", "train_number": "1650A"},
    {"time": "16:53", "type": "快速", "destination": "東京", "train_number": "1653T"},
    {"time": "16:55", "type": "むさしの号", "destination": "大宮", "train_number": "1655M"},
    # 17時台
    {"time": "17:00", "type": "快速", "destination": "東京", "train_number": "1700T"},
    {"time": "17:03", "type": "快速", "destination": "東京", "train_number": "1703T"},
    {"time": "17:09", "type": "中央特快", "destination": "東京", "train_number": "1709C"},
    {"time": "17:15", "type": "快速", "destination": "東京", "train_number": "1715T"},
    {"time": "17:18", "type": "かいじ", "destination": "新宿", "train_number": "1718K"},
    {"time": "17:23", "type": "快速", "destination": "東京", "train_number": "1723T"},
    {"time": "17:30", "type": "あずさ", "destination": "新宿", "train_number": "1730A"},
    {"time": "17:32", "type": "快速", "destination": "東京", "train_number": "1732T"},
    {"time": "17:36", "type": "中央特快", "destination": "東京", "train_number": "1736C"},
    {"time": "17:43", "type": "快速", "destination": "東京", "train_number": "1743T"},
    {"time": "17:47", "type": "快速", "destination": "東京", "train_number": "1747T"},
    {"time": "17:57", "type": "中央特快", "destination": "東京", "train_number": "1757C"},
    {"time": "17:59", "type": "快速", "destination": "東京", "train_number": "1759T"},
    # 18時台
    {"time": "18:04", "type": "快速", "destination": "東京", "train_number": "1804T"},
    {"time": "18:11", "type": "あずさ", "destination": "新宿", "train_number": "1811A"},
    {"time": "18:11", "type": "富士回遊", "destination": "新宿", "train_number": "1811F"},
    {"time": "18:15", "type": "中央特快", "destination": "東京", "train_number": "1815C"},
    {"time": "18:19", "type": "快速", "destination": "東京", "train_number": "1819T"},
    {"time": "18:24", "type": "快速", "destination": "東京", "train_number": "1824T"},
    {"time": "18:28", "type": "快速", "destination": "東京", "train_number": "1828T"},
    {"time": "18:31", "type": "あずさ", "destination": "新宿", "train_number": "1831A"},
    {"time": "18:33", "type": "快速", "destination": "東京", "train_number": "1833T"},
    {"time": "18:38", "type": "快速", "destination": "東京", "train_number": "1838T"},
    {"time": "18:42", "type": "普通", "destination": "立川", "train_number": "1842L"},
    {"time": "18:44", "type": "快速", "destination": "東京", "train_number": "1844T"},
    {"time": "18:48", "type": "むさしの号", "destination": "大宮", "train_number": "1848M"},
    {"time": "18:51", "type": "快速", "destination": "東京", "train_number": "1851T"},
    {"time": "18:57", "type": "快速", "destination": "東京", "train_number": "1857T"},
    # 19時台
    {"time": "19:06", "type": "快速", "destination": "東京", "train_number": "1906T"},
    {"time": "19:10", "type": "かいじ", "destination": "新宿", "train_number": "1910K"},
    {"time": "19:10", "type": "富士回遊", "destination": "新宿", "train_number": "1910F"},
    {"time": "19:14", "type": "快速", "destination": "東京", "train_number": "1914T"},
    {"time": "19:19", "type": "中央特快", "destination": "東京", "train_number": "1919C"},
    {"time": "19:30", "type": "快速", "destination": "東京", "train_number": "1930T"},
    {"time": "19:33", "type": "あずさ", "destination": "千葉", "train_number": "1933A"},
    {"time": "19:39", "type": "快速", "destination": "東京", "train_number": "1939T"},
    {"time": "19:46", "type": "中央特快", "destination": "東京", "train_number": "1946C"},
    {"time": "19:49", "type": "快速", "destination": "東京", "train_number": "1949T"},
    {"time": "19:58", "type": "快速", "destination": "東京", "train_number": "1958T"},
    # 20時台
    {"time": "20:04", "type": "かいじ", "destination": "新宿", "train_number": "2004K"},
    {"time": "20:07", "type": "快速", "destination": "東京", "train_number": "2007T"},
    {"time": "20:16", "type": "中央特快", "destination": "東京", "train_number": "2016C"},
    {"time": "20:26", "type": "快速", "destination": "東京", "train_number": "2026T"},
    {"time": "20:34", "type": "快速", "destination": "東京", "train_number": "2034T"},
    {"time": "20:38", "type": "快速", "destination": "東京", "train_number": "2038T"},
    {"time": "20:42", "type": "あずさ", "destination": "新宿", "train_number": "2042A"},
    {"time": "20:49", "type": "中央特快", "destination": "東京", "train_number": "2049C"},
    {"time": "20:58", "type": "快速", "destination": "東京", "train_number": "2058T"},
    # 21時台
    {"time": "21:02", "type": "快速", "destination": "東京", "train_number": "2102T"},
    {"time": "21:06", "type": "かいじ", "destination": "新宿", "train_number": "2106K"},
    {"time": "21:10", "type": "快速", "destination": "東京", "train_number": "2110T"},
    {"time": "21:19", "type": "中央特快", "destination": "東京", "train_number": "2119C"},
    {"time": "21:23", "type": "快速", "destination": "東京", "train_number": "2123T"},
    {"time": "21:28", "type": "快速", "destination": "東京", "train_number": "2128T"},
    {"time": "21:32", "type": "快速", "destination": "東京", "train_number": "2132T"},
    {"time": "21:36", "type": "かいじ", "destination": "新宿", "train_number": "2136K"},
    {"time": "21:41", "type": "快速", "destination": "東京", "train_number": "2141T"},
    {"time": "21:48", "type": "快速", "destination": "東京", "train_number": "2148T"},
    {"time": "21:53", "type": "快速", "destination": "東京", "train_number": "2153T"},
    {"time": "21:56", "type": "中央特快", "destination": "東京", "train_number": "2156C"},
    # 22時台
    {"time": "22:03", "type": "快速", "destination": "東京", "train_number": "2203T"},
    {"time": "22:10", "type": "快速", "destination": "東京", "train_number": "2210T"},
    {"time": "22:13", "type": "あずさ", "destination": "新宿", "train_number": "2213A"},
    {"time": "22:19", "type": "中央特快", "destination": "東京", "train_number": "2219C"},
    {"time": "22:22", "type": "快速", "destination": "東京", "train_number": "2222T"},
    {"time": "22:30", "type": "中央特快", "destination": "東京", "train_number": "2230C"},
    {"time": "22:37", "type": "快速", "destination": "東京", "train_number": "2237T"},
    {"time": "22:41", "type": "快速", "destination": "東京", "train_number": "2241T"},
    {"time": "22:48", "type": "快速", "destination": "東京", "train_number": "2248T"},
    {"time": "22:58", "type": "快速", "destination": "東京", "train_number": "2258T"},
    # 23時台
    {"time": "23:10", "type": "快速", "destination": "東京", "train_number": "2310T"},
    {"time": "23:26", "type": "快速", "destination": "東京", "train_number": "2326T"},
    {"time": "23:40", "type": "快速", "destination": "三鷹", "train_number": "2340T"},
    {"time": "23:58", "type": "快速", "destination": "三鷹", "train_number": "2358T"},
    # 0時台
    {"time": "00:19", "type": "快速", "destination": "武蔵小金井", "train_number": "0019T"},
]

# -----------------------------------------------------------------------------
# リアルタイムの遅延情報を取得する関数
# -----------------------------------------------------------------------------
def get_realtime_delays():
    """
    JR中央線(快速)のリアルタイム列車情報をAPIから取得し、
    {列車番号: 遅延秒数} の辞書形式で返す
    """
    params = {
        "odpt:railway": "odpt.Railway:JR-East.ChuoRapid",
        "acl:consumerKey": ACCESS_TOKEN
    }
    
    delays = {}
    try:
        response = requests.get(REALTIME_API_URL, params=params)
        # 200 OK 以外の場合はエラーとして処理
        response.raise_for_status()
        train_data = response.json()
        
        if train_data:
            for train in train_data:
                train_number = train.get("odpt:trainNumber")
                delay_seconds = train.get("odpt:delay", 0)
                if train_number:
                    delays[train_number] = delay_seconds
            print("リアルタイムの遅延情報を取得しました。")
        else:
            print("現在、走行中の列車情報はありません。")

    except requests.exceptions.HTTPError as http_err:
        # 4xx, 5xx エラーの場合
        print(f"HTTPエラー: {http_err}")
    except requests.exceptions.RequestException as req_err:
        # タイムアウトや接続エラーなど
        print(f"リクエストエラー: {req_err}")
    except Exception as e:
        # その他の予期せぬエラー
        print(f"予期せぬエラー: {e}")
        
    return delays

# ----------------------------------------------------------------------------
# 次の電車を見つける関数
# ----------------------------------------------------------------------------
def find_next_trains(now, timetable, delays):
    """
    現在時刻、時刻表、遅延情報を元に、次に来る電車3本を返す
    """
    next_trains = []
    
    for entry in timetable:
        # 時刻表の時刻をdatetimeオブジェクトに変換
        # 日付は実行日に合わせる
        scheduled_time_str = f"{now.year}-{now.month}-{now.day} {entry['time']}"
        scheduled_time = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M")

        # 0時台の電車で、現在時刻が23時台などの場合は日付を1日進める
        if scheduled_time.hour < 4 and now.hour > 20:
            scheduled_time += timedelta(days=1)

        # 遅延情報を取得
        train_number = entry.get("train_number")
        delay_seconds = delays.get(train_number, 0)
        actual_time = scheduled_time + timedelta(seconds=delay_seconds)

        # 現在時刻より後に出発する電車をリストに追加
        if actual_time > now:
            entry['scheduled_time'] = scheduled_time.strftime('%H:%M')
            entry['actual_time'] = actual_time.strftime('%H:%M')
            entry['delay_minutes'] = delay_seconds // 60
            next_trains.append(entry)

    # 到着時刻順にソートして、最初の3件を返す
    return sorted(next_trains, key=lambda x: x['actual_time'])[:3]

# ----------------------------------------------------------------------------
# メイン処理
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # 現在時刻を取得
    current_time = datetime.now()
    # current_time = datetime.strptime("2023-10-27 08:00", "%Y-%m-%d %H:%M") # テスト用

    print(f"現在時刻: {current_time.strftime('%H:%M:%S')}")
    print("八王子駅 (上り) の次の電車を検索します...")
    print("-" * 40)

    # リアルタイムの遅延情報を取得
    realtime_delays = get_realtime_delays()

    # 次の電車を検索
    next_trains_to_display = find_next_trains(current_time, HACHIOJI_TIMETABLE_UP_WEEKDAY, realtime_delays)

    # 結果を表示
    if next_trains_to_display:
        for i, train in enumerate(next_trains_to_display):
            delay_info = f"({train['delay_minutes']}分遅れ)" if train['delay_minutes'] > 0 else "(定刻)"
            print(
                f"{i+1}. {train['scheduled_time']}発 -> {train['actual_time']}頃 "
                f"【{train['type']}】{train['destination']}行き "
                f"{delay_info}"
            )
    else:
        print("現在時刻以降に利用可能な電車はありません。")
