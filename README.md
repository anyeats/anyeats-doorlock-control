# anyeats_door_lock

DLE-STX 프레임 프로토콜 기반 잠금장치 시리얼 통신 Flutter 패키지 (Windows only)

## 프로토콜

제조사 시리얼 모니터 캡처(IMG_0778)에서 확인된 프로토콜:

```
명령:   DLE(10) STX(02) [DeviceID] ESC(1B) [Cmd] [Param] DLE(10) ETX(03)
조회:   DLE(10) STX(02) [DeviceID] 1C FF 00 DLE(10) ETX(03)
```

| 명령 | 바이트 |
|------|--------|
| Open | `10 02 01 1B 31 FF 10 03` |
| Open (5초 자동잠금) | `10 02 01 1B 31 31 10 03` |
| Close | `10 02 01 1B 30 FF 10 03` |
| 상태 조회 | `10 02 01 1C FF 00 10 03` |

응답: `SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)`

상태코드: `"00"`=잠금해제(문닫힘), `"01"`=잠금(문닫힘), `"10"`=문열림

## 사용법

### 프로젝트 연동
With Flutter:
```dart
dependencies:
  doorlock:
    git:
      url: https://github.com/anyeats/anyeats-doorlock-control
      ref: "4f75451"
```

### 기능 연동

```dart
import 'package:anyeats_door_lock/anyeats_door_lock.dart';

final controller = DoorLockController(port: 'COM2', baudRate: 9600);
controller.connect();

await controller.openLock();        // 열기
await controller.openLock5sec();    // 열기 (5초 자동잠금)
await controller.closeLock();       // 닫기

final status = await controller.queryStatus();  // 상태 조회
if (status != null) {
  print(status.isLockOpen);   // 잠금 해제 여부
  print(status.isDoorOpen);   // 문 열림 여부
  print(status.description);  // "잠금 해제 (문 닫힘)" 등
}

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

## Windows에서 Example실행하기

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

### 릴리즈 빌드

```powershell
flutter build windows --release
```

결과물: `example\build\windows\x64\runner\Release\` 폴더에 `.exe` 생성

## 의존성

- [serial_port_win32](https://pub.dev/packages/serial_port_win32) - Windows 시리얼 포트 통신

