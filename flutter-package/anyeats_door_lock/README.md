# anyeats_door_lock

DLE-STX 프레임 프로토콜 기반 잠금장치 시리얼 통신 Flutter 패키지 (Windows only)

## 프로토콜

제조사 시리얼 모니터 캡처(IMG_0778)에서 확인된 프로토콜:

```
DLE(10) STX(02) [DeviceID] ESC(1B) [Command] FF DLE(10) ETX(03)
```

| 명령 | 바이트 |
|------|--------|
| Open | `10 02 01 1B 31 FF 10 03` |
| Close | `10 02 01 1B 30 FF 10 03` |

응답: `SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)`

## 사용법

```dart
import 'package:anyeats_door_lock/anyeats_door_lock.dart';

final controller = DoorLockController(port: 'COM2', baudRate: 9600);
controller.connect();

await controller.openLock();   // 열기
await controller.closeLock();  // 닫기

controller.disconnect();
```

## 프로젝트 구조

```
lib/
├── anyeats_door_lock.dart          # export
└── src/
    ├── door_lock_protocol.dart     # DLE-STX 프레임 빌드/파싱
    └── door_lock_controller.dart   # serial_port_win32 기반 컨트롤러
```

## Windows에서 실행하기

### 사전 준비

1. **Flutter SDK** 설치
   - https://docs.flutter.dev/get-started/install/windows/desktop

2. **Visual Studio 2022** 설치
   - https://visualstudio.microsoft.com/
   - 워크로드에서 **"C++를 사용한 데스크톱 개발"** 체크

3. **확인**
   ```powershell
   flutter doctor
   ```
   `[✓] Windows Version`, `[✓] Visual Studio` 두 줄이 초록색이어야 합니다.

### 실행

```powershell
# example 폴더로 이동
cd flutter-package\anyeats_door_lock\example

# 의존성 설치
flutter pub get

# Windows로 실행
flutter run -d windows
```

첫 빌드는 C++ 컴파일 때문에 2-3분 소요, 이후에는 빠릅니다.

### 릴리즈 빌드 (배포용)

```powershell
flutter build windows --release
```

결과물: `example\build\windows\x64\runner\Release\` 폴더에 `.exe` 생성

## 의존성

- [serial_port_win32](https://pub.dev/packages/serial_port_win32) - Windows 시리얼 포트 통신

## 시리얼 포트 설정

- Baud Rate: 9600
- Data Bits: 8
- Parity: None
- Stop Bits: 1
- Flow Control: RTS/DTR enabled
