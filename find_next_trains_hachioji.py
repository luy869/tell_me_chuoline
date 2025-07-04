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