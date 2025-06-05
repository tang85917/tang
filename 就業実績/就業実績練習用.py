import logging
from pathlib import Path
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import logging
import pandas as pd
import io
import urllib3

#ログ表示の設定
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger=logging.getLogger(__name__)

class DownloadWorkrecord:
    def __init__(self):
        self.logger=logger

    def downloadworkrecord(self):
        try:
            #除外するファイル
            exclude_files = ['Audit一覧.xlsx', '就業実績_管理DB.xlsx']

            #出力先のディレクトリ
            output_dir=Path(r'..\data')
            output_dir.mkdir(parents=True,exist_ok=True)

            #SharePointのファイル一覧を取得
            folder_path='Shared Documents/06_Project/就業実績'  #サーバーの相対パス
            #https://<サイトURL>/sites/<サイト名>/Shared Documents/<フォルダ名>
            folder_url=f"https://share.amazon.com/sites/COJP_ORM/_api/web/GetFolderByServerRelativeUrl('{folder_path}')/Files"

            #セッションを作成して、認証を維持する
            session=requests.Session()
            session.auth=HttpNegotiateAuth()  #windowsのログイン情報を使って、サーバーに自動認証する
            headers={
                'Accept':'application/json;odata=verbose',
                'Content-Type':'application/json;odata=verbose',
            }
            self.logger.info('SharePoint接続中...')
            response=session.get(
                folder_url,
                headers=headers,
                timeout=15,
                verify=False
            )  

            #statusコードが200ではない場合はエラーを発生させる
            response.raise_for_status()
            files_data=response.json()

            dfs=[]
            first_header=None
            processed_files=[]

            #jsondataからファイル名を取り出す
            processed_count=0
            for file in files_data['d']['results']:
                file_name=file['Name']

                #除外ファイルをスキップ
                if file_name in exclude_files:
                    self.logger.info(f'対象外ファイル:{file_name}')
                    continue

                if file_name.lower().endswith(('.xlsx','.xlsm')):
                    try:
                        file_url=f"https://share.amazon.com{file['ServerRelativeUrl']}"

                        self.logger.info(f'読み込み中:{file_name}')
                        file_response=session.get(
                            file_url,
                            timeout=15,
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
                        self.logger.info(f'プロセスエラー：{file_name}：{set(e)}')
                        continue

            #全てのデータフレームを結合
            if dfs:
                self.logger.info(f'{len(dfs)}個のデータを結合しました。ファイル名：\n{','.join(processed_files)}')
                merged_df=pd.concat(dfs,ignore_index=True)
                self.logger.info(f'結合されたデータ：{merged_df.shape}')

                output_path=output_dir/'alldate.csv'
                merged_df.to_csv(output_path,index=False,encoding='utf-8-sig')
                self.logger.info(f'CSVファイルを{output_path}に保存しました。')

                #結合されたファイルのサイズを確認
                file_size=output_path.stat().st_size
                self.logger.info(f'結合されたCSVファイルのサイズ：{file_size}bytes')
            else:
                self.logger.warning('結合できるファイルがありませんでした。')
            self.logger.info(f'ダウンロード完了しました。{processed_count}個ファイルを処理しました。')
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f'通信エラー：{str(e)}')
            return False
        except ValueError as e:
            self.logger.error(f'JSON 送信エラー：{str(e)}')
            return False
        except Exception as e:
            self.logger.error(f'予期しないエラー：{str(e)}')
            return False

if __name__=='__main__':
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.info('ダウンロード開始')
        download=DownloadWorkrecord()
        result=download.downloadworkrecord()

        if result:
            logger.info('ダウンロード成功')
        else:
            logger.error('ダウンロード失敗')

    except Exception as e:
        logger.error(f'メインプロセスエラー:{str(e)}')




               
                

            