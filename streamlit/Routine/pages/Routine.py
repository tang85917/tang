import pandas as pd
import os
from pathlib import Path
import glob
import streamlit as st
from annotated_text import annotated_text
from datetime import datetime
import re
import pyperclip
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import warnings
import time
import sqlite3
from contextlib import contextmanager
warnings.filterwarnings('ignore')

st.set_page_config(page_title="RoutineTask", page_icon="📋")

# --- ディレクトリとデータベース設定 ---
DATA_DIR = Path("data")
SESSION_DIR = Path("Session")
DB_PATH = SESSION_DIR / "session.db"

# フォルダ作成
DATA_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)

# データベース関連の関数
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_data
            (key TEXT PRIMARY KEY, value TEXT)
        ''')
        conn.commit()

def load_session():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM session_data')
            return dict(cursor.fetchall())
    except Exception as e:
        st.error(f"セッション読み込みエラー: {str(e)}")
        return {}

def save_session(session_dict):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for key, value in session_dict.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO session_data (key, value)
                    VALUES (?, ?)
                ''', (key, str(value)))
            conn.commit()
    except Exception as e:
        st.error(f"セッション保存エラー: {str(e)}")

# データベース初期化
init_db()

def download_latest_routine_board():
    """SharePointから最新のRoutine Boardをダウンロード"""
    try:
        session = requests.Session()
        auth = HttpNegotiateAuth()
        file_url = "https://share.amazon.com/sites/COJP_ORM/Shared%20Documents/02_Tool/Routine%20Board/Tool_Routine%20Board.xlsm"
        
        st.write("ファイルをダウンロード中...")
        response = session.get(file_url, auth=auth, verify=False)

        if response.status_code != 200:
            st.error(f"ファイルのダウンロードに失敗: {response.status_code}")
            st.write(f"Response: {response.text}")
            return False

        temp_path = DATA_DIR / "temp.xlsm"
        with open(temp_path, 'wb') as f:
            f.write(response.content)

        try:
            df = pd.read_excel(temp_path, sheet_name='Routine Board', header=1)
            csv_path = DATA_DIR / f"Routine_Board.csv"
            df.to_csv(csv_path, encoding='utf-8-sig', index=False)
            temp_path.unlink()
            time.sleep(1)
            st.success("Routine Boardをダウンロードしました")
            return True
        except Exception as e:
            st.error(f"Excel変換エラー: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            return False

    except Exception as e:
        st.error(f"ダウンロードエラー: {str(e)}")
        st.write("エラーの詳細:", str(e))
        if temp_path.exists():
            temp_path.unlink()
        return False

# セッションデータ初期化
session_data = load_session()

if 'task_states' not in st.session_state:
    st.session_state.task_states = {}
if 'Routine_radio' not in st.session_state:
    st.session_state.Routine_radio = session_data.get('Routine_radio')
if 'color_set' not in st.session_state:
    st.session_state.color_set = session_data.get('color_set', 'purple')  # デフォルトカラー

# サイドバー
with st.sidebar:
    if st.button("🔄 最新のRoutine Boardをダウンロード"):
        if download_latest_routine_board():
            time.sleep(2)
            st.rerun()

    display_mode = st.radio(
        "表示方式を選択",
        ["個別表示", "全体表示"],
        key="display_mode"
    )

    # 色の選択と保存（連続変更可能に修正）
    colors = ["red", "blue", "green", "black", "orange", "purple", "pink", 
             "brown", "cyan", "lime", "yellow", "teal", "indigo", "violet", "white"]
    
    previous_color = st.session_state.get('color_set', 'purple')
    new_color = st.selectbox(
        "色を選んでください",
        colors,
        index=colors.index(previous_color)
    )
    
    # 色が変更された場合のみ保存
    if new_color != previous_color:
        st.session_state.color_set = new_color
        session_data['color_set'] = new_color
        save_session(session_data)
        st.rerun()  # 色変更を即時反映

    st.write("---")

    # リセットボタン（カラー設定以外をリセット）
    if st.button("♻️リセット", key="reset_button"):
        # 現在の色設定を保存
        current_color = session_data.get('color_set', 'purple')
        
        # セッションをリセット
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM session_data WHERE key != "color_set"')
            conn.commit()
        
        # Streamlitのセッション状態をクリア（色設定以外）
        for key in list(st.session_state.keys()):
            if key != 'color_set':
                del st.session_state[key]
        
        st.success("セッションデータをリセットしました！")
        st.rerun()

    st.write("📂 最終更新: " + datetime.now().strftime('%H:%M:%S'))

# メイン画面
st.title('🚚Routine Board🎄')

# 当日の最新ファイルを探す
today = datetime.now().date()
files = [(f, datetime.fromtimestamp(os.path.getmtime(f)).date())
         for f in glob.glob(str(DATA_DIR / "Routine_Board.csv"))]

today_files = [f for f, d in files if d == today]

if today_files:
    latest_file = max(today_files, key=os.path.getmtime)
    try:
        if not os.path.exists(latest_file):
            st.error("ファイルが見つかりません。再度ダウンロードしてください。")
            st.stop()

        df = pd.read_csv(latest_file)
        
        if df.empty:
            st.error("データが正しく読み込めませんでした。再度ダウンロードしてください。")
            st.stop()
            
        df_routine = df.loc[:, ~df.columns.str.startswith(('Unnamed', 'Ver', 'Time'))].copy()
        df_time = pd.DataFrame({'Time': df['Unnamed: 2']})
        temp_index = df_time['Time'].replace('”', None).ffill()
        routines = df_routine.columns.tolist()

        if st.session_state.display_mode == "全体表示":
            display_df = df_routine.copy()
            
            # 時間インデックスの処理
            cleaned_index = temp_index.apply(lambda x: str(x)[:5] if pd.notna(x) else '')  # 秒表示を削除
            cleaned_index = cleaned_index.apply(lambda x: '' if len(str(x).strip()) <= 3 else x)  # 3文字以下を空欄に
            
            display_df.index = pd.Index(cleaned_index)
            display_df = display_df.replace({None: '', "None": ''})
            
            def all_routine(df: pd.DataFrame) -> pd.DataFrame:
                keywords = ('Lunch', 'Break')
                for col_idx, col in enumerate(df.columns):
                    col_data = df[col].tolist()
                    for i, data in enumerate(col_data):
                        if isinstance(data, str) and any(keyword in data for keyword in keywords):
                            data = re.sub(r'15min', '0.25h', data)
                            data = re.sub(r'30min', '0.5h', data)
                            time = re.findall(r'\d+(?:\.\d+)?', data)
                            if time:
                                time_value = float(time[0])
                                if time_value <= 2:
                                    steps = int(time_value / 0.25)
                                    for offset in range(1, steps):
                                        if i + offset < len(df):
                                            df.iat[i + offset, col_idx] = data.split('_')[0]
                return df

            display_df = all_routine(display_df)
            st.dataframe(display_df, use_container_width=True, height=900)
      
        else:  # 個別表示モード
            if routines:
                selected_routine = st.radio(
                    'Routineを選択してください',
                    options=routines,
                    horizontal=True,
                    key='Routine_radio'
                )

                session_data['Routine_radio'] = st.session_state.Routine_radio
                save_session(session_data)

                if st.session_state.Routine_radio:
                    routine_data = df_routine[st.session_state.Routine_radio].dropna()
                    my_routine = pd.merge(temp_index, routine_data, left_index=True, right_index=True, how='right')

                    try:
                        chime_rows = my_routine[my_routine.iloc[:, 1].str.contains("・Chime挨拶", na=False)]
                        if not chime_rows.empty and chime_rows.iloc[:, 1].notna().any():
                            node_texts = chime_rows.iloc[:, 1].dropna().str.split('・').str[0].tolist()
                            raw_nodes = re.findall(r'\w+(?:,\w+)*', ' '.join(node_texts))

                            nodes_with_comma = [n for n in raw_nodes if ',' in n]
                            nodes_without_comma = [n for n in raw_nodes if ',' not in n]

                            flattened = []
                            for entry in nodes_with_comma:
                                parts = entry.split(',')
                                prefix = parts[0][:3]
                                flattened.extend([prefix + p if i != 0 else p for i, p in enumerate(parts)])

                            final_nodes = pd.Series(flattened + nodes_without_comma)
                        else:
                            final_nodes = pd.Series([])

                    except Exception as e:
                        st.warning(f"Node処理中にエラーが発生しました: {e}")
                        final_nodes = pd.Series([])

                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        if st.button("🎃NodeCopy", key="Node_Copy"):
                            copied_text = "\n".join(final_nodes.astype(str))
                            pyperclip.copy(copied_text)
                            st.success("担当Nodeをコピーしました")

                    with col1_2:
                        show_nodes = st.checkbox('🔍担当Nodeを表示', key=f'{st.session_state.Routine_radio}_show_nodes')

                    task_counter = 0
                    for i, row in enumerate(routine_data):
                        content = row
                        time_to_show = temp_index.iloc[routine_data.index[i]]

                        if pd.isna(time_to_show) or (
                            isinstance(time_to_show, str) and
                            time_to_show.strip().startswith(('13', '14')) and
                            len(time_to_show.strip()) <= 3 and 
                            time_to_show.strip()[2].isalpha()
                        ):
                            if show_nodes and not pd.isna(content):
                                st.markdown(f':red[👾{content}]')
                        else:
                            if any(word in str(content) for word in ['Lunch', 'Break']):
                                time_str = str(time_to_show)[:5] if isinstance(time_to_show, str) else time_to_show.strftime('%H:%M')
                                st.markdown(f"##  *{time_str} ☕ {content}*")
                            else:
                                task_counter += 1
                                col1, col2 = st.columns([0.03, 0.97])
                                checkbox_key = f"{st.session_state.Routine_radio}_{task_counter}_{str(time_to_show).replace(':', '_')}"

                                with col1:
                                    checked = session_data.get(checkbox_key, 'False') == 'True'
                                    task_done = st.checkbox("完了", key=checkbox_key, value=checked, label_visibility="collapsed")
                                    session_data[checkbox_key] = str(task_done)

                                with col2:
                                    col2_1, col2_2 = st.columns([0.03, 0.97])
                                    with col2_1:
                                        st.write("🕐")
                                    with col2_2:
                                        time_display = str(time_to_show)[:5] if isinstance(time_to_show, str) else time_to_show.strftime('%H:%M')
                                        annotated_text(
                                            (time_display, None, "#808080"),
                                            (f"{content}", "タスク", "#808080" if task_done else st.session_state.color_set)
                                        )

                    save_session(session_data)

    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        st.write("ファイルパス:", latest_file)
        st.write("エラーの詳細:", str(e))
        st.stop()
else:
    st.warning("最新のRoutine Boardをダウンロードしてください")
