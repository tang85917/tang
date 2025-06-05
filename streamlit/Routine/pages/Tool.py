from pathlib import Path
import streamlit as st
import shutil
import os
import glob
import subprocess
import win32file
import webbrowser

# Streamlitのページ設定
st.set_page_config(page_title="Tool Launcher", page_icon="🚀")

image_path = Path('image')

with st.sidebar:
    st.markdown("### 👜 MTG Board")
    if st.button('MTG Board'):
        webbrowser.open_new_tab('https://quip-amazon.com/FbKrAqwaMDpb/MTG-Board')

    st.markdown("### 🎎 TRAIL")
    if st.button('TRAIL'):
        webbrowser.open_new_tab('https://share.amazon.com/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc=%7b27892F50-51B8-4022-9FF1-140B43197418%7d&file=Tool_TRAIL.xlsx&action=default')

# パスの設定
midway_dir = Path(r"W:\Shared With Me\JP_Centralops\CO_ORM\02_Tool\MidwayWorkdocs")
disaster_dir = Path(r"W:\Shared With Me\JP_Centralops\CO_ORM\02_Tool\災害Workdocks")
work_record_dir = Path(r"W:\Shared With Me\JP_Centralops\CO_ORM\06_Project\就業実績")
monitoring_dir = Path(r"W:\Shared With Me\JP_Centralops\CO_ORM\02_Tool\Monitoring")
panorama_dir = Path(r"W:\Shared With Me\JP_Centralops\CO_ORM\02_Tool\Panorama")
dest_dir = Path.home() / "Documents" / "作業ファイル"
work_record_dest_dir = Path.home() / "Documents" / "TimeAlert" / "就業実績"
work_record_dest_dir.mkdir(parents=True, exist_ok=True)
dest_dir.mkdir(parents=True, exist_ok=True)

# ファイル操作の最適化関数
def fast_copy(src, dst):
    """Windows APIを使用した高速ファイルコピー"""
    BUFFER_SIZE = 1024 * 1024  # 1MB buffer
    
    try:
        # ファイルハンドルを取得
        h_src = win32file.CreateFile(str(src),
                                   win32file.GENERIC_READ,
                                   0,
                                   None,
                                   win32file.OPEN_EXISTING,
                                   win32file.FILE_FLAG_SEQUENTIAL_SCAN,
                                   None)
        
        h_dst = win32file.CreateFile(str(dst),
                                   win32file.GENERIC_WRITE,
                                   0,
                                   None,
                                   win32file.CREATE_ALWAYS,
                                   win32file.FILE_FLAG_SEQUENTIAL_SCAN,
                                   None)

        while True:
            # 読み込みと書き込み
            err, buffer = win32file.ReadFile(h_src, BUFFER_SIZE)
            if not buffer:
                break
            win32file.WriteFile(h_dst, buffer)
            
        # ハンドルを閉じる
        win32file.CloseHandle(h_src)
        win32file.CloseHandle(h_dst)
        return True
    except:
        return False

def fast_folder_copy(src, dst):
    """高速フォルダコピー"""
    try:
        # Windows の xcopy コマンドを使用してフォルダをコピー
        subprocess.run(['xcopy', str(src), str(dst), '/E', '/I', '/H', '/Y'], 
                      check=True, 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        print(f"フォルダコピーエラー: {e}")
        # エラーが発生した場合は shutil.copytree を使用
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
        except Exception as e2:
            print(f"代替コピーエラー: {e2}")
            return False

def get_latest_file_or_folder(directory, prefix):
    """ファイルまたはフォルダを検索"""
    try:
        # プレフィックスに一致するすべてのファイルとフォルダを検索
        pattern = str(Path(directory) / f"{prefix}*")
        all_items = glob.glob(pattern)
        
        # アイテムが見つからない場合
        if not all_items:
            return None
        
        # Rescue待機DP抽出の場合は、Shinkaを含まないファイルのみをフィルタリング
        if prefix == 'Rescue待機DP抽出':
            filtered_items = [item for item in all_items if 'Shinka' not in item]
            if filtered_items:
                return max(filtered_items, key=os.path.getctime)
        
        # その他のファイルは通常通り最新のものを返す
        return max(all_items, key=os.path.getctime)
    except Exception as e:
        print(f"ファイル/フォルダ検索エラー: {e}")
        return None

def open_file_separately_fast(file_path):
    """ファイルを開く"""
    try:
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.xlsm', '.xlsx']:
            subprocess.Popen(['start', 'excel', '/x', str(file_path)], shell=True)
        elif file_ext == '.exe':
            subprocess.Popen([str(file_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(['start', '', str(file_path)], shell=True)
    except Exception as e:
        st.error(f"ファイルを開く際にエラーが発生しました: {e}")


# ツールファイルの情報を辞書で管理
tool_files = {
    'Two_Beat': {'path': 'Two_Beat', 'action': 'copy_to_subfolder', 'dest': dest_dir, 'dir': midway_dir},
    'Session': {'path': 'セッション切断', 'action': 'copy', 'dest': dest_dir, 'dir': midway_dir},
    'RP_DP': {'path': 'Rescue待機DP抽出', 'action': 'copy', 'dest': dest_dir, 'dir': midway_dir},
    'Pastel': {'path': 'Pastel_P', 'action': 'copy', 'dest': dest_dir, 'dir': midway_dir},
    'MC': {'path': 'MissionControl', 'action': 'copy', 'dest': dest_dir, 'dir': midway_dir},
    'Flash': {'path': 'Flash Master', 'action': 'copy', 'dest': dest_dir, 'dir': midway_dir},
    'Duplo': {'path': 'Duplo', 'action': 'copy_folder', 'dest': dest_dir, 'dir': midway_dir},
    'Four_seasons': {'path': 'Tool_Four seasons', 'action': 'direct_open', 'dir': disaster_dir},
    'Weather': {'path': 'WeatherOffset_AmflexOnly', 'action': 'copy', 'dest': dest_dir, 'dir': disaster_dir},
    'Disaster': {'path': '災害CSV出力', 'action': 'copy_to_subfolder', 'dest': dest_dir, 'dir': disaster_dir},
    'Work_Record': {'path': '就業実績入力用', 'action': 'copy', 'dest': work_record_dest_dir, 'dir': work_record_dir},
    'Trouble': {'path': 'Tool_トラブル報告Check', 'action': 'copy', 'dest': dest_dir, 'dir': monitoring_dir},
    'Vista_Check': {'path': 'Vista_Check', 'action': 'copy', 'dest': dest_dir, 'dir': panorama_dir}
}

def handle_tool_fast(tool_name):
    try:
        tool_info = tool_files[tool_name]
        source_dir = tool_info['dir']
        file_prefix = tool_info['path']
        action = tool_info['action']
        dest_dir_path = Path(tool_info.get('dest', dest_dir))

        # 最新のファイルまたはフォルダを取得
        source_path = get_latest_file_or_folder(source_dir, file_prefix)
        if not source_path:
            st.error(f"{tool_name}のファイル/フォルダが見つかりません。")
            return

        source_path = Path(source_path)

        if action == 'copy_to_subfolder':
            subfolder_name = tool_name
            dest_subfolder = dest_dir_path / subfolder_name
            dest_subfolder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_subfolder / source_path.name
        else:
            dest_path = dest_dir_path / source_path.name

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if action == 'direct_open':
            open_file_separately_fast(source_path)
            st.success(f"{tool_name}を開きました。")
            
        elif action == 'copy_folder':
            try:
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                if fast_folder_copy(source_path, dest_path):
                    open_file_separately_fast(dest_path)
                    st.success(f"{tool_name}フォルダをコピーしました。")
                else:
                    st.error(f"{tool_name}フォルダのコピーに失敗しました。")
            except Exception as e:
                st.error(f"フォルダコピー中にエラーが発生しました: {e}")
            
        elif action in ['copy', 'copy_to_subfolder']:
            if dest_path.exists():
                os.remove(dest_path)
            fast_copy(source_path, dest_path)
            open_file_separately_fast(dest_path)
            st.success(f"{tool_name}をコピーして開きました。")

    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")

tool_emojis = {
    'Two_Beat': '📊',  # グラフ
    'Session': '🔄',   # リフレッシュ
    'RP_DP': '📋',    # クリップボード
    'Pastel': '🎨',   # パレット
    'MC': '🎮',       # ゲームコントローラー
    'Flash': '⚡',    # 稲妻
    'Duplo': '📁',    # フォルダ
    'Four_seasons': '🌸', # 花
    'Weather': '🌦️',   # 天気
    'Disaster': '🚨',  # 警報
    'Work_Record': '📝', # メモ
    'Trouble': '⚠️',   # 警告
    'Vista_Check': '🔍' # 虫眼鏡
}

st.title('🛠️ Tool Launcher')
st.markdown("### :blue[*🎢よく使うツール！👻*]")
st.image(image_path / "1.gif")
# ツールのカテゴリー分け
download_tools = ['Two_Beat', 'Session', 'RP_DP', 'Pastel', 'MC', 'Flash', 'Duplo']
disaster_tools = ['Weather', 'Disaster']
work_record_tools = ['Work_Record']
monitoring_tools = ['Trouble', 'Vista_Check']
direct_tools = ['Four_seasons']

# すべてのツールを結合
all_tools = download_tools + disaster_tools + work_record_tools + monitoring_tools + direct_tools

# 3列でボタンを配置
cols = st.columns(3)
for i, tool_name in enumerate(all_tools):
    with cols[i % 3]:
        if st.button(f"{tool_emojis[tool_name]} {tool_name}", key=f"btn_{tool_name}"):
            handle_tool_fast(tool_name)
st.write("👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺👺")
st.write("-------------------------------------------------------------------")
st.write("👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹👹")

st.markdown("### :green[*🎭よく使うサイト！🎡*]")
st.image(image_path / "1.gif")

# リンク辞書の定義
LINKS = {
    "トラブル報告": {
        "トラブル報告L1": "https://issues.amazon.com/issues/search?q=status%3A(Open)+containingFolder%3A(d5cb84ef-fcc1-4156-b41d-3e6e9b085526)+(On-road)+(Amazon+AND+Flex+AND+DP%3F+AND+%22%3A%22+AND+Yes)+(ChannelTypePhone)&sort=createDate+desc&selectedDocument=616e77b5-5d61-4cb3-aaa1-d9f75d5519ca",
        "トラブル報告L2": "https://t.corp.amazon.com/issues?q=%7B%22AND%22%3A%7B%22status%22%3A%7B%22OR%22%3A%5B%22Assigned%22%2C%7B%22OR%22%3A%5B%22Work%20In%20Progress%22%2C%7B%22OR%22%3A%5B%22Researching%22%2C%7B%22OR%22%3A%5B%22Pending%22%2C%7B%22OR%22%3A%5B%22Resolved%22%2C%22Closed%22%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%2C%22AND%22%3A%7B%22severity%22%3A%7B%22OR%22%3A%5B%221%22%2C%7B%22OR%22%3A%5B%222%22%2C%7B%22OR%22%3A%5B%222.5%22%2C%7B%22OR%22%3A%5B%223%22%2C%7B%22OR%22%3A%5B%224%22%2C%7B%22OR%22%3A%5B%225%22%2C%22N%22%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%2C%22AND%22%3A%7B%22assignedGroup%22%3A%22Advocacy%20Operations%22%2C%22AND%22%3A%7B%22category%22%3A%22Flex%22%2C%22AND%22%3A%7B%22type%22%3A%22Advocacy%20Operations%22%2C%22AND%22%3A%7B%22item%22%3A%22LC%20-%20JP%22%2C%22NOT%22%3A%7B%22createDate%22%3A%7B%22amount%22%3A-7%2C%22unit%22%3A%22day%22%7D%2C%22keyword%22%3A%22(E-mail)%22%7D%7D%7D%7D%7D%7D%7D%7D",
        "トラブル報告S1": "https://t.corp.amazon.com/issues?q=extensions.tt.status%3A%28Assigned%20OR%20%22Work%20In%20Progress%22%20OR%20Researching%20OR%20Pending%20OR%20Resolved%20OR%20Closed%29%20AND%20currentSeverity%3A%281%20OR%202%20OR%203%20OR%204%20OR%205%20OR%202.5%20OR%20N%29%20AND%20full_text%3A%28AMZL%20Flex%20Escalations%20Form%20%20%20JP%29%20AND%20createDate%3A%5BNOW%2FDAY-1DAY%20TO%20NOW%2FDAY%2B1DAY%5D",
        "トラブル報告S2": "https://issues.amazon.com/issues/search?q=containingFolder%3A(6446699e-1784-43d9-bf9f-96d9a82111d6)+title%3A(Escalations+AND+Shinka+AND+AMZL)+createDate%3A(%5BNOW-1DAYS..NOW%5D)&sort=lastUpdatedDate+desc&selectedDocument=1f03e7eb-d64c-4a86-b6ca-ab3ff92f899c"
    },
    "CRC": {
        "CRC進捗管理": "https://share.amazon.com/sites/COJP_ORM_public/_layouts/15/WopiFrame2.aspx?sourcedoc=%7b9744702F-807E-4A13-A763-784C971E1601%7d&file=CRC_NewsFeed%20A.xlsm&action=default",
        "AmFlex": "https://issues.amazon.com/issues/search?q=status%3A(Open)+containingFolder%3A(99b6b6ce-9cfb-48f9-ac93-ed7994eb9882)&sort=lastUpdatedDate+desc&selectedDocument=a1c08241-7f04-4c57-842a-82451945cc84",
        "DSP": "https://issues.amazon.com/issues/search?q=status%3A(Open)+containingFolder%3A(60f1db42-9e17-4d13-997c-ea6a8d5d7a18)&sort=lastUpdatedDate+desc&selectedDocument=a473b384-22f1-45da-99ac-0da7d80ddeb9",
        "Msg_Tracker": "https://share.amazon.com/sites/COJP/_layouts/15/WopiFrame2.aspx?sourcedoc=%7b07727590-1282-4C57-98EA-6B78CB13D6E7%7d&file=Message_Tracker_2025.xlsx&action=default"
    },
    "RP": {
        "Chat_template": "https://quip-amazon.com/Ko7wA1fp1BnT/Rescue-Planner-Chat#temp:C:KcN15a725c832614697adfd80cec",
        "Connect": "https://japancentralops.my.connect.aws/home",
        "SayMyName": "https://saymyname.tools.amazon.dev/practice.html?language=ja-JP&name=&voice=Tomoko",
        "Cortex": "https://logistics.amazon.co.jp/internal/operations/execution/dv/routes?provider=ALL_DRIVERS",
        "Annex": "https://start.wwops.amazon.dev/boards/browse?boardId=IjIxMjQ0Ig==&businessUnitId=IjMi&selectedTagValueIds=WyIxNzMwIiwiMjk3OCIsIjI5ODMiXQ==&topLevelFilters=eyI0IjoiNzgiLCI2IjoiMTEwIn0=#21244"
    },
    "SOP": { 
        "RP SOP": "https://share.amazon.com/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc={0EFCCEC6-39CC-473F-AC39-6A8A2BB2859E}&file=SOP_RP.xlsm&action=default",
        "トラブル報告 SOP": "https://share.amazon.com/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc=%7b3E247940-064A-4437-88EB-81B74E645462%7d&file=SOP_%E3%83%88%E3%83%A9%E3%83%96%E3%83%AB%E5%A0%B1%E5%91%8A.xlsx&action=default",
        "CRC SOP": "https://share.amazon.com/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc=%7bC3458D8D-78AE-450C-8266-79F04433F63E%7d&file=CRC_%E7%81%BD%E5%AE3%E7%B7%8F%E5%90%88SOP.xlsm&action=default",
        "Panorama SOP": "https://share.amazon.com/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc=%7bE9B8794C-2936-4070-8833-5B226ECCAB92%7d&file=SOP_Panorama.xlsm&action=default",
        "D-0 SOP": "https://share.amazon.com/sites/COJP/_layouts/15/WopiFrame2.aspx?sourcedoc=%7B2ECA225F-70E9-4399-8D21-113F5CD0F470%7D&file=SOP_D-0%20Over%20Route%20Risk%20Reduction_%E5%85%B1%E6%9C%89.xlsx&action=default"
    }
}

# セクションアイコンの定義
SECTION_ICONS = {
    "トラブル報告": "📋",
    "CRC": "📊",
    "RP": "🛠️",
    "SOP": "📚"
}

def open_links(links):
    """指定されたリンクを全て開く"""
    for url in links.values():
        webbrowser.open_new_tab(url)

def create_link_sections():
    for section, links in LINKS.items():
        # セクションヘッダー
        st.markdown(f"### {SECTION_ICONS[section]} {section}")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        # リンクを2列に分割
        links_list = list(links.items())
        mid_point = (len(links_list) + 1) // 2
        
        # 左列のリンク
        with col1:
            for name, url in links_list[:mid_point]:
                st.link_button(name, url)
        
        # 右列のリンク
        with col2:
            for name, url in links_list[mid_point:]:
                st.link_button(name, url)
        
        # 全て開くボタン
        if st.button(f"🔄 全ての{section}リンクを開く", key=f"open_all_{section}"):
            open_links(links)
        
        # セクション区切り線
        st.markdown("---")

# メインコンテンツの表示
create_link_sections()

# JavaScript用のコンポーネントを追加
st.markdown("""
<script>
function openAllLinks(urls) {
    urls.forEach(url => {
        window.open(url, '_blank');
    });
}
</script>
""", unsafe_allow_html=True)