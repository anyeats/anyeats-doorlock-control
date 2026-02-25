@echo off
echo Door Lock Control Web Server
echo.

REM 패키지 설치
pip install -q Flask pyserial

REM 서버 실행
echo 서버 시작... http://localhost:5000
echo.
python app.py

pause
