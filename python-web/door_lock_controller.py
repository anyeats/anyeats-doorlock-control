"""
Door Lock Controller Module
시리얼 통신을 통해 잠금장치를 제어하는 모듈
"""
import serial
import time
from typing import Optional


class DoorLockController:
    def __init__(self, port: str = 'COM2', baudrate: int = 9600, timeout: int = 1, append_cr: bool = True):
        """
        잠금장치 컨트롤러 초기화

        Args:
            port: COM 포트 (기본값: COM2)
            baudrate: 통신 속도 (기본값: 9600)
            timeout: 타임아웃 시간 (초)
            append_cr: 명령어 끝에 CR(0x0D) 추가 여부 (기본값: True)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.append_cr = append_cr
        self.serial_conn: Optional[serial.Serial] = None

    def connect(self) -> bool:
        """
        시리얼 포트에 연결

        Returns:
            bool: 연결 성공 여부
        """
        try:
            if self.serial_conn and self.serial_conn.is_open:
                return True

            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                rtscts=True,  # RTS/CTS 하드웨어 흐름 제어 (RequestToSend)
                dsrdtr=False  # DTR/DSR 비활성화
            )
            # RTS 신호 활성화
            self.serial_conn.rts = True
            self.serial_conn.dtr = True
            time.sleep(0.2)  # 연결 안정화 대기
            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    def disconnect(self):
        """시리얼 포트 연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def send_command(self, command: bytes) -> bool:
        """
        명령어 전송

        Args:
            command: 전송할 명령어 (바이트 배열)

        Returns:
            bool: 전송 성공 여부
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                if not self.connect():
                    return False

            # CR(Carriage Return) 추가 옵션 처리
            if self.append_cr:
                command = command + bytes([0x0D])  # CR 추가

            # 송신 버퍼 비우기
            self.serial_conn.reset_output_buffer()

            # 명령어 전송
            self.serial_conn.write(command)
            self.serial_conn.flush()

            # 명령 처리 대기
            time.sleep(0.15)

            print(f"명령 전송: {command.hex()} (길이: {len(command)} bytes)")
            return True
        except Exception as e:
            print(f"명령 전송 실패: {e}")
            return False

    def open_lock(self, device_id: int = 1) -> bool:
        """
        잠금장치 열기

        Args:
            device_id: 장치 ID (기본값: 1)

        Returns:
            bool: 명령 전송 성공 여부
        """
        # OPEN 명령: 0x01 0x00 0x00 0x00
        command = bytes([0x01, 0x00, 0x00, 0x00])
        return self.send_command(command)

    def close_lock(self) -> bool:
        """
        잠금장치 닫기

        Returns:
            bool: 명령 전송 성공 여부
        """
        # CLOSE 명령: 0x00 0x00 0x00 0x00
        command = bytes([0x00, 0x00, 0x00, 0x00])
        return self.send_command(command)

    def read_status(self) -> Optional[dict]:
        """
        잠금장치 상태 읽기

        Returns:
            dict: 상태 정보 (status: 'open' | 'closed', raw_data: bytes)
            None: 읽기 실패
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                if not self.connect():
                    return None

            # 수신 버퍼 비우기
            self.serial_conn.reset_input_buffer()

            # 데이터 읽기 (최대 5바이트: SOH + 상태(2바이트) + DLE + ETX)
            data = self.serial_conn.read(5)

            if len(data) >= 5:
                # 응답 형식: 0x01 0x30 0x30/0x31 0x10 0x03
                if data[0] == 0x01 and data[3] == 0x10 and data[4] == 0x03:
                    # 상태 코드는 두 번째, 세 번째 바이트 ('00' 또는 '01')
                    status_code = data[1:3].decode('ascii')

                    return {
                        'status': 'open' if status_code == '00' else 'closed',
                        'status_code': status_code,
                        'raw_data': data.hex()
                    }

            return None
        except Exception as e:
            print(f"상태 읽기 실패: {e}")
            return None

    def check_id(self) -> Optional[int]:
        """
        장치 ID 확인

        Returns:
            int: 장치 ID
            None: 읽기 실패
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                if not self.connect():
                    return None

            # ID 체크 명령 전송이 필요하다면 여기에 구현
            # 현재는 응답만 읽는 방식으로 구현

            data = self.serial_conn.read(10)

            # ID 응답 파싱 로직
            # 예시: <SOH> 등이 포함된 응답에서 ID 추출

            return 1  # 기본 ID
        except Exception as e:
            print(f"ID 확인 실패: {e}")
            return None

    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()
