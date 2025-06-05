from pathlib import Path
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import io
from datetime import datetime
import getpass
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

LOGISTICS_BASE_URL = "https://logistics.amazon.co.jp/internal"
SHAREPOINT_BASE_URL = "https://share.amazon.com"
SHAREPOINT_TEAM_URL = "sites/COJP_ORM"
DOWNLOAD_PATH = Path.home() / 'Documents/dsp_info/data'
TODAY = datetime.now().strftime('%Y/%m/%d')
USERNAME = getpass.getuser()
MIDWAY_FILE = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\python\\Midway"

class Sharepoint:
    def __init__(self):    
        self.session = requests.Session()
        self.session.auth = HttpNegotiateAuth()
        self.session.verify = False
        self.headers = {
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose'
        }
        
    def get_files(self, path: str, output_dir: str, max_workers: int = 5):
        folder_url = f"{SHAREPOINT_BASE_URL}/{SHAREPOINT_TEAM_URL}/_api/web/GetFolderByServerRelativeUrl('{path}')/Files"
        try:
            response = self.session.get(folder_url, headers=self.headers, verify=self.session.verify)
            response.raise_for_status()
            files = response.json().get('d', {}).get('results', [])

            def download_file(file):
                file_name = file.get('Name') or file.get('name')
                file_url = f"{SHAREPOINT_BASE_URL}{file['ServerRelativeUrl']}"
                output_path = Path(output_dir) / file_name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    file_response = self.session.get(file_url, headers=self.headers, verify=self.session.verify)
                    file_response.raise_for_status()
                    with open(output_path, 'wb') as f:
                        f.write(file_response.content)
                    return f"Downloaded: {file_name}"
                except Exception as e:
                    return f"Error downloading {file_name}: {e}"

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(download_file, file) for file in files]
                for future in as_completed(futures):
                    print(future.result())

        except Exception as e:
            print(f"Error accessing folder: {e}")
            
    def get_file(self, path: str, output_dir: str, file_name: str):
        folder_url = f"{SHAREPOINT_BASE_URL}/{SHAREPOINT_TEAM_URL}/_api/web/GetFileByServerRelativeUrl('{path}/{file_name}')/$value"
        try:
            response = self.session.get(folder_url, headers=self.headers, verify=self.session.verify)
            response.raise_for_status()
            output_path = Path(output_dir) / file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return f"Downloaded: {file_name}"
                
        except requests.HTTPError as e:
            return f"HTTP error while accessing {file_name}: {e}"
        except Exception as e:
            return f"Error downloading {file_name}: {e}"
        
    def executor_get(self, path: str, output_dir: str, file_names: list):
        results = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.get_file, path, output_dir, file_name)
                for file_name in file_names
            ]
            for future in as_completed(futures):
                result = future.result()
                print(result)
                results.append(result)
        return results
    
    def get_json(self, path: str):
        try:
            response = self.session.get(path, headers=self.headers, verify=self.session.verify)
            response.raise_for_status()
            data = response.json()
            return data.get('d', {}).get('results', [])
        except Exception as e:
            print(f"Error accessing folder: {e}")
            return None
        
    def info_download(self):
        try:
            url = f"{SHAREPOINT_BASE_URL}/{SHAREPOINT_TEAM_URL}/Shared%20Documents/04_Metrics/dsp_info.txt"
            response = self.session.get(url, headers=self.headers, verify=self.session.verify)
            
            if response.status_code == 200:
                df = pd.read_csv(
                    io.StringIO(response.content.decode('utf-8')),
                    sep='\t',
                    usecols=['parent_location', 'station_code', 'provider_code', 'service_area_id']
                )
                
                dsp_name_mapping = {
                    'ENSH': 'ENSHU',
                    'SATT': 'LOGINET',
                    'MRUK': 'MARUWA',
                    'SBCL': 'SBS',
                    'WKB': 'WAKABA'
                }
                
                df = df[~df['parent_location'].str.startswith('H')]
                df['provider_code'] = df['provider_code'].map(dsp_name_mapping)
                
                DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
                df.to_csv(DOWNLOAD_PATH / 'dsp_info.csv', index=False)
                
        except Exception as e:
            print(f'Download failed: {e}')

class Midway:
    def __init__(self, headless=True):
        self.profile_path = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\python"
        self.hng_path = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Google\\Chrome\\__hng"
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f'--user-data-dir={self.profile_path}')
        self.options.add_argument('--disable-gpu')
        if headless:
            self.options.add_argument('--headless=new')
        self.driver = webdriver.Chrome(
            service=Service(
                ChromeDriverManager().install()
            ),
            options=self.options
        )
        
    def check_midway_auth(self):
        is_valid = (Path(MIDWAY_FILE).exists() and 
                Path(MIDWAY_FILE).read_text().strip() == TODAY)
        return is_valid
        
    def update_midway_auth(self):
        Path(MIDWAY_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(MIDWAY_FILE, 'w') as f:
            f.write(TODAY)

    def midway_auth(self):
        self.driver.get('https://midway-auth.amazon.com/login')
        wait = WebDriverWait(self.driver, 60)
        
        try:
            body_text = self.driver.find_element(By.TAG_NAME, 'body').get_attribute('innerHTML')
            if 'Sign in with Midway' not in body_text:
                self.update_midway_auth()
                return True
            hng_path = self.hng_path
            
            if not Path(hng_path).exists():
                return False
            
            with open(hng_path, 'r') as f:
                password = f.read().strip()
                
            username_input = wait.until(EC.presence_of_element_located((By.ID, 'user_name')))
            username_input.clear()
            username_input.send_keys(USERNAME)
            
            password_input = wait.until(EC.presence_of_element_located((By.ID, 'password')))
            password_input.clear()
            password_input.send_keys(password)
            
            verify_btn = wait.until(EC.element_to_be_clickable((By.ID, 'verify_btn')))
            verify_btn.click()
            
            wait.until_not(EC.presence_of_element_located((By.ID, 'login_form')))
            self.update_midway_auth()
            return True
        
        except Exception as e:
            print(f"認証処理でエラーが発生しました: {str(e)}")
            return False
