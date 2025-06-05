import pandas as pd
import os
from pathlib import Path
import streamlit as st
from datetime import datetime
import warnings
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import shutil
import json
warnings.filterwarnings('ignore')

# プロファイルパスを定数として定義
PROFILE_PATH = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\python"

def initialize_driver(headless=False):
    """ドライバーの初期化と認証を行う"""
    username = os.getenv('USERNAME')
    
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={PROFILE_PATH}')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-extensions')
    
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 既存のプロファイルをクリーンアップ
    try:
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
        os.makedirs(PROFILE_PATH, exist_ok=True)
    except Exception as e:
        print(f"プロファイルのクリーンアップエラー: {str(e)}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"ドライバー初期化リトライ {attempt + 1}/{max_retries}")
            time.sleep(2)

def check_midway_auth():
    """Midway認証の有効期限をチェック"""
    midway_file = os.path.join(PROFILE_PATH, 'Midway')
    
    if os.path.exists(midway_file):
        with open(midway_file, 'r') as f:
            last_auth_date = f.read().strip()
        if last_auth_date == datetime.now().strftime('%Y/%m/%d'):
            return True   
    return False

def update_midway_auth():
    """Midway認証の日付を更新"""
    midway_file = os.path.join(PROFILE_PATH, 'Midway')
    os.makedirs(os.path.dirname(midway_file), exist_ok=True)
    with open(midway_file, 'w') as f:
        f.write(datetime.now().strftime('%Y/%m/%d'))

def perform_midway_auth(driver):
    """Midway認証を実行"""
    username = os.getenv('USERNAME')
    if not username:
        raise ValueError("USERNAMEが設定されていません")
    
    hng_path = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\__hng"
    wait = WebDriverWait(driver, 30)
    
    driver.get("https://midway-auth.amazon.com/login")
    username_input = wait.until(EC.presence_of_element_located((By.ID, "user_name")))
    username_input.send_keys(username)
    
    with open(hng_path, 'r') as f:
        password = f.read().strip()
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)
    
    driver.find_element(By.ID, "verify_btn").click()
    wait.until_not(EC.presence_of_element_located((By.ID, "login_form")))
    update_midway_auth()
    return True

def get_service_area_id(station_code: str) -> str:
    df = pd.read_csv("C:\\Users\\tangtao\\Desktop\\TAO\\Routine\\data\\dsp_info.csv")
    return str(df[df['station_code'] == station_code]['service_area_id'].iloc[0])

def get_delivery_info(driver, station_code):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            service_area_id = get_service_area_id(station_code)
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            api_url = f"https://logistics.amazon.co.jp/internal/operations/execution/api/summaries?historicalDay=false&localDate={date_str}&serviceAreaId={service_area_id}"
            
            driver.get(api_url)
            wait = WebDriverWait(driver, 30)  # タイムアウトを30秒に延長
            
            # ページの完全なロードを待機
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(2)  # 追加の待機時間
            
            # preタグの存在を確認
            pre_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "pre")),
                message="JSONデータが見つかりません"
            )
            
            json_text = pre_element.text
            if not json_text:
                raise ValueError("JSONデータが空です")
            
            data = json.loads(json_text)
            delivery_data = []
            
            for itinerary in data.get('itinerarySummaries', []):
                try:
                    transporter_id = itinerary.get('transporterId')
                    transporter_info = next((t for t in data.get('transporters', []) 
                                          if t.get('transporterId') == transporter_id), {})
                    
                    route_codes = itinerary.get('routeCodes', [])
                    route_str = ' '.join(str(code) for code in route_codes) if route_codes else ''
                    
                    progress_status = itinerary.get('progressStatus', '')
                    risk_status = {'BEHIND': '赤', 'AT_RISK': '黄'}.get(progress_status, '青')
                    
                    route_delivery_progress = itinerary.get('routes', [{}])[0].get('routeDeliveryProgress', {})
                    total_deliveries = route_delivery_progress.get('totalDeliveries', 0)
                    completed_deliveries = route_delivery_progress.get('completedDeliveries', 0)
                    
                    delivery_data.append({
                        "名前": f"{transporter_info.get('firstName', '')} {transporter_info.get('lastName', '')}".strip(),
                        "ルート": route_str,
                        "TransporterID": transporter_id,
                        "電話": transporter_info.get('workPhoneNumber', ''),
                        "リスク": risk_status,
                        "全配達": total_deliveries,
                        "完了配達": completed_deliveries,
                        "状態": "ログアウト" if itinerary.get('sessionEndTime') else ""
                    })
                    
                except Exception as e:
                    print(f"配送員データの処理中にエラー: {str(e)}")
                    continue
            
            df = pd.DataFrame(delivery_data)
            if df.empty:
                if attempt < max_retries - 1:
                    print(f"データが空です。リトライ {attempt + 1}/{max_retries}")
                    time.sleep(3)
                    continue
                else:
                    raise ValueError("データを取得できませんでした")
                    
            if not df.empty:
                numeric_columns = ['全配達', '完了配達']
                df[numeric_columns] = df[numeric_columns].astype(int)
            
            return df
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"エラーが発生しました。リトライ {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(3)
                driver.refresh()
                continue
            else:
                raise
    
    return pd.DataFrame()

def get_roster_data(driver, station_code):
    try:
        service_area_id = get_service_area_id(station_code)
        date_str = datetime.now().strftime('%Y-%m-%d')
        roster_url = f"https://logistics.amazon.co.jp/internal/capacity/rosterview?serviceAreaId={service_area_id}&date={date_str}"
        
        driver.get(roster_url)
        wait = WebDriverWait(driver, 30)
        
        max_retries = 5
        roster_data = []
        
        for attempt in range(max_retries):
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                time.sleep(2)
                
                try:
                    flex_table = wait.until(EC.presence_of_element_located((By.ID, "cspDATable")))
                    wait.until(EC.visibility_of_element_located((By.ID, "cspDATable")))
                except Exception:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        driver.refresh()
                        continue
                    else:
                        raise
                
                flex_rows = flex_table.find_elements(By.TAG_NAME, "tr")[1:]
                
                if not flex_rows and attempt < max_retries - 1:
                    time.sleep(3)
                    driver.refresh()
                    continue
                
                for row in flex_rows:
                    try:
                        cols = wait.until(lambda d: row.find_elements(By.TAG_NAME, "td"))
                        if len(cols) >= 7:
                            data = {
                                "DP ID": cols[0].text.strip(),
                                "DP名": cols[1].text.strip(),
                                "ステータス": cols[2].text.strip(),
                                "サービスタイプ": cols[3].text.strip(),
                                "開始時刻": cols[5].text.strip(),
                                "終了時間": cols[6].text.strip(),
                                "サイクル": cols[-1].text.strip()
                            }
                            if any(data.values()):
                                roster_data.append(data)
                    except Exception:
                        continue
                
                if roster_data:
                    break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    driver.refresh()
                    continue
                else:
                    raise
        
        return pd.DataFrame(roster_data).fillna('')
        
    except Exception as e:
        st.error(f"Station {station_code}: データの取得に失敗: {str(e)}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="RoutineTask", page_icon="📋")
    
    st.sidebar.title("メニュー")
    app_mode = st.sidebar.radio(
        "アプリケーション選択",
        options=["Cortex", "Roster"],
        horizontal=True
    )

    # Midwayリセットボタン
    if st.sidebar.button("Midwayリセット"):
        try:
            if os.path.exists(PROFILE_PATH):
                shutil.rmtree(PROFILE_PATH)
                st.sidebar.success("Midwayセッションをリセットしました")
        except Exception as e:
            st.sidebar.error(f"リセット失敗: {str(e)}")

    # Midway認証チェック
    if not check_midway_auth():
        with st.spinner("Midway認証を実行中..."):
            driver = None
            try:
                driver = initialize_driver(headless=False)
                perform_midway_auth(driver)
                st.success("認証完了")
            except Exception as e:
                st.error(f"認証エラー: {str(e)}")
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except:
                        pass

    # 検索インターフェース
    station_input = st.text_input("", placeholder="Station Code (例: DAI1)").strip().upper()

    if station_input:
        with st.spinner(f"Station {station_input} のデータを取得中..."):
            driver = None
            try:
                driver = initialize_driver(headless=True)
                
                if app_mode == "Cortex":
                    df = get_delivery_info(driver, station_input)
                    if not df.empty:
                        df['Station'] = station_input
                        df['電話'] = df['電話'].str.replace('+81', '0').apply(
                            lambda x: ''.join(filter(str.isdigit, str(x)))).apply(
                            lambda x: f"{x[:3]}-{x[3:7]}-{x[7:]}" if len(x) == 11 else x)
                        
                        columns_order = ['Station', '名前', 'ルート', 'TransporterID', '電話', 
                                       'リスク', '全配達', '完了配達', '状態']
                else:
                    df = get_roster_data(driver, station_input)
                    if not df.empty:
                        df['Station'] = station_input
                        columns_order = ['Station', 'DP名', 'DP ID', 'ステータス', 
                                       '開始時刻', '終了時間', 'サイクル', 'サービスタイプ']
                
                if not df.empty:
                    final_df = df[columns_order]
                    st.dataframe(final_df, hide_index=True,
                               column_config={col: st.column_config.Column(width="small") 
                                            for col in final_df.columns})
                    st.info(f"総配送員数: {len(final_df)}")
                
            except Exception as e:
                st.error(f"Station {station_input}: {str(e)}")
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except:
                        pass

if __name__ == "__main__":
    main()
