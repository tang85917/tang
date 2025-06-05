@echo off
call C:\Users\tangtao\Desktop\TAO\venv\Scripts\activate.bat
REM --server.headless=true でブラウザの自動起動を無効化
start /B streamlit run Home.py --server.headless=true
cmd /c "C:\Program Files\Google\Chrome\Application\chrome.exe" http://localhost:8501
