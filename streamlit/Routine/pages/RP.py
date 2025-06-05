import os
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import shutil
import json
import concurrent.futures
import time

def check_midway_auth():
    profile_path = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\python"
    midway_file = f"{profile_path}\\Midway"

    is_valid = (os.path.exists(midway_file) and 
                open(midway_file).read().strip() == datetime.now().strftime('%Y/%m/%d'))
    
    return is_valid, profile_path

def update_midway_auth():
    midway_file = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\python\\Midway"
    os.makedirs(os.path.dirname(midway_file), exist_ok=True)
    with open(midway_file, 'w') as f:
        f.write(datetime.now().strftime('%Y/%m/%d'))

def get_service_area_id(station_code: str) -> str:
    df = pd.read_csv("C:\\Users\\tangtao\\Desktop\\TAO\\Routine\\data\\dsp_info.csv")
    return str(df[df['station_code'] == station_code]['service_area_id'].iloc[0])

def initialize_driver(headless=False):
    profile_path = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\python"
    
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument('--disable-gpu')
    if headless:
        options.add_argument('--headless=new')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def perform_midway_auth(driver):
    username = os.getenv('USERNAME')
    if not username:
        raise ValueError("USERNAMEが設定されていません")
    
    hng_path = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\__hng"
    wait = WebDriverWait(driver, 30)
    
    driver.get("https://midway-auth.amazon.com/login")
    username_input = wait.until(EC.presence_of_element_located((By.ID, "user_name")))
    username_input.send_keys(username)
    
    # パスワードの読み込みと復号化
    def decrypt_password(encrypted):
        return ''.join(chr(ord(c) - 1) for c in encrypted)
    
    with open(hng_path, 'r') as f:
        encrypted_password = f.read().strip()
        password = decrypt_password(encrypted_password)
    
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)
    
    driver.find_element(By.ID, "verify_btn").click()
    
    wait.until_not(EC.presence_of_element_located((By.ID, "login_form")))
    update_midway_auth()
    return True

def get_delivery_info(driver, station_code):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            service_area_id = get_service_area_id(station_code)
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            api_url = f"https://logistics.amazon.co.jp/internal/operations/execution/api/summaries?historicalDay=false&localDate={date_str}&serviceAreaId={service_area_id}"
            driver.get(api_url)
            
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
            
            json_text = driver.find_element(By.TAG_NAME, "pre").text
            if not json_text:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return pd.DataFrame()
            
            data = json.loads(json_text)
            delivery_data = []
            
            for itinerary in data.get('itinerarySummaries', []):
                try:
                    # Flex配送員のみを抽出
                    company_id = itinerary.get('companyId')
                    company_info = next((c for c in data.get('companies', []) if c.get('companyId') == company_id), {})
                    if company_info.get('companyName') != 'Amazon Flex':
                        continue
                    
                    transporter_id = itinerary.get('transporterId')
                    transporter_info = next((t for t in data.get('transporters', []) if t.get('transporterId') == transporter_id), {})
                    
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
                        "電話": transporter_info.get('workPhoneNumber', ''),  # フォーマット処理を削除
                        "リスク": risk_status,
                        "全配達": total_deliveries,
                        "完了配達": completed_deliveries,
                        "状態": "ログアウト" if itinerary.get('sessionEndTime') else ""
                    })
                    
                except Exception as e:
                    continue
            
            if delivery_data:
                df = pd.DataFrame(delivery_data)
                numeric_columns = ['全配達', '完了配達']
                df[numeric_columns] = df[numeric_columns].astype(int)
                return df
            
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                st.error(f"Station {station_code}: エラー発生 - {str(e)}")
    
    return pd.DataFrame()

def process_station(station_code):
    """1つのステーションのデータを処理"""
    max_retries = 2
    for attempt in range(max_retries):
        driver = None
        try:
            driver = initialize_driver(headless=True)
            df = get_delivery_info(driver, station_code)
            if not df.empty:
                df['Station'] = station_code
                return df
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            st.error(f"Station {station_code} の処理中にエラー: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    return pd.DataFrame()

def main():
    st.title("Flex配送員情報")

    with st.sidebar:
        if st.button("セッションリセット"):
            _, profile_path = check_midway_auth()
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                st.success("セッションをリセットしました")

    # 検索セクションのコンテナ
    search_container = st.container()
    
    with search_container:
        # 2列に分割（左側が広い）
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if 'station_input' not in st.session_state:
                st.session_state.station_input = ""

            station_input = st.text_area(
                "Station Codes",
                value=st.session_state.station_input,
                help="1行1ステーション",
                placeholder="DAI1\nONGA",
                height=68, 
            ).strip().upper()

            st.session_state.station_input = station_input

        with col2:
            # ボタンの位置を調整
            st.write("")
            search_button = st.button("🔍 検索", use_container_width=True)

    # 説明文を小さく表示
    st.caption("Station Codeを入力してください（1行1ステーション）")

    selected_stations = list(dict.fromkeys([s.strip() for s in station_input.split('\n') if s.strip()]))

    if search_button:
        if selected_stations:
            is_valid, _ = check_midway_auth()
            
            if not is_valid:
                with st.spinner("Midway認証を実行中..."):
                    driver = initialize_driver(headless=False)
                    try:
                        if perform_midway_auth(driver):
                            st.success("認証完了")
                    finally:
                        driver.quit()
            
            with st.spinner("データを取得中..."):
                all_data = []
                
                # プログレス表示用のコンテナ
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    processing_text = st.empty()
                
                # 並列処理の実行
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_station = {executor.submit(process_station, station): station 
                                       for station in selected_stations}
                    
                    completed = 0
                    successful = 0
                    
                    for future in concurrent.futures.as_completed(future_to_station):
                        station = future_to_station[future]
                        completed += 1
                        
                        progress = completed / len(selected_stations)
                        progress_percentage = int(progress * 100)
                        
                        if progress_bar is not None:
                            progress_bar.progress(progress)
                        if status_text is not None:
                            status_text.text(f"処理中... {progress_percentage}% ({completed}/{len(selected_stations)} 件完了)")
                        
                        try:
                            df = future.result()
                            if df is not None and not df.empty:
                                all_data.append(df)
                                successful += 1
                                processing_text.text(f"Station {station}: データ取得成功 ({successful}/{len(selected_stations)}件成功)")
                            else:
                                processing_text.text(f"Station {station}: データなし")
                        except Exception as e:
                            processing_text.text(f"Station {station}: 処理失敗 - {str(e)}")
                
                # 処理完了後のメッセージ
                status_text.text(f"処理完了! (成功: {successful}/{len(selected_stations)}件)")
                
                # データの表示処理
                if all_data:
                    # プログレス表示をクリア
                    progress_container.empty()
                    
                    # データの結合と処理
                    final_df = pd.concat(all_data, ignore_index=True)
                    
                    # 電話番号の整形
                    final_df['電話'] = final_df['電話'].str.replace('+81', '0', regex=False)
                    final_df['電話'] = final_df['電話'].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
                    final_df['電話'] = final_df['電話'].apply(lambda x: f"{x[:3]}-{x[3:7]}-{x[7:]}" if len(x) == 11 else x)
                    
                    # カラム順序の設定
                    columns_order = ['Station', '名前', 'ルート', 'TransporterID', '電話', 
                                   'リスク', '全配達', '完了配達', '状態']
                    final_df = final_df[columns_order]
                    
                    # データフレームの表示
                    st.dataframe(
                        final_df,
                        hide_index=True,
                        column_config={col: st.column_config.Column(width="small") for col in final_df.columns}
                    )
                    
                    # サマリー情報の表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Flex配送員数: {len(final_df)}")
                    with col2:
                        station_summary = final_df.groupby('Station').size()
                        st.info(f"Station別配送員数:\n{station_summary.to_string()}")
                else:
                    progress_container.empty()
                    st.warning("取得できたデータがありません")
        else:
            st.warning("Station Codeを入力してください。")

if __name__ == "__main__":
    main()
