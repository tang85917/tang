import os
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import pandas as pd
import time
import shutil
import concurrent.futures

def initialize_driver(headless=False):
    profile_path = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\python"
    
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-extensions')
        
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        st.error(f"ブラウザの初期化エラー: {str(e)}")
        if os.path.exists(profile_path):
            try:
                shutil.rmtree(profile_path)
                st.warning("プロファイルをリセットしました。もう一度お試しください。")
            except Exception as e:
                st.error(f"プロファイルの削除に失敗: {str(e)}")
        raise

def get_service_area_id(station_code: str) -> str:
    df = pd.read_csv("C:\\Users\\tangtao\\Desktop\\TAO\\Routine\\data\\dsp_info.csv")
    return str(df[df['station_code'] == station_code]['service_area_id'].iloc[0])

def get_roster_data(driver, station_code):
    try:
        service_area_id = get_service_area_id(station_code)
        date_str = datetime.now().strftime('%Y-%m-%d')
        roster_url = f"https://logistics.amazon.co.jp/internal/capacity/rosterview?serviceAreaId={service_area_id}&date={date_str}"
        
        driver.get(roster_url)
        time.sleep(5)  # 待機時間を5秒に増加
        
        wait = WebDriverWait(driver, 30)  # タイムアウトを30秒に増加
        roster_data = []
        
        max_retries = 5  # リトライ回数を5回に増加
        for attempt in range(max_retries):
            try:
                # ページが完全に読み込まれるまで待機
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                time.sleep(2)  # 追加の待機時間
                
                try:
                    flex_table = wait.until(EC.presence_of_element_located((By.ID, "cspDATable")))
                    wait.until(EC.visibility_of_element_located((By.ID, "cspDATable")))
                except Exception as table_error:
                    st.warning(f"Station {station_code}: テーブルの読み込みに失敗 (試行 {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        driver.refresh()  # ページをリフレッシュ
                        continue
                    else:
                        raise table_error
                
                flex_rows = flex_table.find_elements(By.TAG_NAME, "tr")[1:]
                
                if not flex_rows:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        driver.refresh()
                        continue
                
                for row in flex_rows:
                    try:
                        # 各行の読み込みを待機
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
                            # データの検証
                            if any(data.values()):
                                roster_data.append(data)
                    except Exception as row_error:
                        st.warning(f"Station {station_code}: 行データの取得エラー: {str(row_error)}")
                        continue
                
                if roster_data:
                    st.success(f"Station {station_code}: データ取得成功 ({len(roster_data)}件)")
                    break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    driver.refresh()
                    continue
                else:
                    raise e

        if not roster_data:
            st.warning(f"Station {station_code}: データが見つかりませんでした。")
        
        return pd.DataFrame(roster_data).fillna('')
        
    except Exception as e:
        st.error(f"Station {station_code}: データの取得に失敗: {str(e)}")
        return pd.DataFrame()

def process_station(station_code):
    """1つのステーションのデータを処理"""
    driver = None
    try:
        driver = initialize_driver(headless=True)
        df = get_roster_data(driver, station_code)
        if not df.empty:
            df['Station'] = station_code
            return df
    except Exception as e:
        st.error(f"Station {station_code} の処理中にエラー: {str(e)}")
        return pd.DataFrame()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    st.title("Flex Roster Viewer")

    station_input = st.text_area(
        "Station Codes",
        help="1行1ステーション",
        placeholder="""例：
TKY1
DAI1
OCJ5""",
        height=100
    ).strip().upper()
    
    # 重複を除去して一意のステーションリストを作成
    selected_stations = list(dict.fromkeys([s.strip() for s in station_input.split('\n') if s.strip()]))

    if selected_stations:
        with st.spinner("データを取得中..."):
            all_data = []
            processed_stations = set()  # 処理済みステーションを追跡
            
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # 同時実行数を2に制限し、処理間隔を設定
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # 処理するステーションをキューに追加
                future_to_station = {}
                for station in selected_stations:
                    if station not in processed_stations:
                        future = executor.submit(process_station, station)
                        future_to_station[future] = station
                        processed_stations.add(station)
                        time.sleep(1)  # ステーション間の待機時間
                
                completed = 0
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
                            st.success(f"Station {station}: データ取得成功 ({len(df)} 件)")
                            all_data.append(df)
                        else:
                            st.warning(f"Station {station}: データなし")
                    except Exception as e:
                        st.error(f"Station {station}: 処理失敗 - {str(e)}")
            
            if progress_bar is not None:
                progress_bar.progress(1.0)
            if status_text is not None:
                status_text.text(f"処理完了! 100% (全 {len(selected_stations)} 件)")
            
            time.sleep(1)
            progress_container.empty()
            
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                columns_order = ['Station', 'DP名', 'DP ID', 'ステータス', 
                               '開始時刻', '終了時間', 'サイクル', 
                               'サービスタイプ']
                final_df = final_df[columns_order]
                
                st.dataframe(
                    final_df,
                    hide_index=True,
                    column_config={col: st.column_config.Column(width="small") for col in final_df.columns}
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"総配送員数: {len(final_df)}")
                with col2:
                    station_summary = final_df.groupby('Station').size()
                    st.info(f"Station別配送員数:\n{station_summary.to_string()}")

if __name__ == "__main__":
    main()
