from pathlib import Path
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import urllib3
import logging
import pandas as pd
from datetime import datetime, timezone
import pytz
import io

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SharePointDataMerger:
    def __init__(self):
        self.logger = logger
        
    def merge_sharepoint_files(self):
        try:
            # 除外するファイル名のリスト
            exclude_files = ['Audit一覧.xlsx', '就業実績_管理DB.xlsx']
            
            # 出力先のディレクトリ
            output_dir = Path(r'C:\Users\tangtao\Desktop\TAO\PJ\就業実績\data')
            output_dir.mkdir(parents=True, exist_ok=True)

            # SharePointのファイル一覧を取得
            folder_path = '/sites/COJP_ORM/Shared Documents/06_Project/就業実績'
            folder_url = f"https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('{folder_path}')/Files"
            
            session = requests.Session()
            session.auth = HttpNegotiateAuth()
            headers = {
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose',
                'User-Agent': 'Python NTLM Client'
            }
            
            self.logger.info("Connecting to SharePoint...")
            response = session.get(
                folder_url,
                headers=headers,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            files_data = response.json()
            
            # データフレームのリストを保持
            dfs = []
            first_header = None
            processed_files = []
            
            # 現在時刻（JST）
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst)
            
            # ファイルの処理
            processed_count = 0
            for file in files_data['d']['results']:
                file_name = file['Name']
                
                # 除外ファイルをスキップ
                if file_name in exclude_files:
                    self.logger.info(f"Skipping excluded file: {file_name}")
                    continue
                
                # 更新日時のチェック
                modified_date = datetime.strptime(
                    file['TimeLastModified'],
                    '%Y-%m-%dT%H:%M:%SZ'
                ).replace(tzinfo=timezone.utc).astimezone(jst)
                    
                if file_name.lower().endswith(('.xlsx', '.xlsm')):
                    try:
                        file_url = f"https://share.amazon.com{file['ServerRelativeUrl']}"
                        
                        # ファイルの内容を直接読み込む
                        self.logger.info(f"Reading: {file_name}")
                        file_response = session.get(
                            file_url,
                            verify=False,
                            timeout=30
                        )
                        file_response.raise_for_status()
                        
                        # バイナリデータからデータフレームを作成
                        df = pd.read_excel(io.BytesIO(file_response.content))
                        
                        # データフレームが空でないことを確認
                        if not df.empty:
                            # 最初のファイルのヘッダーを保存
                            if first_header is None:
                                first_header = df.columns.tolist()
                                self.logger.info(f"First header set from {file_name}: {first_header}")
                            
                            # ヘッダーを統一
                            if len(df.columns) == len(first_header):
                                df.columns = first_header
                                dfs.append(df)
                                processed_files.append(file_name)
                                processed_count += 1
                                self.logger.info(f"Successfully processed: {file_name}")
                            else:
                                self.logger.warning(f"Skipping {file_name} due to different column count")
                        else:
                            self.logger.warning(f"Skipping empty file: {file_name}")
                            
                    except Exception as e:
                        self.logger.error(f"Error processing file {file_name}: {str(e)}")
                        continue
            
            # すべてのデータフレームを結合
            if dfs:
                self.logger.info(f"Merging {len(dfs)} files: {', '.join(processed_files)}")
                merged_df = pd.concat(dfs, ignore_index=True)
                
                # 結合されたデータの検証
                self.logger.info(f"Merged data shape: {merged_df.shape}")
                
                # CSVとして保存
                output_path = output_dir / 'merged_data.csv'
                merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"Created merged CSV file at: {output_path}")
                
                # 結合されたファイルのサイズを確認
                file_size = output_path.stat().st_size
                self.logger.info(f"Merged file size: {file_size} bytes")
            else:
                self.logger.warning("No files were successfully processed for merging")
            
            self.logger.info(f"Process completed. Total files processed and merged: {processed_count}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error: {str(e)}")
            return False
        except ValueError as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return False

# メイン実行部分
if __name__ == "__main__":
    try:
        # SSL警告を無視
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        logger.info("Starting merge process...")
        merger = SharePointDataMerger()
        result = merger.merge_sharepoint_files()
        
        if result:
            logger.info("Process completed successfully")
        else:
            logger.error("Process completed with errors")
            
    except Exception as e:
        logger.error(f"Main process error: {str(e)}")
