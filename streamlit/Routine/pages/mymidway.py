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

USERNAME = os.getenv('USERNAME')
MIDWAY_FILE = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\python\\Midway"

def check_midway_auth():
    profile_path = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\python"
    is_valid = (os.path.exists(MIDWAY_FILE) and 
                open(MIDWAY_FILE).read().strip() == datetime.now().strftime('%Y/%m/%d'))
    return is_valid, profile_path

def update_midway_auth():
    os.makedirs(os.path.dirname(MIDWAY_FILE), exist_ok=True)
    with open(MIDWAY_FILE, 'w') as f:
        f.write(datetime.now().strftime('%Y/%m/%d'))
        
def get_service_area_id(station_code: str) -> str:
    df = pd.read_csv("data\\dsp_info.csv")
    return set(df[df['station_code'] == station_code]['service_area_id'].iloc[0])

def initialize_driver(headless=False):
    profile_path = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\python"
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument('--disable-gpu')
    if headless:
        options.add_argument('--headless=new')
    #options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver
    
def perform_midway_auth(driver):
    hng_path = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\__hng"
    wait = WebDriverWait(driver, 60)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "user_name")))
    username_input.send_keys(USERNAME)
    
    with open(hng_path, 'r') as f:
        password = f.read().strip()
    password_input = wait.until(EC.presence_of_element_located((By.ID, 'password')))
    password_input.send_keys(password)
    
    verify_btn = wait.until(EC.element_to_be_clickable((By.ID, 'verify_btn')))
    verify_btn.click()
    
    wait.until_not(EC.presence_of_element_located((By.ID, "login_form")))
    update_midway_auth()
    return True
    
def get_cortex_data(driver, node):
    try:
        service_area_id = get_service_area_id(node)
        today = datetime.now().strftime('%Y-%m-%d')
        
        api_url = f"https://logistics.amazon.co.jp/internal/operations/execution/api/summaries?historicalDay=false&localDate={today}&serviceAreaId={service_area_id}"
        driver.get(api_url)
        
        wait = WebDriverWait(driver, 180)
        json_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'pre'))).text
        
        data = json.loads(json_text)
        dp_data =[]
        
        for itinerary in data.get('itinerarySummaries', []):
            try:
                transporter_id = itinerary.get('transporterId')
                transporter_info = next((t for t in data.get('transporters', []) if t.get('transporterId') == transporter_id), {})
                
                route_codes = itinerary.get('routeCodes', [])
                route = ','.join(str(r) for r in route) if route else ''
                
                progress_status = itinerary.get('progressStatus', '')
                risk_status = {'BEHIND': '赤', 'AT_RISK': '黄'}.get(progress_status, '青')
                
                route_delivery_progress = itinerary.get('routes', [{}])[0].get('routeDeliveryProgress', {})
                total_deliveries = route_delivery_progress.get('totalDeliveries', 0)
                completed_deliveries = route_delivery_progress.get('completedDeliveries', 0)
                
                dp_data.append({
                    "Name": f"{transporter_info.get('firstName', '')} {transporter_info.get('lastName', '')}".strip(),
                    "Route": route,
                    "Id": transporter_id,
                    "Phone": transporter_info.get('workPhoneNumber', ''),
                    "Pkg_done" : completed_deliveries,
                    "Pkg_total": total_deliveries,
                    "Risk": risk_status
                })

            except Exception:
                continue
                
        if dp_data:
            df = pd.DataFrame(dp_data)
            return df
        
    except Exception as e:
        st.error(f"Station {node}: エラー発生 - {str(e)}")
            
    return pd.DataFrame

def cortex_process(node):
    driver = None
    try:
        driver = initialize_driver(headless=True)
        df = get_cortex_data(driver, node)
        if df:
            df['Node'] = node
            return df
    except Exception as e:
        st.error(f"Station {node} の処理中にエラー: {str(e)}")
    finally:
        if driver:
            driver.quit()
    return pd.DataFrame()

def main():
    st.title('Flex配送員情報')
    
    with st.sidebar:
        if st.button('Midway reset'):
            _, profile_path = check_midway_auth()
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                st.success('セッションをリセットしました')
                
    station_input = st.text_area(
        'Node名を入力してください',
        help='1行1Node',
        placeholder='DAI1\nONGA\nOCJ5',
        height=70
    ).strip().upper()
        
    st.caption("Station Codeを入力してください（1行1ステーション）")

    selected_stations = list(dict.fromkeys([s.strip() for s in station_input.split('\n') if s.strip()]))
    
    if selected_stations:
        is_valid, _ = check_midway_auth()
        
        if not is_valid:
            with st.spinner('Midway認証を実行中🤡☠️👻🙈🙉🙊'):
                driver = initialize_driver(headless=False)
                try:
                    if perform_midway_auth(driver):
                        st.success('認証完了')
                finally:
                    driver.quit()
                    
        with st.spinner('Cortexからデータを取得中...'):
            all_data = []
            
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                processing_text = st.empty()
                
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_station = {executor.submit(cortex_process, station): station
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
                        status_text.text(f"処理中...{progress_percentage}% ({completed} / {len(selected_stations)}件完了) ")
                        
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
                        
            status_text.text(f"処理完了! (成功: {successful}/{len(selected_stations)}件)")
            
            if all_data:
                progress_container.empty()
                final_df = pd.concat(all_data,ignore_index=True)
                
                final_df['電話'] = final_df['電話'].str.replace('+81', '0', regex=False)
                final_df['電話'] = final_df['電話'].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
                final_df['電話'] = final_df['電話'].apply(lambda x: f'{x[:3]}-{x[3:7]}-{x[7:]}' if len(x) == 11 else x)
                
                columns_order = ['Node', 'Name', 'Route', 'Id', 'Phone', 'Risk', 'Pkg_done', 'Pkg_total']
                final_df = final_df[columns_order]
                
                st.dataframe(final_df, hide_index=True,
                            column_config={col: st.column_config.Column(width='small') for col in final_df.columns})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"Flex配送員数: {len(final_df)}")
                with col2:
                    station_summary = final_df.groupby('Node').size()
                    st.info(f"Station別配送員数:\n{station_summary.to_string()}")
            else:
                progress_container.empty()
                st.warning('データ取得が失敗しました')
    else:
        st.warning("Station Codeを入力してください。")
        
if __name__ == "__main__":
    main()