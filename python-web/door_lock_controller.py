"""
Door Lock Controller Module
시리얼 통신을 통해 잠금장치를 제어하는 모듈
"""
import sys
import serial
import time
from typing import Optional

# Windows API 상수 및 구조체
if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes as wintypes

    EV_RXCHAR = 0x0001
    WAIT_TIMEOUT = 0x00000102
    ERROR_IO_PENDING = 997

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ('Internal', ctypes.POINTER(ctypes.c_ulong)),
            ('InternalHigh', ctypes.POINTER(ctypes.c_ulong)),
            ('Offset', wintypes.DWORD),
            ('OffsetHigh', wintypes.DWORD),
            ('hEvent', wintypes.HANDLE),
        ]

    kernel32 = ctypes.windll.kernel32


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

            # CommMask 설정: EV_RXCHAR (제조사 프로그램과 동일)
            # pyserial은 기본적으로 EV_ERR만 설정하므로, EV_RXCHAR로 재설정
            self._set_comm_mask()

            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    def _set_comm_mask(self):
        """Windows: SetCommMask(EV_RXCHAR) 호출"""
        if sys.platform == 'win32':
            try:
                handle = self.serial_conn._port_handle
                kernel32.SetCommMask(handle, EV_RXCHAR)
                print("CommMask 설정 완료: EV_RXCHAR")
            except Exception as e:
                print(f"CommMask 설정 실패: {e}")

    def _wait_comm_event(self, timeout_ms: int = 1000) -> bool:
        """
        Windows: WaitCommEvent로 EV_RXCHAR 이벤트 대기
        제조사 프로그램과 동일한 IOCTL_SERIAL_WAIT_ON_MASK 패턴 생성

        Args:
            timeout_ms: 대기 타임아웃 (밀리초)

        Returns:
            bool: 이벤트 수신 여부
        """
        if sys.platform != 'win32':
            time.sleep(timeout_ms / 1000)
            return False

        try:
            handle = self.serial_conn._port_handle
            mask = wintypes.DWORD(0)

            # Overlapped I/O용 이벤트 생성
            overlapped = OVERLAPPED()
            overlapped.hEvent = kernel32.CreateEventW(None, True, False, None)

            # SetCommMask + WaitCommEvent → IOCTL_SERIAL_WAIT_ON_MASK 발생
            kernel32.SetCommMask(handle, EV_RXCHAR)
            result = kernel32.WaitCommEvent(
                handle, ctypes.byref(mask), ctypes.byref(overlapped)
            )

            if result:
                # 즉시 완료
                kernel32.CloseHandle(overlapped.hEvent)
                if mask.value & EV_RXCHAR:
                    print(f"EV_RXCHAR 이벤트 수신 (즉시)")
                    return True
                return False

            # 비동기 대기
            error = ctypes.get_last_error() if hasattr(ctypes, 'get_last_error') else ctypes.GetLastError()
            if error == ERROR_IO_PENDING:
                wait_result = kernel32.WaitForSingleObject(overlapped.hEvent, timeout_ms)
                if wait_result == WAIT_TIMEOUT:
                    print("WaitCommEvent 타임아웃")
                    kernel32.CancelIo(handle)
                    kernel32.CloseHandle(overlapped.hEvent)
                    return False

                # 완료 확인
                bytes_transferred = wintypes.DWORD(0)
                kernel32.GetOverlappedResult(
                    handle, ctypes.byref(overlapped),
                    ctypes.byref(bytes_transferred), False
                )
                kernel32.CloseHandle(overlapped.hEvent)

                if mask.value & EV_RXCHAR:
                    print(f"EV_RXCHAR 이벤트 수신")
                    return True
            else:
                print(f"WaitCommEvent 실패 (error: {error})")
                kernel32.CloseHandle(overlapped.hEvent)

            return False
        except Exception as e:
            print(f"WaitCommEvent 예외: {e}")
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

            # 수신 버퍼 비우기
            self.serial_conn.reset_input_buffer()

            # 명령어 전송
            self.serial_conn.write(command)
            self.serial_conn.flush()

            print(f"명령 전송: {command.hex()} (길이: {len(command)} bytes)")

            # 응답 대기: WaitCommEvent로 EV_RXCHAR 이벤트 대기
            # (제조사 프로그램과 동일한 WAIT_ON_MASK 패턴)
            if self._wait_comm_event(timeout_ms=int(self.timeout * 1000)):
                # 이벤트 수신됨 - 데이터 읽기
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.read(self.serial_conn.in_waiting)
                    print(f"응답 수신: {response.hex()}")
            else:
                print("응답 없음 (타임아웃)")

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

            # WaitCommEvent로 데이터 수신 대기
            if self._wait_comm_event(timeout_ms=int(self.timeout * 1000)):
                if self.serial_conn.in_waiting >= 5:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)

                    if len(data) >= 5:
                        # 응답 형식: 0x01 0x30 0x30/0x31 0x10 0x03
                        if data[0] == 0x01 and data[3] == 0x10 and data[4] == 0x03:
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

            if self._wait_comm_event(timeout_ms=int(self.timeout * 1000)):
                data = self.serial_conn.read(self.serial_conn.in_waiting or 10)
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
