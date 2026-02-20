"""
Door Lock Controller Module
시리얼 통신을 통해 잠금장치를 제어하는 모듈
- Windows: ctypes로 Windows API 직접 호출 (Overlapped I/O + WaitCommEvent)
- 기타 OS: pyserial 사용
"""
import sys
import time
from typing import Optional

if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes as wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    # CreateFile 상수
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    FILE_FLAG_OVERLAPPED = 0x40000000
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    # EscapeCommFunction 상수
    SETRTS = 3
    SETDTR = 5

    # PurgeComm 상수
    PURGE_RXCLEAR = 0x0008

    # SetCommMask 상수
    EV_RXCHAR = 0x0001

    # WaitForSingleObject 상수
    WAIT_OBJECT_0 = 0x00000000
    WAIT_TIMEOUT = 0x00000102

    # Error codes
    ERROR_IO_PENDING = 997

    class DCB(ctypes.Structure):
        _fields_ = [
            ('DCBlength', wintypes.DWORD),
            ('BaudRate', wintypes.DWORD),
            ('flags', wintypes.DWORD),
            ('wReserved', wintypes.WORD),
            ('XonLim', wintypes.WORD),
            ('XoffLim', wintypes.WORD),
            ('ByteSize', wintypes.BYTE),
            ('Parity', wintypes.BYTE),
            ('StopBits', wintypes.BYTE),
            ('XonChar', ctypes.c_char),
            ('XoffChar', ctypes.c_char),
            ('ErrorChar', ctypes.c_char),
            ('EofChar', ctypes.c_char),
            ('EvtChar', ctypes.c_char),
            ('wReserved1', wintypes.WORD),
        ]

    class COMMTIMEOUTS(ctypes.Structure):
        _fields_ = [
            ('ReadIntervalTimeout', wintypes.DWORD),
            ('ReadTotalTimeoutMultiplier', wintypes.DWORD),
            ('ReadTotalTimeoutConstant', wintypes.DWORD),
            ('WriteTotalTimeoutMultiplier', wintypes.DWORD),
            ('WriteTotalTimeoutConstant', wintypes.DWORD),
        ]

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ('Internal', ctypes.c_void_p),
            ('InternalHigh', ctypes.c_void_p),
            ('Offset', wintypes.DWORD),
            ('OffsetHigh', wintypes.DWORD),
            ('hEvent', wintypes.HANDLE),
        ]
else:
    import serial


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
        self._handle = None  # Windows 직접 핸들
        self._write_event = None
        self._read_event = None
        self._wait_event = None
        self.serial_conn = None  # pyserial 폴백 (비Windows용)

    def connect(self) -> bool:
        """시리얼 포트에 연결"""
        if sys.platform == 'win32':
            return self._connect_win32()
        else:
            return self._connect_pyserial()

    def _connect_win32(self) -> bool:
        """Windows: CreateFile + Overlapped I/O로 포트 열기"""
        try:
            if self._handle is not None:
                return True

            port_name = f"\\\\.\\{self.port}"

            # Overlapped 모드로 포트 열기 (제조사 프로그램과 동일한 비동기 I/O)
            handle = kernel32.CreateFileW(
                port_name,
                GENERIC_READ | GENERIC_WRITE,
                0,
                None,
                OPEN_EXISTING,
                FILE_FLAG_OVERLAPPED,
                None
            )

            if handle == INVALID_HANDLE_VALUE:
                error = ctypes.get_last_error()
                print(f"포트 열기 실패: {self.port} (error: {error})")
                return False

            self._handle = handle

            # 이벤트 객체 생성 (Manual Reset)
            self._write_event = kernel32.CreateEventW(None, True, False, None)
            self._read_event = kernel32.CreateEventW(None, True, False, None)
            self._wait_event = kernel32.CreateEventW(None, True, False, None)

            # 통신 버퍼 설정
            kernel32.SetupComm(self._handle, 4096, 4096)

            # DCB 설정 (9600, 8N1, RTS/DTR 활성화)
            dcb = DCB()
            dcb.DCBlength = ctypes.sizeof(DCB)
            kernel32.GetCommState(self._handle, ctypes.byref(dcb))

            dcb.BaudRate = self.baudrate
            dcb.ByteSize = 8
            dcb.Parity = 0   # NOPARITY
            dcb.StopBits = 0  # ONESTOPBIT

            # flags 비트 설정
            dcb.flags = dcb.flags | 0x0001                   # fBinary
            dcb.flags = dcb.flags & ~(1 << 2)                # fOutxCtsFlow = 0
            dcb.flags = dcb.flags & ~(1 << 3)                # fOutxDsrFlow = 0
            dcb.flags = (dcb.flags & ~(0x3 << 4)) | (1 << 4)    # fDtrControl = ENABLE
            dcb.flags = dcb.flags & ~(1 << 8)                # fOutX = 0
            dcb.flags = dcb.flags & ~(1 << 9)                # fInX = 0
            dcb.flags = (dcb.flags & ~(0x3 << 12)) | (1 << 12)  # fRtsControl = ENABLE
            dcb.flags = dcb.flags & ~(1 << 14)               # fAbortOnError = 0

            if not kernel32.SetCommState(self._handle, ctypes.byref(dcb)):
                error = ctypes.get_last_error()
                print(f"SetCommState 실패 (error: {error})")

            # 타임아웃 설정
            timeouts = COMMTIMEOUTS()
            timeouts.ReadIntervalTimeout = 50
            timeouts.ReadTotalTimeoutMultiplier = 10
            timeouts.ReadTotalTimeoutConstant = int(self.timeout * 1000)
            timeouts.WriteTotalTimeoutMultiplier = 10
            timeouts.WriteTotalTimeoutConstant = 5000
            kernel32.SetCommTimeouts(self._handle, ctypes.byref(timeouts))

            # CommMask 설정 (제조사 프로그램과 동일: EV_RXCHAR)
            kernel32.SetCommMask(self._handle, EV_RXCHAR)

            # RTS/DTR 수동 활성화
            kernel32.EscapeCommFunction(self._handle, SETRTS)
            kernel32.EscapeCommFunction(self._handle, SETDTR)

            time.sleep(0.2)
            print(f"포트 연결 완료: {self.port} (ctypes Overlapped I/O)")
            return True

        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    def _connect_pyserial(self) -> bool:
        """비Windows: pyserial로 연결"""
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
            )
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    def disconnect(self):
        """시리얼 포트 연결 해제"""
        if self._handle is not None:
            kernel32.CloseHandle(self._handle)
            self._handle = None
        if self._write_event is not None:
            kernel32.CloseHandle(self._write_event)
            self._write_event = None
        if self._read_event is not None:
            kernel32.CloseHandle(self._read_event)
            self._read_event = None
        if self._wait_event is not None:
            kernel32.CloseHandle(self._wait_event)
            self._wait_event = None
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
            if not self.connect():
                return False

            if self.append_cr:
                command = command + bytes([0x0D])

            if sys.platform == 'win32':
                return self._send_command_win32(command)
            else:
                return self._send_command_pyserial(command)

        except Exception as e:
            print(f"명령 전송 실패: {e}")
            return False

    def _send_command_win32(self, command: bytes) -> bool:
        """Windows: Overlapped I/O WriteFile + WaitCommEvent + ReadFile"""
        # 수신 버퍼 클리어
        kernel32.PurgeComm(self._handle, PURGE_RXCLEAR)

        # 1. WaitCommEvent 시작 (Overlapped - Write 전에 비동기로 대기 시작)
        evt_mask = wintypes.DWORD(0)
        ov_wait = OVERLAPPED()
        ctypes.memset(ctypes.byref(ov_wait), 0, ctypes.sizeof(OVERLAPPED))
        ov_wait.hEvent = self._wait_event
        kernel32.ResetEvent(self._wait_event)

        wait_started = True
        result = kernel32.WaitCommEvent(
            self._handle, ctypes.byref(evt_mask), ctypes.byref(ov_wait)
        )
        if not result:
            err = ctypes.get_last_error()
            if err != ERROR_IO_PENDING:
                print(f"WaitCommEvent 시작 실패 (error: {err})")
                wait_started = False
            # ERROR_IO_PENDING = 정상 (비동기 대기 중)

        # 2. Overlapped WriteFile
        bytes_written = wintypes.DWORD(0)
        buf = (ctypes.c_char * len(command))(*command)
        ov_write = OVERLAPPED()
        ctypes.memset(ctypes.byref(ov_write), 0, ctypes.sizeof(OVERLAPPED))
        ov_write.hEvent = self._write_event
        kernel32.ResetEvent(self._write_event)

        result = kernel32.WriteFile(
            self._handle, buf, len(command),
            ctypes.byref(bytes_written), ctypes.byref(ov_write)
        )
        if not result:
            err = ctypes.get_last_error()
            if err == ERROR_IO_PENDING:
                # Write 완료 대기
                wr = kernel32.WaitForSingleObject(self._write_event, 5000)
                if wr != WAIT_OBJECT_0:
                    print("WriteFile 타임아웃")
                    return False
                kernel32.GetOverlappedResult(
                    self._handle, ctypes.byref(ov_write),
                    ctypes.byref(bytes_written), False
                )
            else:
                print(f"WriteFile 실패 (error: {err})")
                return False

        print(f"명령 전송: {command.hex()} (WriteFile: {bytes_written.value} bytes)")

        # 3. FlushFileBuffers - 데이터가 실제로 wire로 전송되도록 보장
        kernel32.FlushFileBuffers(self._handle)

        # 4. WaitCommEvent 완료 대기 (device 응답)
        if wait_started:
            wr = kernel32.WaitForSingleObject(
                self._wait_event, int(self.timeout * 1000)
            )

            if wr == WAIT_OBJECT_0:
                transferred = wintypes.DWORD(0)
                kernel32.GetOverlappedResult(
                    self._handle, ctypes.byref(ov_wait),
                    ctypes.byref(transferred), False
                )
                print(f"WaitCommEvent 완료: evt_mask={evt_mask.value}")

                if evt_mask.value & EV_RXCHAR:
                    # 5. Overlapped ReadFile
                    read_buf = (ctypes.c_char * 64)()
                    bytes_read = wintypes.DWORD(0)
                    ov_read = OVERLAPPED()
                    ctypes.memset(ctypes.byref(ov_read), 0, ctypes.sizeof(OVERLAPPED))
                    ov_read.hEvent = self._read_event
                    kernel32.ResetEvent(self._read_event)

                    result = kernel32.ReadFile(
                        self._handle, read_buf, 64,
                        ctypes.byref(bytes_read), ctypes.byref(ov_read)
                    )
                    if not result:
                        err = ctypes.get_last_error()
                        if err == ERROR_IO_PENDING:
                            kernel32.WaitForSingleObject(self._read_event, 1000)
                            kernel32.GetOverlappedResult(
                                self._handle, ctypes.byref(ov_read),
                                ctypes.byref(bytes_read), False
                            )

                    if bytes_read.value > 0:
                        response = bytes(read_buf[:bytes_read.value])
                        print(f"응답 수신: {response.hex()}")
                    else:
                        print("응답 데이터 없음")
            elif wr == WAIT_TIMEOUT:
                print("WaitCommEvent 타임아웃")
                # 타임아웃 시 pending WaitCommEvent 취소
                kernel32.CancelIo(self._handle)
            else:
                print(f"WaitCommEvent 대기 실패: {wr}")
                kernel32.CancelIo(self._handle)
        else:
            print("WaitCommEvent 없이 응답 대기 불가")

        return True

    def _send_command_pyserial(self, command: bytes) -> bool:
        """비Windows: pyserial로 전송"""
        self.serial_conn.reset_input_buffer()
        self.serial_conn.write(command)
        self.serial_conn.flush()

        print(f"명령 전송: {command.hex()} (길이: {len(command)} bytes)")

        time.sleep(0.15)
        if self.serial_conn.in_waiting > 0:
            response = self.serial_conn.read(self.serial_conn.in_waiting)
            print(f"응답 수신: {response.hex()}")
        else:
            print("응답 없음 (타임아웃)")

        return True

    def open_lock(self, device_id: int = 1) -> bool:
        """잠금장치 열기"""
        command = bytes([0x01, 0x00, 0x00, 0x00])
        return self.send_command(command)

    def close_lock(self) -> bool:
        """잠금장치 닫기"""
        command = bytes([0x00, 0x00, 0x00, 0x00])
        return self.send_command(command)

    def read_status(self) -> Optional[dict]:
        """잠금장치 상태 읽기"""
        try:
            if not self.connect():
                return None

            if sys.platform == 'win32':
                kernel32.PurgeComm(self._handle, PURGE_RXCLEAR)

                # Overlapped ReadFile
                read_buf = (ctypes.c_char * 64)()
                bytes_read = wintypes.DWORD(0)
                ov_read = OVERLAPPED()
                ctypes.memset(ctypes.byref(ov_read), 0, ctypes.sizeof(OVERLAPPED))
                ov_read.hEvent = self._read_event
                kernel32.ResetEvent(self._read_event)

                result = kernel32.ReadFile(
                    self._handle, read_buf, 5,
                    ctypes.byref(bytes_read), ctypes.byref(ov_read)
                )
                if not result:
                    err = ctypes.get_last_error()
                    if err == ERROR_IO_PENDING:
                        kernel32.WaitForSingleObject(
                            self._read_event, int(self.timeout * 1000)
                        )
                        kernel32.GetOverlappedResult(
                            self._handle, ctypes.byref(ov_read),
                            ctypes.byref(bytes_read), False
                        )

                if bytes_read.value >= 5:
                    data = bytes(read_buf[:bytes_read.value])
                    if data[0] == 0x01 and data[3] == 0x10 and data[4] == 0x03:
                        status_code = data[1:3].decode('ascii')
                        return {
                            'status': 'open' if status_code == '00' else 'closed',
                            'status_code': status_code,
                            'raw_data': data.hex()
                        }
            else:
                self.serial_conn.reset_input_buffer()
                data = self.serial_conn.read(5)
                if len(data) >= 5:
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
        """장치 ID 확인"""
        try:
            if not self.connect():
                return None

            if sys.platform == 'win32':
                read_buf = (ctypes.c_char * 64)()
                bytes_read = wintypes.DWORD(0)
                ov_read = OVERLAPPED()
                ctypes.memset(ctypes.byref(ov_read), 0, ctypes.sizeof(OVERLAPPED))
                ov_read.hEvent = self._read_event
                kernel32.ResetEvent(self._read_event)

                kernel32.ReadFile(
                    self._handle, read_buf, 10,
                    ctypes.byref(bytes_read), ctypes.byref(ov_read)
                )

            return 1
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
