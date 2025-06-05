import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import urllib3
import os

# SSL証明書の警告を無視
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Shift", page_icon="📅")

with st.sidebar:
    st.markdown("### 🔄 シフト更新")
    
    if st.button("Shift_Download"):
        try:
            # ダウンロード先のディレクトリ
            download_dir = Path(r'data')
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # SharePointのファイルパスとURL設定
            folder_path = '/sites/COJP/Shared Documents/Shift/ORM'
            file_name = 'Shift_STCO.xlsx'
            file_url = f"https://share.amazon.com/sites/COJP/_api/web/GetFileByServerRelativeUrl('{folder_path}/{file_name}')/$value"
            
            # セッション設定
            session = requests.Session()
            auth = HttpNegotiateAuth()
            headers = {
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose',
                'User-Agent': 'Python NTLM Client'
            }
            
            # ファイルダウンロード
            st.info("ファイルをダウンロード中...")
            response = session.get(
                file_url,
                auth=auth,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                file_path = download_dir / file_name
                try:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    st.success("ファイルを更新しました")
                    st.rerun()
                except PermissionError:
                    st.error("ファイルが使用中です。Excel を閉じてから再度お試しください。")
            else:
                st.error(f"ダウンロードに失敗しました。ステータスコード: {response.status_code}")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    st.markdown("### 👓 シフト確認")
    st.link_button('SharePoint', 'https://share.amazon.com/sites/COJP/_layouts/15/WopiFrame2.aspx?sourcedoc=%7b7350860C-98D7-470D-9DED-1808426202B6%7d&file=Shift_STCO.xlsx&action=default')

    st.markdown("### 📊 表示切替")
    view_mode = st.radio(
        "",
        ["個人", "全員"],
        horizontal=True
    )

def create_calendar_view(my_shift, month):
    first_day = my_shift.iloc[0, 0].weekday()
    
    calendar = pd.DataFrame(columns=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    calendar = calendar.fillna('')

    week = 0
    day_pos = first_day
    current_week = [''] * 7
    has_data_in_week = False

    for col in range(len(my_shift.columns)):
        day = my_shift.iloc[0, col]
        shift = my_shift.iloc[1, col]
        
        if pd.notna(day) and pd.notna(shift):
            # 日付とシフトを組み合わせて表示
            current_week[day_pos] = f"{day.day}日 / {shift}"
            has_data_in_week = True
        
        day_pos += 1
        if day_pos > 6:
            if has_data_in_week:
                calendar.loc[week] = current_week
                week += 1
            current_week = [''] * 7
            has_data_in_week = False
            day_pos = 0

    if has_data_in_week:
        calendar.loc[week] = current_week

    st.markdown(f"### :violet[📅{month.strftime('%Y年%m月')}シフト]")
    
    def style_cells(df):
        return pd.DataFrame([
            [
                'height: 60px; text-align: center; vertical-align: middle; color: red; font-weight: bold;' if '8' in str(val).split('/')[-1].strip()
                else 'height: 60px; text-align: center; vertical-align: middle; color: #00bfff; font-weight: bold;' if '6' in str(val).split('/')[-1].strip()
                else 'height: 60px; text-align: center; vertical-align: middle; color: #ffd700; font-weight: bold;' if '14' in str(val).split('/')[-1].strip()
                else 'background-color: #90caf9; height: 60px; text-align: center; vertical-align: middle;' if any(x in str(val).upper() for x in ['OFF', 'PAID', 'PL'])
                else 'height: 60px; text-align: center; vertical-align: middle;'
                for val in row
            ]
            for _, row in df.iterrows()
        ], index=df.index, columns=df.columns)
    
    st.dataframe(
        calendar.style.apply(style_cells, axis=None),
        use_container_width=True,
        hide_index=True
    )

# メイン処理
st.title('Home')

user_name = os.getenv('USERNAME')
current_date = datetime.now()
current_month = current_date.strftime("%B")

next_month_date = current_date + relativedelta(months=1)
next_month = next_month_date.strftime("%B")

file_path = Path(r'data/Shift_STCO.xlsx')

if view_mode == "個人":
    try:
        # Excel fileを読み込み
        df = pd.read_excel(file_path, sheet_name=current_month)
        
        # user_nameの行を見つける
        user_row_index = df[df.iloc[:, 2] == user_name].index[0] if any(df.iloc[:, 2] == user_name) else None
        
        # 見つかった場合、col2の値をcol1に上書き
        if user_row_index is not None:
            df.iloc[user_row_index, 1] = df.iloc[user_row_index, 2]
        
        # 以降の処理のためにindex_col=1でデータフレームを再構築
        df_this_month = df.set_index(df.columns[1])
        dates_this_month = df_this_month.iloc[3]
        
        # ユーザー一覧を取得して不要なものを除外
        users = df_this_month.index.tolist()
        excluded_terms = ['Wk#', 'Total', 'train', 'LS', 'Associate', 'Manager']
        users = [user for user in users 
                if isinstance(user, str) 
                and not any(term.lower() in user.lower() for term in excluded_terms)
                and not user[0].isdigit()]
        
        # user_nameを最初に持ってくる
        if user_name in users:
            users.remove(user_name)
            users.insert(0, user_name)
        
        if st.checkbox("👥 メンバー選択", value=False):  # デフォルトは閉じた状態
            selected_user = st.radio(
                "",
                users,
                index=0,
                horizontal=True
            )
        else:
            selected_user = user_name if user_name in users else users[0]

        # 選択されたユーザーのシフトを取得
        name_this_month = df_this_month.loc[selected_user]

        my_shift_this_month = pd.DataFrame([dates_this_month, name_this_month]).iloc[:, 9:40]
        my_shift_this_month.iloc[0] = pd.to_datetime(my_shift_this_month.iloc[0])
        
        create_calendar_view(my_shift_this_month, current_date)
    except Exception as e:
        st.write(f"今月のシフトデータはまだ登録されていません")

    # 次の月のシフト表示も同様に処理
    try:
        # Excel fileを読み込み
        df = pd.read_excel(file_path, sheet_name=next_month)
        
        # user_nameの行を見つける
        user_row_index = df[df.iloc[:, 2] == user_name].index[0] if any(df.iloc[:, 2] == user_name) else None
        
        # 見つかった場合、col2の値をcol1に上書き
        if user_row_index is not None:
            df.iloc[user_row_index, 1] = df.iloc[user_row_index, 2]
        
        # 以降の処理のためにindex_col=1でデータフレームを再構築
        df_next_month = df.set_index(df.columns[1])
        dates_next_month = df_next_month.iloc[3]
        name_next_month = df_next_month.loc[selected_user]

        my_shift_next_month = pd.DataFrame([dates_next_month, name_next_month]).iloc[:, 9:40]
        my_shift_next_month.iloc[0] = pd.to_datetime(my_shift_next_month.iloc[0])
        
        create_calendar_view(my_shift_next_month, next_month_date)
    except Exception as e:
        st.write(f"来月のシフトデータはまだ登録されていません")

else:  # 全員シフト表示
    try:
        # 今月のシフト
        df_this_month = pd.read_excel(file_path, sheet_name=current_month, index_col=2)
        
        # 不要な行を削除
        df_this_month = df_this_month.iloc[4:]  # ヘッダー行を除外
        
        # 数字で始まる行とWk#, Total, trainを含む行を除外
        df_this_month = df_this_month[
            df_this_month.index.map(lambda x: isinstance(x, str) and 
                                  not x[0].isdigit() and 
                                  not any(term.lower() in str(x).lower() 
                                        for term in ['Wk#', 'Total', 'train']))
        ]

        st.markdown(f"### :violet[📅{current_date.strftime('%Y年%m月')}シフト]")
        
        # シフトデータの列名を日付に変更
        shift_data = df_this_month.iloc[:, 9:40].copy()  # .copy()を追加
        shift_data.columns = [f"{i+1}日" for i in range(len(shift_data.columns))]
        
        # インデックスにTeam名を設定
        shift_data = shift_data.set_index(df_this_month.iloc[:, 1])
        
        st.dataframe(
            shift_data,
            height=600
        )

        # 来月のシフト
        st.markdown(f"### :violet[📅{next_month_date.strftime('%Y年%m月')}シフト]")
        
        df_next_month = pd.read_excel(file_path, sheet_name=next_month, index_col=2)
        df_next_month = df_next_month.iloc[4:]
        df_next_month = df_next_month[
            df_next_month.index.map(lambda x: isinstance(x, str) and 
                                  not x[0].isdigit() and 
                                  not any(term.lower() in str(x).lower() 
                                        for term in ['Wk#', 'Total', 'train']))
        ]

        # 来月のシフトデータの列名を日付に変更
        shift_data_next = df_next_month.iloc[:, 9:40].copy()  # .copy()を追加
        shift_data_next.columns = [f"{i+1}日" for i in range(len(shift_data_next.columns))]
        
        # インデックスにTeam名を設定
        shift_data_next = shift_data_next.set_index(df_next_month.iloc[:, 1])
        
        st.dataframe(
            shift_data_next,
            height=600
        )

    except Exception as e:
        st.write(f"シフトデータの読み込みに失敗しました: {str(e)}")

