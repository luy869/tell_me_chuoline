import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# 設定
# -----------------------------------------------------------------------------
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# リアルタイム列車情報API (2025年更新版)
REALTIME_API_URL = "https://api.odpt.org/api/v4/odpt:Train"

# -----------------------------------------------------------------------------
# 手動で作成した時刻表データ (八王子駅・平日・上り方面)は外部ファイルに分離
# -----------------------------------------------------------------------------
from hachioji_timetable import HACHIOJI_TIMETABLE_UP_WEEKDAY

# -----------------------------------------------------------------------------
# リアルタイムの遅延情報を取得する関数
# -----------------------------------------------------------------------------
def get_realtime_delays():
    """
    JR中央線(快速)のリアルタイム列車情報をAPIから取得し、
    {列車番号: 遅延秒数} の辞書形式で返す
    """
    # 2025年API仕様に準拠したパラメータ
    params = {
        "acl:consumerKey": ACCESS_TOKEN,
        "odpt:railway": "odpt.Railway:JR-East.ChuoRapid",
        "odpt:operator": "odpt.Operator:JR-East"
    }
    
    # 2025年API仕様に準拠したヘッダー
    headers = {
        "Accept": "application/json",
        "User-Agent": "TrainInfoApp/1.0"
    }
    
    delays = {}
    try:
        # print("リアルタイム遅延情報を取得中...")
        response = requests.get(REALTIME_API_URL, params=params, headers=headers, timeout=15)
        
        # レスポンスの詳細を出力
        # print(f"ステータスコード: {response.status_code}")
        # print(f"リクエストURL: {response.url}")
        
        # 200 OK 以外の場合はエラーとして処理
        response.raise_for_status()
        train_data = response.json()
        
        # print(f"取得したデータ件数: {len(train_data)}")
        
        if train_data:
            # デバッグ用：最初の3件のデータを表示
            # print("取得データの例:")
            # for i, train in enumerate(train_data[:3]):
            #     print(f"  {i+1}. 列車ID: {train.get('owl:sameAs', 'N/A')}")
            #     print(f"     列車番号: {train.get('odpt:trainNumber', 'N/A')}")
            #     print(f"     遅延: {train.get('odpt:delay', 0)}秒")
            #     print(f"     現在位置: {train.get('odpt:fromStation', 'N/A')} → {train.get('odpt:toStation', 'N/A')}")
            
            for train in train_data:
                # 2025年API仕様での列車番号取得
                train_number = train.get("odpt:trainNumber")
                
                # 遅延情報の取得（秒単位）
                delay_seconds = train.get("odpt:delay", 0)
                
                # 列車の現在位置情報
                from_station = train.get("odpt:fromStation", "")
                to_station = train.get("odpt:toStation", "")
                
                # 八王子駅に関連する列車のみを対象にする
                hachioji_station = "odpt.Station:JR-East.ChuoRapid.Hachioji"
                
                if train_number and (hachioji_station in from_station or 
                                   "Hachioji" in from_station or
                                   "八王子" in str(train.get("odpt:trainInformationText", ""))):
                    delays[train_number] = delay_seconds
                    # print(f"  列車番号: {train_number}, 遅延: {delay_seconds}秒")
                    # print(f"    現在位置: {from_station} → {to_station}")
            
            # print(f"リアルタイムの遅延情報を取得しました。対象列車数: {len(delays)}")
        else:
            # print("現在、走行中の列車情報はありません。")
            pass

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTPエラー: {http_err}")
        if hasattr(http_err.response, 'text'):
            print(f"エラー詳細: {http_err.response.text[:500]}")
        
        # 2025年API仕様での代替エンドポイントを試行
        try:
            print("代替APIエンドポイントを試行中...")
            alternative_url = "https://api-tokyochallenge.odpt.org/api/v4/odpt:Train"
            response = requests.get(alternative_url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                train_data = response.json()
                print(f"代替API成功: {len(train_data)}件のデータを取得")
                # 上記と同じ処理ロジックを適用
                # ...existing code...
        except:
            print("代替APIも失敗しました。")
        
        print("リアルタイム遅延情報の取得をスキップします。定刻での表示を行います。")
    except requests.exceptions.RequestException as req_err:
        print(f"リクエストエラー: {req_err}")
        print("リアルタイム遅延情報の取得をスキップします。定刻での表示を行います。")
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        print("リアルタイム遅延情報の取得をスキップします。定刻での表示を行います。")
        
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

        # 遅延情報を取得（2025年API対応の検索パターン）
        train_number = entry.get("train_number")
        delay_seconds = 0
        
        # 2025年API仕様に対応した列車番号マッチング
        if train_number:
            # 完全一致を最優先
            delay_seconds = delays.get(train_number, 0)
            
            # マッチしない場合は、接尾辞を除去して再検索
            if delay_seconds == 0:
                base_number = train_number.rstrip('TCKSLAFM')
                for key, value in delays.items():
                    if key.startswith(base_number) or base_number in key:
                        delay_seconds = value
                        print(f"遅延情報マッチ: {train_number} → {key} ({delay_seconds}秒)")
                        break
        
        actual_time = scheduled_time + timedelta(seconds=delay_seconds)

        # 現在時刻より後に出発する電車をリストに追加
        if actual_time > now:
            entry_copy = entry.copy()  # 元のデータを変更しないようにコピー
            entry_copy['scheduled_time'] = scheduled_time.strftime('%H:%M')
            entry_copy['actual_time'] = actual_time.strftime('%H:%M')
            entry_copy['delay_minutes'] = delay_seconds // 60
            next_trains.append(entry_copy)

    # 到着時刻順にソートして、最初の3件を返す
    return sorted(next_trains, key=lambda x: x['actual_time'])[:3]

# ----------------------------------------------------------------------------
# メイン処理
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # 現在時刻を取得
    current_time = datetime.now()
    # current_time = datetime.strptime("2025-01-27 08:00", "%Y-%m-%d %H:%M") # テスト用

    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("八王子駅 (上り) の次の電車を検索します...")
    print("ODPT API v4 (2025年仕様) を使用")
    print("-" * 50)

    # リアルタイムの遅延情報を取得
    realtime_delays = get_realtime_delays()
    
    print("API停止中につきスキップ中")
    print("-" * 50)


    # 次の電車を検索
    next_trains_to_display = find_next_trains(current_time, HACHIOJI_TIMETABLE_UP_WEEKDAY, realtime_delays)

    # 結果を表示
    if next_trains_to_display:
        print("次の電車情報:")
        for i, train in enumerate(next_trains_to_display):
            delay_info = f"({train['delay_minutes']}分遅れ)" if train['delay_minutes'] > 0 else "(定刻)"
            print(
                f"{i+1}. {train['scheduled_time']}発 → {train['actual_time']}頃 "
                f"【{train['type']}】{train['destination']}行き "
                f"{delay_info}"
            )
    else:
        print("現在時刻以降に利用可能な電車はありません。")
    print("-" * 50)
    print("※リアルタイム情報は公共交通オープンデータセンター(ODPT)提供")

    # バス時刻表データ（キャンパス発、駅発着）
    BUS_TIMETABLE = [
        ("07:15", "07:30"), ("07:28", "07:40"), ("07:33", "07:45"), ("07:38", "07:50"), ("07:43", "07:55"),
        ("09:03", "09:15"), ("09:08", "09:20"), ("09:13", "09:25"), ("09:18", "09:30"), ("09:23", "09:35"),
        ("09:28", "09:40"), ("09:33", "09:45"), ("09:38", "09:50"), ("09:43", "09:55"), ("09:48", "10:00"),
        ("09:53", "10:05"), ("09:58", "10:10"), ("10:03", "10:15"), ("10:08", "10:20"), ("10:13", "10:25"),
        ("10:18", "10:30"), ("10:23", "10:35"), ("10:28", "10:40"), ("10:33", "10:45"), ("10:38", "10:50"),
        ("10:48", "11:00"), ("10:58", "11:10"), ("11:08", "11:20"), ("11:18", "11:30"), ("11:28", "11:40"),
        ("11:38", "11:50"), ("11:53", "12:05"), ("12:03", "12:15"), ("12:08", "12:20"), ("12:13", "12:25"),
        ("12:18", "12:30"), ("12:23", "12:35"), ("12:28", "12:40"), ("12:33", "12:45"), ("12:38", "12:50"),
        ("12:48", "13:00"), ("12:58", "13:10"), ("13:08", "13:20"), ("13:18", "13:30"), ("13:28", "13:40"),
        ("13:38", "13:50"), ("13:48", "14:00"), ("13:58", "14:10"), ("14:08", "14:20"), ("14:18", "14:30"),
        ("14:28", "14:40"), ("14:38", "14:50"), ("14:48", "15:00"), ("15:00", "15:11"),
        ("15:30", "15:41"), ("15:40", "15:51"), ("15:50", "16:01"), ("16:00", "16:11"), ("16:10", "16:21"), ("16:20", "16:31"),
        ("17:30", "17:41"), ("17:40", "17:51"), ("17:50", "18:01"), ("18:00", "18:11"), ("18:10", "18:21"),
        ("18:20", "18:31"), ("18:30", "18:41"), ("18:40", "18:51"),
        ("19:10", "19:21"), ("19:20", "19:31"), ("19:30", "19:41"), ("19:40", "19:51"), ("19:50", "20:01"),
        ("20:00", "20:11"), ("20:10", "20:21"), ("20:20", "20:31"), ("20:30", "20:41"), ("20:45", "20:56"),
        ("21:00", "21:11"), ("21:10", "21:21"), ("21:15", "21:26"), ("21:20", "21:31")
    ]

    # シャトル運行の時間帯定義
    SHUTTLE_PERIODS = [
        ("07:55", "09:03", "約3～5分間隔"),
        ("15:11", "15:30", "約5～10分間隔"),
        ("16:31", "17:30", "約3～10分間隔"),
        ("18:51", "19:10", "約5～10分間隔")
    ]

    # バス時刻表の表示
    print("\n八王子駅⇔東京工科大学 シャトルバス時刻表（抜粋）")
    print("-" * 50)
    print("八王子駅南口［発着所：片柳研究所西側］")
    
    # 現在時刻以降のバス3本を表示
    now_hm = current_time.strftime("%H:%M")
    count = 0
    found_future_bus = False
    
    # シャトル運行期間をチェック
    def is_in_shuttle_period(time_str):
        for start, end, interval in SHUTTLE_PERIODS:
            if start <= time_str <= end:
                return interval
        return None
    
    # まずシャトル運行期間をチェック
    shuttle_info = is_in_shuttle_period(now_hm)
    if shuttle_info:
        print(f"現在はシャトル運行中（{shuttle_info}）")
        found_future_bus = True
        count = 1
    
    # 通常の時刻表から次のバスを探す
    for campus_dep, station_arr in BUS_TIMETABLE:
        if campus_dep >= now_hm and count < 3:
            found_future_bus = True
            print(f"キャンパス発{campus_dep} → 駅発着{station_arr}")
            count += 1
    
    # 未来のシャトル運行期間もチェック
    if count < 3:
        for start, end, interval in SHUTTLE_PERIODS:
            if start > now_hm and count < 3:
                print(f"{start}〜{end} シャトル運行（{interval}）")
                count += 1
    
    if not found_future_bus:
        print("本日の運行は終了しました。")
    elif count == 0:
        print("現在時刻以降のバスはありません。")

print("-" * 50)

# アクセスするURL
url = "https://transit.yahoo.co.jp/diainfo/38/0"

# URLにアクセスする
res = requests.get(url)


# res.textをBeautifulSoupで扱うための処理
soup = BeautifulSoup(res.content, "html.parser")

st = soup.find_all("dt")

for dt in st:
    print(dt.get_text(strip=True))

mes = soup.find_all("dd")

for dt in mes:
    print(dt.get_text(strip=True))
