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
    CLRRTS = 4
    SETDTR = 5
    CLRDTR = 6

    # PurgeComm 상수
    PURGE_TXABORT = 0x0001
    PURGE_RXABORT = 0x0002
    PURGE_TXCLEAR = 0x0004
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

    class COMSTAT(ctypes.Structure):
        _fields_ = [
            ('flags', wintypes.DWORD),
            ('cbInQue', wintypes.DWORD),
            ('cbOutQue', wintypes.DWORD),
        ]

    # --- kernel32 함수 프로토타입 설정 (64비트 HANDLE 잘림 방지) ---
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE

    kernel32.CreateEventW.argtypes = [
        ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR
    ]
    kernel32.CreateEventW.restype = wintypes.HANDLE

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
    ]
    kernel32.WriteFile.restype = wintypes.BOOL

    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
    ]
    kernel32.ReadFile.restype = wintypes.BOOL

    kernel32.GetOverlappedResult.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p,
        ctypes.POINTER(wintypes.DWORD), wintypes.BOOL
    ]
    kernel32.GetOverlappedResult.restype = wintypes.BOOL

    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD

    kernel32.ResetEvent.argtypes = [wintypes.HANDLE]
    kernel32.ResetEvent.restype = wintypes.BOOL

    kernel32.SetCommState.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.SetCommState.restype = wintypes.BOOL

    kernel32.GetCommState.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.GetCommState.restype = wintypes.BOOL

    kernel32.SetCommTimeouts.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.SetCommTimeouts.restype = wintypes.BOOL

    kernel32.SetCommMask.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetCommMask.restype = wintypes.BOOL

    kernel32.WaitCommEvent.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
    ]
    kernel32.WaitCommEvent.restype = wintypes.BOOL

    kernel32.EscapeCommFunction.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.EscapeCommFunction.restype = wintypes.BOOL

    kernel32.PurgeComm.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.PurgeComm.restype = wintypes.BOOL

    kernel32.SetupComm.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
    kernel32.SetupComm.restype = wintypes.BOOL

    kernel32.ClearCommError.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
    ]
    kernel32.ClearCommError.restype = wintypes.BOOL

    kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel32.FlushFileBuffers.restype = wintypes.BOOL

    kernel32.CancelIo.argtypes = [wintypes.HANDLE]
    kernel32.CancelIo.restype = wintypes.BOOL
else:
    import serial


class DoorLockController:
    def __init__(self, port: str = 'COM2', baudrate: int = 9600, timeout: int = 1, append_cr: bool = False):
        """
        잠금장치 컨트롤러 초기화

        Args:
            port: COM 포트 (기본값: COM2)
            baudrate: 통신 속도 (기본값: 9600)
            timeout: 타임아웃 시간 (초)
            append_cr: 명령어 끝에 CR(0x0D) 추가 여부 (기본값: False, 제조사 프로그램과 동일)
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
        self._last_response = None  # 마지막 응답 데이터

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

            # Overlapped 모드로 포트 열기
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
            print(f"포트 핸들: 0x{handle:X}")

            # 이벤트 객체 생성 (Manual Reset)
            self._write_event = kernel32.CreateEventW(None, True, False, None)
            self._read_event = kernel32.CreateEventW(None, True, False, None)
            self._wait_event = kernel32.CreateEventW(None, True, False, None)

            # 기존 에러 클리어
            errors = wintypes.DWORD(0)
            comstat = COMSTAT()
            kernel32.ClearCommError(self._handle, ctypes.byref(errors), ctypes.byref(comstat))
            if errors.value:
                print(f"초기 에러 클리어: {errors.value:#x}")

            # 버퍼 초기화
            kernel32.PurgeComm(self._handle, PURGE_TXABORT | PURGE_RXABORT | PURGE_TXCLEAR | PURGE_RXCLEAR)

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

            # DCB 설정 검증
            verify_dcb = DCB()
            verify_dcb.DCBlength = ctypes.sizeof(DCB)
            kernel32.GetCommState(self._handle, ctypes.byref(verify_dcb))
            print(f"DCB 검증: BaudRate={verify_dcb.BaudRate}, ByteSize={verify_dcb.ByteSize}, "
                  f"Parity={verify_dcb.Parity}, StopBits={verify_dcb.StopBits}, flags=0x{verify_dcb.flags:08X}")

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
            import traceback
            traceback.print_exc()
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
            import traceback
            traceback.print_exc()
            return False

    def _send_command_win32(self, command: bytes) -> bool:
        """Windows: Overlapped I/O WriteFile + WaitCommEvent + ReadFile"""
        # 에러 상태 클리어 + 현재 버퍼 상태 확인
        errors = wintypes.DWORD(0)
        comstat = COMSTAT()
        kernel32.ClearCommError(self._handle, ctypes.byref(errors), ctypes.byref(comstat))
        if errors.value:
            print(f"에러 클리어: {errors.value:#x}")
        print(f"버퍼 상태: TX={comstat.cbOutQue}, RX={comstat.cbInQue}")

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
        if result:
            # 이미 이벤트 발생 (즉시 완료)
            print(f"WaitCommEvent 즉시 완료: evt_mask={evt_mask.value}")
        else:
            err = ctypes.get_last_error()
            if err == ERROR_IO_PENDING:
                print("WaitCommEvent 대기 시작 (IO_PENDING)")
            else:
                print(f"WaitCommEvent 시작 실패 (error: {err})")
                wait_started = False

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

        # 3. Write 후 TX 버퍼 상태 확인
        errors2 = wintypes.DWORD(0)
        comstat2 = COMSTAT()
        kernel32.ClearCommError(self._handle, ctypes.byref(errors2), ctypes.byref(comstat2))
        print(f"Write 후 버퍼: TX={comstat2.cbOutQue}, RX={comstat2.cbInQue}, errors={errors2.value:#x}")

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
                        self._last_response = response
                        print(f"응답 수신: {response.hex()}")
                    else:
                        self._last_response = None
                        print("응답 데이터 없음")
            elif wr == WAIT_TIMEOUT:
                # 타임아웃 후 최종 버퍼 상태 확인
                errors3 = wintypes.DWORD(0)
                comstat3 = COMSTAT()
                kernel32.ClearCommError(self._handle, ctypes.byref(errors3), ctypes.byref(comstat3))
                print(f"WaitCommEvent 타임아웃 (TX={comstat3.cbOutQue}, RX={comstat3.cbInQue}, err={errors3.value:#x})")
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
            self._last_response = response
            print(f"응답 수신: {response.hex()}")
        else:
            self._last_response = None
            print("응답 없음 (타임아웃)")

        return True

    def send_raw(self, hex_string: str) -> bool:
        """
        Raw hex 문자열을 직접 전송 (프로토콜 실험용)
        CR 추가 없이 입력된 hex 그대로 전송

        Args:
            hex_string: 공백 구분 hex 문자열 (예: "01 00 00 00 0D")
        """
        try:
            if not self.connect():
                return False

            hex_clean = hex_string.replace(' ', '').replace('0x', '').replace(',', '')
            command = bytes.fromhex(hex_clean)

            print(f"[RAW] 전송: {command.hex()} ({len(command)} bytes)")

            if sys.platform == 'win32':
                return self._send_command_win32(command)
            else:
                return self._send_command_pyserial(command)

        except ValueError as e:
            print(f"Hex 파싱 실패: {e}")
            return False
        except Exception as e:
            print(f"Raw 전송 실패: {e}")
            return False

    def _build_frame(self, device_id: int, command_char: str, param: int = 0xFF) -> bytes:
        """
        DLE-STX 프레임 생성 (제조사 프로토콜)
        프레임: DLE(10) STX(02) [DeviceID] [ESC(1B)] [Command] [Param] DLE(10) ETX(03)
        """
        return bytes([
            0x10, 0x02,                    # DLE STX (프레임 시작)
            device_id,                     # 장치 ID
            0x1B,                          # ESC
            ord(command_char),             # '1'=열기(0x31), '0'=닫기(0x30)
            param,                         # 파라미터 (0xFF=일반, 0x31=5초 자동잠금)
            0x10, 0x03,                    # DLE ETX (프레임 끝)
        ])

    def open_lock(self, device_id: int = 1) -> bool:
        """잠금장치 열기"""
        command = self._build_frame(device_id, '1')
        return self.send_command(command)

    def open_lock_5sec(self, device_id: int = 1) -> bool:
        """잠금장치 열기 (5초 후 자동잠금) - 문이 열리지 않으면 5초 후 닫힘"""
        command = self._build_frame(device_id, '1', param=0x31)
        return self.send_command(command)

    def close_lock(self, device_id: int = 1) -> bool:
        """잠금장치 닫기"""
        command = self._build_frame(device_id, '0')
        return self.send_command(command)

    def query_status(self, device_id: int = 1) -> Optional[dict]:
        """
        잠금장치 상태 조회 (능동적 쿼리)
        명령: 10 02 [DeviceID] 1C FF 00 10 03
        응답 상태코드: "00"=잠금해제(문닫힘), "01"=잠금(문닫힘), "10"=문열림
        """
        command = bytes([
            0x10, 0x02,        # DLE STX
            device_id,         # 장치 ID
            0x1C,              # 상태 조회 명령
            0xFF, 0x00,        # 파라미터
            0x10, 0x03,        # DLE ETX
        ])

        self._last_response = None
        success = self.send_command(command)

        if not success or self._last_response is None:
            return None

        return self._parse_status_response(self._last_response)

    def _parse_status_response(self, data: bytes) -> Optional[dict]:
        """상태 조회 응답 파싱"""
        STATUS_MAP = {
            '00': {'lock': 'open', 'door': 'closed', 'description': '잠금 해제 (문 닫힘)'},
            '01': {'lock': 'closed', 'door': 'closed', 'description': '잠금 (문 닫힘)'},
            '10': {'lock': 'open', 'door': 'open', 'description': '문 열림'},
        }

        status_code = None

        # SOH 프로토콜: SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)
        if len(data) >= 5:
            for i in range(len(data) - 4):
                if data[i] == 0x01 and data[i+3] == 0x10 and data[i+4] == 0x03:
                    try:
                        status_code = data[i+1:i+3].decode('ascii')
                        break
                    except (UnicodeDecodeError, ValueError):
                        pass

        # DLE-STX + 'S' 마커 프로토콜: STX(02) S(53) DeviceID Status1 Status2 DLE(10) ETX(03)
        if status_code is None and len(data) >= 7:
            for i in range(len(data) - 6):
                if data[i] == 0x02 and data[i+1] == 0x53:
                    try:
                        status_code = data[i+3:i+5].decode('ascii')
                        break
                    except (UnicodeDecodeError, ValueError):
                        pass

        if status_code is None:
            print(f"상태코드 파싱 실패: {data.hex()}")
            return {
                'status_code': None,
                'lock': 'unknown',
                'door': 'unknown',
                'description': f'파싱 실패 (raw: {data.hex()})',
                'raw_data': data.hex()
            }

        info = STATUS_MAP.get(status_code, {
            'lock': 'unknown',
            'door': 'unknown',
            'description': f'알 수 없는 상태코드: {status_code}'
        })

        return {
            'status_code': status_code,
            'lock': info['lock'],
            'door': info['door'],
            'description': info['description'],
            'raw_data': data.hex()
        }

    def read_status(self) -> Optional[dict]:
        """잠금장치 상태 읽기"""
        try:
            if not self.connect():
                return None

            if sys.platform == 'win32':
                kernel32.PurgeComm(self._handle, PURGE_RXCLEAR)

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
