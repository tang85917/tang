import streamlit as st
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import urllib3
from urllib.parse import quote
import webbrowser
import os
from pathlib import Path
import pandas as pd
from io import StringIO
from datetime import datetime

# SSL証明書の警告を無視
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SharePointのURL設定
BASE_URL = "https://share.amazon.com"
FOLDER_URL = "https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('/sites/COJP_ORM/Shared Documents/05_DS_Rescue/2025/RP')/Files?$select=Name,ServerRelativeUrl,UniqueId"

# データディレクトリの設定
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

@st.cache_data(ttl=28800)  # 1時間キャッシュ
def get_files_and_guids():
    """SharePointからファイル一覧とGUIDを一度に取得"""
    try:
        session = requests.Session()
        auth = HttpNegotiateAuth()
        headers = {
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'Python NTLM Client'
        }
        
        response = session.get(
            FOLDER_URL,
            auth=auth,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            files = data['d']['results']
            
            file_info = []
            guid_map = {}
            
            for file in files:
                if file['Name'].lower().endswith(('.xlsx', '.xlsm')):
                    file_info.append({
                        'name': file['Name'],
                        'button_name': file['Name'].split()[0],
                        'server_relative_url': file['ServerRelativeUrl'],
                        'guid': file['UniqueId']
                    })
                    guid_map[file['ServerRelativeUrl']] = file['UniqueId']

            def sort_key(item):
                name = item['button_name']
                # 数値部分とそれ以外の部分を分離
                numeric_part = ""
                alpha_part = ""
                for char in name:
                    if char.isdigit():
                        numeric_part += char
                    else:
                        alpha_part += char
                
                # 1. 数字で始まるものを優先（例：1VIT, 2VIT）
                if name[0].isdigit():
                    return (0, int(numeric_part), alpha_part)
                # 2. Vで始まるものを次に（例：VIT1, VKI1）
                elif name.startswith('V'):
                    return (1, alpha_part, numeric_part if numeric_part else "999999")
                # 3. その他のアルファベット（例：Mini, Shinka）
                else:
                    return (2, alpha_part, numeric_part if numeric_part else "999999")

            # ソート実行
            file_info = sorted(file_info, key=sort_key)
            
            return file_info, guid_map
        else:
            st.error(f"SharePointからのデータ取得に失敗しました。ステータスコード: {response.status_code}")
            return [], {}
            
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return [], {}

def create_excel_url(web_url):
    """Excelで開くためのURLを生成（新しいセッションで開く）"""
    return f"ms-excel:ofv|u|{web_url}"

def create_browser_url(file_info, guid):
    """ブラウザで開くためのURLを生成"""
    encoded_filename = quote(file_info['name'])
    return f"{BASE_URL}/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc={{{guid}}}&file={encoded_filename}&action=default"

def download_file(file_info):
    """ファイルをダウンロードして別セッションで開く"""
    try:
        session = requests.Session()
        auth = HttpNegotiateAuth()
        file_url = f"{BASE_URL}{file_info['server_relative_url']}"
        
        response = session.get(
            file_url,
            auth=auth,
            verify=False,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            downloads_path = str(Path.home() / "Downloads")
            temp_file_path = os.path.join(downloads_path, f"temp_{file_info['name']}")
            file_path = os.path.join(downloads_path, file_info['name'])
            
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                base, ext = os.path.splitext(file_path)
                counter = 1
                while os.path.exists(file_path):
                    file_path = f"{base}_{counter}{ext}"
                    counter += 1
            
            os.rename(temp_file_path, file_path)
            os.system(f'start "" "{file_path}"')
            return file_path
            
        else:
            st.error(f"ダウンロードに失敗しました。ステータスコード: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"ダウンロードエラー: {str(e)}")
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        return None

# Streamlitページの設定
st.set_page_config(
    page_title="SharePoint Files",
    page_icon="📁",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
    <style>
        div.stButton > button {
            margin: 5px 0;
            background-color: #1E90FF;
            color: white;
        }
        div.stButton > button:hover {
            background-color: #0066CC;
            color: white;
        }
        .stRadio [role=radiogroup] {
            gap: 0px;
            background-color: #87CEEB;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# サイドバーの設定
with st.sidebar:
    st.title("🎐Cortex&Roster&SUI")
    
    # 現在の日付を取得
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Cortex
    cortex_code = st.text_input(label="Cortex DS Code", key="cortex").upper()
    if cortex_code != st.session_state.get('last_cortex', ''):
        try:
            df = pd.read_csv(DATA_DIR / 'dsp_info.csv')
            df['station_code'] = df['station_code'].str.upper()
            service_area_id = df[df['station_code'] == cortex_code]['service_area_id'].iloc[0]
            cortex_url = f"https://logistics.amazon.co.jp/internal/operations/execution/itineraries?provider=ALL_DRIVERS&selectedDay={today}&serviceAreaId={service_area_id}"
            webbrowser.open(cortex_url)
            st.success(f"Opening Cortex for {cortex_code}")
        except Exception as e:
            if cortex_code:  # 空文字列でない場合のみエラーを表示
                st.error(f"DSP Code not found or error occurred: {str(e)}")
        st.session_state['last_cortex'] = cortex_code
    
    st.markdown("---")
    
    # Roster
    roster_code = st.text_input(label="Roster DS Code", key="roster").upper()
    if roster_code != st.session_state.get('last_roster', ''):
        try:
            df = pd.read_csv(DATA_DIR / 'dsp_info.csv')
            df['station_code'] = df['station_code'].str.upper()
            service_area_id = df[df['station_code'] == roster_code]['service_area_id'].iloc[0]
            roster_url = f"https://logistics.amazon.co.jp/internal/capacity/rosterview?serviceAreaId={service_area_id}&date={today}"
            webbrowser.open(roster_url)
            st.success(f"Opening Roster for {roster_code}")
        except Exception as e:
            if roster_code:  # 空文字列でない場合のみエラーを表示
                st.error(f"DSP Code not found or error occurred: {str(e)}")
        st.session_state['last_roster'] = roster_code
    
    st.markdown("---")
    
    # SUI
    sui_code = st.text_input(label="SUI DS Code", key="sui").upper()
    if sui_code != st.session_state.get('last_sui', ''):
        try:
            df = pd.read_csv(DATA_DIR / 'dsp_info.csv')
            df['station_code'] = df['station_code'].str.upper()
            service_area_id = df[df['station_code'] == sui_code]['service_area_id'].iloc[0]
            sui_url = f"https://logistics.amazon.co.jp/internal/scheduling/dsps?serviceAreaId={service_area_id}&date={today}"
            webbrowser.open(sui_url)
            st.success(f"Opening SUI for {sui_code}")
        except Exception as e:
            if sui_code:  # 空文字列でない場合のみエラーを表示
                st.error(f"DSP Code not found or error occurred: {str(e)}")
        st.session_state['last_sui'] = sui_code
    
    st.markdown("---")
    
    # dsp_info_Downloadボタン
    if st.button("dsp_info_Download", use_container_width=True):
        url = "https://share.amazon.com/sites/COJP_ORM/Shared%20Documents/04_Metrics/dsp_info.txt"
        file_name = 'dsp_info.csv'
        
        try:
            session = requests.Session()
            auth = HttpNegotiateAuth()
            response = session.get(url, auth=auth, verify=False, timeout=30)
            
            if response.status_code == 200:
                df = pd.read_csv(
                    StringIO(response.content.decode('utf-8')), 
                    sep='\t',
                    usecols=['station_code', 'service_area_id']
                )
                
                file_path = DATA_DIR / file_name
                df.to_csv(file_path, index=False)
                
                st.success(f"{file_name} がダウンロードされました。")
            
            else:
                st.error(f"ダウンロードに失敗しました。")
        
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

# メインコンテンツ
st.title("📁 SharePoint Files")

# 表示モード選択のラジオボタン
display_mode = st.radio(
    "開き方を選択してください:",
    ["ブラウザで開く", "Excelで開く", "Download"],
    horizontal=True
)

# ファイル一覧を取得
files, guid_map = get_files_and_guids()

# メインコンテンツ部分
if files:
    cols = st.columns(3)
    
    for idx, file_info in enumerate(files):
        with cols[idx % 3]:
            # Vから始まるボタンは "secondary" タイプ、それ以外は "primary" タイプを使用
            button_type = "primary" if file_info['button_name'].startswith('V') else "secondary"
            
            if display_mode == "Download":
                if st.button(
                    file_info['button_name'],
                    help=file_info['name'],
                    use_container_width=True,
                    type=button_type
                ):
                    with st.spinner('ダウンロード中...'):
                        file_path = download_file(file_info)
                        if file_path:
                            st.success(f"ダウンロード完了: {os.path.basename(file_path)}")
            else:
                url = create_excel_url(f"{BASE_URL}{file_info['server_relative_url']}") if display_mode == "Excelで開く" else create_browser_url(file_info, guid_map[file_info['server_relative_url']])
                
                if st.button(
                    file_info['button_name'],
                    help=file_info['name'],
                    use_container_width=True,
                    type=button_type
                ):
                    webbrowser.open(url)

# フッター
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>© 2024 Amazon.com, Inc.</div>", unsafe_allow_html=True)
