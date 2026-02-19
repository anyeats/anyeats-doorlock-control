#!/bin/bash
echo "Door Lock Control Web Server"
echo ""

# 패키지 설치
pip3 install -q Flask pyserial

# 서버 실행
echo "서버 시작... http://localhost:5000"
echo ""
python3 app.py
