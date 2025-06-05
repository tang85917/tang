import logging
from pathlib import Path
import requests
import pandas as pd
import io
import urllib3
from requests_negotiate_sspi import HttpNegotiateAuth

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s-%(levelname)s-%(message)s')
logger=logging.getLogger(__name__)
print(__name__)

class Download:
    def __init__(self):
        self.logger=logger

    def download(self):
        try:
            exclude_files=['Audit一覧.xlsx', '就業実績_管理DB.xlsx']

            output=Path(r'..\data')
            output.mkdir(parents=True,exist_ok=True)

            folder_path='Shared Documents/06_Project/就業実績'
            folder_url=f"https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('{folder_path}')/Files"

            session=requests.Session()
            session.auth=HttpNegotiateAuth()
            headers={
                'Accept':'application/json;odata=verbose',
                'Content-Type':'application/json;odata=verbose',
            }

            self.logger.info('SharePoint接続中...')
            response=session.get(
                folder_url,
                headers=headers,
                timeout=10,
                verify=False
            )

            response.raise_for_status()
            files_data=response.json()
            self.logger.info(f"response_files_data:\n{files_data}\n")

            dfs=[]
            first_header=None
            processed_files=[]
            processed_count=0

            for file in files_data['d']['results']:
                file_name=file['Name']

                if file_name in exclude_files:
                    self.logger.info(f'対象外ファイル：{file_name}')
                    continue

                if file_name.lower().endswith(('.xlsx','.xlsm')):
                    try:
                        file_url=f"https://share.amazon.com/{file['ServerRelativeUrl']}"
                        self.logger.info(f'読み込み中:{file_name}')
                        file_response=session.get(
                            file_url,
                            timeout=10,
                            verify=False
                        )
                        file_response.raise_for_status()
                        
                        df=pd.read_excel(io.BytesIO(file_response.content))

                        if not df.empty:
                            if first_header is None:
                                first_header=df.columns.tolist()
                                self.logger.info(f'ヘッダーを設定します：{first_header}')

                            if len(df.columns)==len(first_header):
                                df.columns=first_header
                                dfs.append(df)
                                processed_files.append(file_name)
                                processed_count+=1
                                self.logger.info(f'処理成功：{file_name}')
                            else:
                                self.logger.warning(f'ヘッダーが異なるため、{file_name}をスキップします。')

                        else:
                            self.logger.warning(f'データが見つからないため、スキップします。{file_name}')
                    except Exception as e:
                        self.logger.error(f'プロセスエラー：{file_name}:{str(e)}')
                        continue
                
            if dfs:
                self.logger.info(f'{len(dfs)}個データを結合しました。ファイル名：\n{(processed_files)}\n')
                merged_df=pd.concat(dfs,ignore_index=True)
                self.logger.info(f'結合されたデータ：{merged_df.shape}')

                output_path=output / 'alldata.csv'
                merged_df.to_csv(output_path,index=False,encoding='utf-8-sig')
                self.logger.info(f'CSVファイルを{output}に保存されました。')

                file_info=output_path.stat()
                self.logger.info(f"{file_info}\n")
            else:
                self.logger.warning('結合できるファイルがありませんでした。')
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f'通信エラー：{str(e)}')
            return False
        except ValueError as e:
            self.logger.error(f'JSON 送信エラー：{str(e)}')
            return False
        except Exception as e:
            self.logger.error(f'その他予期しないエラーが発生しました{str(e)}')
            return False

if __name__=='__main__':
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.info('ダウンロード開始')
        download=Download()
        result=download.download()

        if result:
            logger.info('ダウンロード成功')
        else:
            logger.error('ダウンロード失敗')

    except Exception as e:
        logger.error(f'メインプロセスエラー：{str(e)}')
            



