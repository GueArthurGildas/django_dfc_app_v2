@echo off
echo ================================================
echo   CIE Manager - DFC/CIE
echo ================================================
cd /d %~dp0
call venv\Scripts\activate
python run_server.py --host 0.0.0.0 --port 8000
pause
