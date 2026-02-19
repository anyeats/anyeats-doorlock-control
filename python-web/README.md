# Door Lock Control

## 실행 방법

1. `run.bat` 더블클릭
2. 브라우저에서 `http://localhost:5000` 접속

## 파일 구성

- `app.py` - 웹 서버
- `door_lock_controller.py` - 시리얼 통신
- `templates/index.html` - 웹 UI
- `requirements.txt` - 패키지 목록
- `run.bat` - 실행 파일

## 통신 설정

- COM2, 9600, None, 1
- RTS/CTS 하드웨어 흐름 제어
- CR(0x0D) 추가 옵션
