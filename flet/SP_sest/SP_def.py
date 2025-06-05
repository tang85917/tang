import flet as ft
import pandas as pd
from pathlib import Path
import webbrowser
from datetime import datetime
from auth import sp


TODAY = datetime.now().strftime('%Y/%m/%d')
DOWNLOAD_PATH = Path.home() / 'Documents/dsp_info/data'
LOGISTICS_BASE_URL = "https://logistics.amazon.co.jp/internal"
FOLDER_URL = "https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('/sites/COJP_ORM/Shared Documents/05_DS_Rescue/2025/RP')/Files?$select=Name,ServerRelativeUrl,UniqueId"
BASE_URL = "https://share.amazon.com"

def read_info():
    info_path = DOWNLOAD_PATH / 'dsp_info.csv'
    try:
        df = pd.read_csv(info_path, usecols=[0, 1, 2])
        df.columns = ['Mother', 'Station', 'DSP']
    except Exception as e:
        print(f'ファイルが見つかりません。{e}')
    return df

def open_cortex_roster_sui(e, ds: str, view_type: str):
    info_path = DOWNLOAD_PATH / 'dsp_info.csv'
    if not ds:
        raise ValueError('Station code cannot be empty')
    
    view_paths = {
        'cortex': f"/operations/execution/itineraries?provider=ALL_DRIVERS&selectedDay={TODAY}&serviceAreaId=",
        'roster': f"/capacity/rosterview?serviceAreaId={{}}&date={TODAY}",
        'sui': f"/scheduling/dsps?serviceAreaId={{}}&date={TODAY}"
    }
    
    if view_type not in view_paths:
        raise ValueError(f"Invalid view_type: {view_type}")
    
    try:
        df = pd.read_csv(info_path).drop_duplicates(subset='station_code')
        ds = ds.upper()
        
        if ds not in df['station_code'].values:
            raise ValueError(f'Invalid station code: {ds}')
        
        service_area_id = df[df['station_code'] == ds]['service_area_id'].iloc[0]
        url = LOGISTICS_BASE_URL + view_paths[view_type].format(service_area_id)
        webbrowser.open(url)
    except Exception as e:
        print(f"{view_type.capitalize()} open failed: {e}")
        
def get_files_and_guids():
    file_info = []
    guid_map = {}
    
    try:
        files = sp.get_json(FOLDER_URL)
        
        for file in files:
            if file['Name'].lower().endswith(('.xlsx', 'xlsm')):
                file_info.append({
                    'name': file['Name'],
                    'button_name': file['Name'].split()[0],
                    'server_relative_url': file['ServerRelativeUrl'],
                    'guid': file['UniqueId']
                })
                guid_map[file['ServerRelativeUrl']] = file['UniqueId']
                
        file_info = sorted(file_info, key=lambda item: (
            0 if item['button_name'].startswith('D') and len(item['button_name']) == 4 else
            1 if item['button_name'].startswith('V') and len(item['button_name']) == 4 else
            2, item['button_name']
        ))
    except Exception as e:
        print(f'エラーが発生しました：{str(e)}')
        
    return file_info, guid_map

def download_file(file_info):
    try:
        file_url = f"{BASE_URL}{file_info['server_relative_url']}"
        response = sp.get(file_url)
        
        download_path = Path.home() / "Downloads"
        file_path = download_path / file_info['name']
        
        base, ext = file_path.stem, file_path.suffix
        counter = 1
        
        while file_path.exists():
            file_path = file_path.with_name(f"{base}_{counter}{ext}")
            counter += 1
            
        with file_path.open('wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return file_path
    except Exception as e:
        print(f"ダウンロードエラー： {str(e)}")
        return ""

