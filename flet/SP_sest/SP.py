import win32timezone
import subprocess
import ctypes
import sys
import flet as ft
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import urllib3
from urllib.parse import quote
import os
from pathlib import Path
from datetime import datetime
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Dict, TypedDict, Optional

# SSL証明書の警告を無視
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_dsp_info_cache: Optional[Dict[str, str]] = None
_dsp_info_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1)

VERSION = '1.0.1'

# SharePointのURL設定
BASE_URL = "https://share.amazon.com"
FOLDER_URL = "https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('/sites/COJP_ORM/Shared Documents/05_DS_Rescue/2025/RP')/Files?$select=Name,ServerRelativeUrl,UniqueId"

class FileInfo(TypedDict):
    name: str
    button_name: str
    server_relative_url: str
    guid: str

# グローバルセッションの作成
global_session = requests.Session()
setattr(global_session, 'auth', HttpNegotiateAuth())
setattr(global_session, 'verify', False)

def read_dsp_info() -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """DSP情報をSharePointから直接読み込む（非同期対応版）"""
    global _dsp_info_cache

    with _dsp_info_lock:
        if _dsp_info_cache is not None:
            return _dsp_info_cache, []  # キャッシュがある場合は空のリストを返す

    try:
        url = "https://share.amazon.com/sites/COJP_ORM/Shared%20Documents/04_Metrics/dsp_info.txt"
        response = global_session.get(url, timeout=30)
        
        if response.status_code == 200:
            import csv
            from io import StringIO
            
            station_dict: Dict[str, str] = {}
            dsp_info_list: List[Dict[str, str]] = []
            csv_data = StringIO(response.content.decode('utf-8'))
            reader = csv.DictReader(csv_data, delimiter='\t')
            
            # DSP名の変換マッピング
            dsp_name_mapping = {
                'ENSH': 'ENSHU',
                'SATT': 'LOGINET',
                'MRUK': 'MARUWA',
                'SBCL': 'SBS',
                'WKB': 'WAKABA'
            }
            
            for row in reader:
                if 'station_code' in row and 'service_area_id' in row:
                    station_code = row['station_code'].upper()
                    parent_location = row.get('parent_location', '')
                    provider_code = row.get('provider_code', '')
                    
                    # station_dict の更新
                    if station_code not in station_dict:
                        station_dict[station_code] = row['service_area_id']
                    
                    # Motherがhで始まらない場合のみリストに追加
                    if not parent_location.startswith('H'):
                        dsp_info_list.append({
                            'Mother': parent_location,
                            'Station': station_code,
                            'DSP': dsp_name_mapping.get(provider_code, provider_code)  # マッピングされていない場合は元の値を使用
                        })

            with _dsp_info_lock:
                _dsp_info_cache = station_dict
            return station_dict, dsp_info_list
            
        return {}, []
            
    except Exception as e:
        print(f"Error reading DSP info: {e}")
        return {}, []

            
    except Exception as e:
        print(f"Error reading DSP info: {e}")
        return {}, []

async def async_read_dsp_info() -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """DSP情報を非同期で読み込む"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, read_dsp_info)

def get_files_and_guids() -> Tuple[List[FileInfo], Dict[str, str]]:
    """SharePointからファイル一覧とGUIDを取得"""
    file_info: List[FileInfo] = []
    guid_map: Dict[str, str] = {}

    try:
        headers = {
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'Python NTLM Client'
        }
        
        response = global_session.get(
            FOLDER_URL,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        files = data['d']['results']
        
        for file in files:
            if file['Name'].lower().endswith(('.xlsx', '.xlsm')):
                file_info.append({
                    'name': file['Name'],
                    'button_name': file['Name'].split()[0],
                    'server_relative_url': file['ServerRelativeUrl'],
                    'guid': file['UniqueId']
                })
                guid_map[file['ServerRelativeUrl']] = file['UniqueId']

        file_info = sorted(file_info, key=lambda item: (
            (0, int(''.join(filter(str.isdigit, item['button_name']))), ''.join(filter(str.isalpha, item['button_name']))) if item['button_name'][0].isdigit()
            else (1, item['button_name']) if item['button_name'].startswith('V')
            else (2, item['button_name'])
        ))
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

    return file_info, guid_map

def download_file(file_info: FileInfo) -> str:
    """ファイルをダウンロードして保存パスを返す"""
    try:
        file_url = f"{BASE_URL}{file_info['server_relative_url']}"

        response = global_session.get(
            file_url,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            downloads_path = str(Path.home() / "Downloads")
            file_path = os.path.join(downloads_path, file_info['name'])
            
            base, ext = os.path.splitext(file_path)
            counter = 1
            while os.path.exists(file_path):
                file_path = f"{base}_{counter}{ext}"
                counter += 1
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return file_path
        
        return ""
            
    except Exception as e:
        print(f"ダウンロードエラー: {str(e)}")
        return ""

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

async def main(page: ft.Page):
    # アプリケーションの設定
    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "RP_hirakegoma"
    page.window.width = 1200
    page.window.height = 800
    page.window.maximized = False

    # 画面中央に配置
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_x = (screen_width - page.window.width) // 2
    window_y = (screen_height - page.window.height) // 2
    page.window.left = window_x
    page.window.top = window_y

    # アイコンの設定
    icon_path = resource_path("liu.ico")
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    # 時計とテーマのコンポーネントを定義
    clock_text = ft.Text(
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_400,
    )

    date_text = ft.Text(
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_200,
    )

    def toggle_theme(e):
        current_mode = page.theme_mode
        if current_mode == ft.ThemeMode.LIGHT:
            # ダークモード設定
            page.theme_mode = ft.ThemeMode.DARK
            theme_button.icon = ft.Icons.LIGHT_MODE
            theme_button.icon_color = ft.Colors.RED_800
            page.bgcolor = ft.Colors.with_opacity(0.95, ft.Colors.SHADOW)
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_PURPLE_900)
            clock_text.color = ft.Colors.RED
            date_text.color = ft.Colors.AMBER_200
        else:
            # ライトモード設定
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_button.icon = ft.Icons.DARK_MODE
            theme_button.icon_color = ft.Colors.BROWN_800
            page.bgcolor = ft.Colors.with_opacity(0.97, "#F5E6D3")
            page.theme = ft.Theme(color_scheme_seed="#D2B48C")
            clock_text.color = ft.Colors.BROWN_800
            date_text.color = ft.Colors.BROWN_700
        page.update()

    # テーマボタンの定義
    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_color=ft.Colors.BROWN_800,
        tooltip="テーマ切り替え",
        on_click=toggle_theme
    )

    header = ft.Row(
        [
            clock_text,
            ft.Container(
                content=ft.Row(  # Columnから Rowに変更
                    [
                        ft.Text(
                            "RP SharePoint Files",
                            size=38,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.BLUE,
                        ),
                        ft.Text(
                            f"Ver. {VERSION}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_400,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # 要素を両端に配置
                ),
                padding=ft.padding.all(10),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.1, color=ft.Colors.INDIGO_400),
            ),
            ft.Row(
                [date_text, theme_button],
                spacing=10
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    # ローディング画面を表示
    loading_container = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ProgressRing(
                                width=60,
                                height=60,
                                stroke_width=4,
                                color=ft.Colors.BLUE_400,
                            ),
                            ft.Text(
                                "Loading...",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_400,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    margin=ft.margin.only(bottom=20),
                ),
                ft.Text(
                    "Initializing components...",
                    color=ft.Colors.GREY_600,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.ProgressBar(
                    width=300,
                    color=ft.Colors.BLUE_200,
                    bgcolor=ft.Colors.BLUE_50,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ft.Colors.WHITE,
    )
    page.add(loading_container)
    page.update()

    # DSP情報とファイル一覧の取得
    station_dict, dsp_info_list = await async_read_dsp_info()
    files, guid_map = get_files_and_guids()

    def handle_url_open(e, input_field: ft.TextField, url_type: str):
        try:
            station_code = input_field.value if input_field.value else ""
            if not station_code:
                input_field.border_color = ft.Colors.RED_400
                input_field.update()
                return

            def open_service_url(station_code: str, url_type: str) -> bool:
                if not station_code:
                    raise ValueError("Station code cannot be empty")
                        
                try:
                    station_dict, _ = read_dsp_info()  # タプルから station_dict を取得
                    station_code = station_code.upper()
                    
                    if station_code not in station_dict:
                        raise ValueError(f"Invalid station code: {station_code}")
                        
                    service_area_id = station_dict[station_code]
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    encoded_service_area_id = quote(service_area_id)
                    
                    base_url = "https://logistics.amazon.co.jp/internal"
                    urls = {
                        'cortex': f"{base_url}/operations/execution/itineraries?provider=ALL_DRIVERS&selectedDay={today}&serviceAreaId={encoded_service_area_id}",
                        'roster': f"{base_url}/capacity/rosterview?serviceAreaId={encoded_service_area_id}&date={today}",
                        'sui': f"{base_url}/scheduling/dsps?serviceAreaId={encoded_service_area_id}&date={today}"
                    }
                    
                    target_url = urls[url_type]
                    subprocess.Popen(f'start "" "{target_url}"', 
                        shell=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW)
                    return True
                        
                except Exception as e:
                    raise ValueError(f"Error opening URL: {str(e)}")

            success = open_service_url(station_code, url_type)
            if success:
                input_field.value = ""
                input_field.border_color = ft.Colors.BLUE_400
            else:
                input_field.border_color = ft.Colors.RED_400
            input_field.update()
            
        except ValueError as error:
            input_field.border_color = ft.Colors.RED_400
            input_field.update()

    # ツールバーとdisplay_modeの作成
    def create_tool_row():
        cortex_field = ft.TextField(
            label="Cortex",
            width=200,
            height=40,
            text_align=ft.TextAlign.CENTER,
            on_submit=lambda e: handle_url_open(e, cortex_field, 'cortex'),
            suffix_icon=ft.Icons.OPEN_IN_BROWSER,
            suffix_text="DS",
            hint_text="DSPコードを入力",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_800,
            border_radius=8,
        )
        
        roster_field = ft.TextField(
            label="Roster",
            width=200,
            height=40,
            text_align=ft.TextAlign.CENTER,
            on_submit=lambda e: handle_url_open(e, roster_field, 'roster'),
            suffix_icon=ft.Icons.OPEN_IN_BROWSER,
            suffix_text="DS",
            hint_text="DSPコードを入力",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_800,
            border_radius=8,
        )
        
        sui_field = ft.TextField(
            label="SUI",
            width=200,
            height=40,
            text_align=ft.TextAlign.CENTER,
            on_submit=lambda e: handle_url_open(e, sui_field, 'sui'),
            suffix_icon=ft.Icons.OPEN_IN_BROWSER,
            suffix_text="DS",
            hint_text="DSPコードを入力",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_800,
            border_radius=8,
        )

        display_mode = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="ブラウザ", icon=ft.Icons.LANGUAGE),
                ft.Tab(text="Excel", icon=ft.Icons.TABLE_CHART),
                ft.Tab(text="ダウンロード", icon=ft.Icons.DOWNLOAD),
                ft.Tab(text="DSP情報", icon=ft.Icons.INFO),
            ],
        )

        return ft.Row(
            [
                ft.Container(
                    content=display_mode,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                    border_radius=30,
                    padding=5,
                ),
                ft.VerticalDivider(width=20),
                cortex_field,
                roster_field,
                sui_field,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        ), display_mode

    tool_row, display_mode = create_tool_row()

    def create_hover_button(text: str, tooltip: str, bgcolor: str, hover_color: str, on_click):
        button = ft.ElevatedButton(
            text=text,
            tooltip=tooltip,
            bgcolor=bgcolor,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                padding=10,
            ),
        )

        container = ft.Container(
            content=button,
            animate=ft.Animation(200, ft.AnimationCurve.BOUNCE_OUT),
            scale=1.0,
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            rotate=0
        )

        def on_hover(e):
            is_hovered = e.data == "true"
            if isinstance(button, ft.ElevatedButton):
                button.bgcolor = hover_color if is_hovered else bgcolor
                container.scale = 1.1 if is_hovered else 1.0
                container.update()

        def on_button_click(e):
            if on_click:
                on_click(e)

            container.rotate = 360
            container.update()
            
            def reset_rotation():
                time.sleep(0.3)
                container.rotate = 0
                container.update()
            
            threading.Thread(target=reset_rotation, daemon=True).start()

        button.on_hover = on_hover
        button.on_click = on_button_click

        return container

    def handle_button_click(e, file_info: FileInfo):
        if display_mode.selected_index == 0:  # ブラウザ
            url = create_browser_url(file_info, guid_map[file_info['server_relative_url']])
            subprocess.Popen(['start', '', url], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        elif display_mode.selected_index == 1:  # Excel
            url = create_excel_url(f"{BASE_URL}{file_info['server_relative_url']}")
            subprocess.Popen(['start', '', url], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # ダウンロード
            def download_async():
                progress_bar.visible = True
                page.update()
                file_path = download_file(file_info)
                progress_bar.visible = False
                page.update()
                if file_path:
                    subprocess.Popen(['start', '', file_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

            threading.Thread(target=download_async, daemon=True).start()

    def create_excel_url(web_url: str) -> str:
        return f"ms-excel:ofv|u|{web_url}"

    def create_browser_url(file_info: FileInfo, guid: str) -> str:
        encoded_filename = quote(file_info['name'])
        return f"{BASE_URL}/sites/COJP_ORM/_layouts/15/WopiFrame2.aspx?sourcedoc={{{guid}}}&file={encoded_filename}&action=default"

    # グリッドの作成
    grid = ft.GridView(
        expand=True,
        runs_count=6,
        max_extent=120,
        child_aspect_ratio=2.0,
        spacing=8,
        run_spacing=8,
        padding=15,
    )

    # ボタンの追加
    for file_info in files:
        is_v_button = file_info['button_name'].startswith('V')
        is_d_button = file_info['button_name'].startswith('D')
        
        if is_v_button:
            bgcolor = ft.Colors.GREEN_ACCENT_400
            hover_color = ft.Colors.GREEN_900
        elif is_d_button:
            bgcolor = ft.Colors.INDIGO_300
            hover_color = ft.Colors.INDIGO_900
        else:
            bgcolor = ft.Colors.DEEP_PURPLE_300
            hover_color = ft.Colors.PURPLE_900

        button = create_hover_button(
            text=file_info['button_name'],
            tooltip=file_info['name'],
            bgcolor=bgcolor,
            hover_color=hover_color,
            on_click=lambda e, f=file_info: handle_button_click(e, f)
        )
        grid.controls.append(button)

    grid_container = ft.Container(
    content=ft.Column(
        [
            ft.Container(  # スクロール可能なコンテナ
                content=grid,
                height=200,  # 固定高さを設定（必要に応じて調整）
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=10,
                padding=10,
            )
        ],
        scroll=ft.ScrollMode.AUTO,  # 必要に応じてスクロール
        expand=True,
    ),
    expand=True,
    visible=True,
)

    dsp_info_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Text("Mother", weight=ft.FontWeight.BOLD),
            ),
            ft.DataColumn(
                ft.Text("Station", weight=ft.FontWeight.BOLD),
            ),
            ft.DataColumn(
                ft.Text("DSP", weight=ft.FontWeight.BOLD),
            ),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(info['Mother']),
                        )
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(info['Station']),
                        )
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(info['DSP']),
                        )
                    ),
                ]
            )
            for info in dsp_info_list
        ],
    )


    # コンテナの作成
    grid_container = ft.Container(content=grid, visible=True)

    def create_search_box():
        search_text = ft.TextField(
            label="検索",
            hint_text="DSP Station Name",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            border_radius=10,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_800,
            text_size=16,
            height=50,
            on_change=lambda e: filter_table(e.control.value),
        )

        def filter_table(search_term: str):
            if not search_term:
                rows = [
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(info['Mother'])),
                            ft.DataCell(ft.Text(info['Station'])),
                            ft.DataCell(ft.Text(info['DSP'])),
                        ]
                    )
                    for info in dsp_info_list
                ]
                result_count.value = f"全 {len(dsp_info_list)} 件"
            else:
                search_term = search_term.lower()
                filtered_info = [
                    info for info in dsp_info_list
                    if search_term in info['Mother'].lower() or 
                       search_term in info['Station'].lower() or 
                       search_term in info['DSP'].lower()
                ]
                rows = [
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(info['Mother'])),
                            ft.DataCell(ft.Text(info['Station'])),
                            ft.DataCell(ft.Text(info['DSP'])),
                        ]
                    )
                    for info in filtered_info
                ]
                result_count.value = f"検索結果: {len(filtered_info)} 件"

            dsp_info_table.rows = rows
            page.update()

        return search_text

    # 検索結果件数表示用のテキスト
    result_count = ft.Text(f"全 {len(dsp_info_list)} 件", size=14)

    # 検索ボックスの作成
    search_box = create_search_box()

    # DSP情報テーブルの作成
    dsp_info_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Mother", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Station", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("DSP", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(info['Mother'])),
                    ft.DataCell(ft.Text(info['Station'])),
                    ft.DataCell(ft.Text(info['DSP'])),
                ]
            )
            for info in dsp_info_list
        ],
    )

    dsp_info_container = ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    ft.Text("DSP Information", size=20, weight=ft.FontWeight.BOLD),
                    result_count,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            search_box,  # 検索ボックスを追加
            ft.Container(
                content=ft.ListView(
                    controls=[dsp_info_table],
                    spacing=10,
                    padding=10,
                    height=300,
                ),
            )
        ]),
        visible=False,
    )

    # タブ切り替えのイベントハンドラー
    def on_tab_change(e):
        grid_container.visible = display_mode.selected_index != 3
        dsp_info_container.visible = display_mode.selected_index == 3
        page.update()

    display_mode.on_change = on_tab_change

    # プログレスバー
    progress_bar = ft.ProgressBar(visible=False)

    # メインコンテンツの作成
    main_content = ft.Container(
        content=ft.Column(
            [
                header,
                tool_row,
                progress_bar,
                ft.Divider(),
                grid_container,
                dsp_info_container,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        ),
        animate=ft.Animation(duration=500, curve=ft.AnimationCurve.EASE_OUT),
        opacity=0,
    )

    # 画面の初期化と表示
    page.controls.clear()
    page.add(main_content)
    
    # アニメーションの実行
    await asyncio.sleep(0.1)
    main_content.opacity = 1
    page.update()

    # 時計の更新を開始
    def update_clock():
        while True:
            try:
                current_time = datetime.now()
                clock_text.value = current_time.strftime("🕒 %H:%M:%S")
                date_text.value = current_time.strftime("📅 %Y年%m月%d日")
                page.update()
            except Exception as e:
                print(f"Clock update error: {e}")
            time.sleep(1)

    threading.Thread(target=update_clock, daemon=True).start()

    # 一時的な最前面表示の処理
    page.window.always_on_top = True
    def remove_always_on_top():
        time.sleep(1)
        page.window.always_on_top = False
        page.update()

    threading.Thread(target=remove_always_on_top, daemon=True).start()

    # 初期テーマ設定
    page.bgcolor = ft.Colors.with_opacity(0.97, "#F5E6D3")
    page.theme = ft.Theme(color_scheme_seed="#D2B48C")

if __name__ == "__main__":
    ft.app(target=main)
