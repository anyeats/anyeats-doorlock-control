# Windows 빌드 가이드

## 사전 요구사항

| 항목 | 설명 |
|------|------|
| Flutter SDK | `C:\flutter` 에 설치 (버전 3.41.2 이상) |
| Visual Studio Build Tools 2022 | **"C++를 사용한 데스크톱 개발"** 워크로드 필수 |

### Visual Studio Code vs Visual Studio Build Tools

> **주의:** Visual Studio Code(코드 에디터)와 Visual Studio Build Tools(C++ 컴파일러)는 **다른 프로그램**입니다.
> Flutter Windows 빌드에는 반드시 **Visual Studio Build Tools**가 필요합니다.

### Visual Studio Build Tools 설치

1. https://visualstudio.microsoft.com/downloads/ 접속
2. 페이지 하단 **"Tools for Visual Studio"** 섹션 → **"Build Tools for Visual Studio 2022"** 다운로드
3. 설치 시 **"C++를 사용한 데스크톱 개발(Desktop development with C++)"** 워크로드 선택
4. 다음 구성 요소가 포함되어 있는지 확인:
   - `MSVC v143 - VS 2022 C++ x64/x86 빌드 도구`
   - `C++ CMake 도구`
   - `Windows 10 SDK`

---

## 빌드 방법

```bash
cd example
C:\flutter\bin\flutter build windows --release
```

빌드 결과물 위치:
```
example\build\windows\x64\runner\Release\
  anyeats_door_lock_example.exe
  flutter_windows.dll
  anyeats_door_lock_plugin.dll
  data\
    icudtl.dat
    flutter_assets\
```

모든 파일이 자동으로 복사되므로 수동 작업 없이 바로 실행 가능합니다.

---

## 수정된 파일 및 이유

### `example/windows/CMakeLists.txt`

**1. CMake 4.x / googletest 호환성 문제 수정**

```cmake
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
```

- **원인:** googletest 의존성의 `CMakeLists.txt`가 CMake 4.x에서 제거된 구버전 문법 사용
- **증상:** `Compatibility with CMake < 3.5 has been removed from CMake` 오류

**2. CMake install prefix 고정**

```cmake
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/runner/Release" CACHE PATH "..." FORCE)
```

- **원인:** 기본 install prefix가 `C:\Program Files\anyeats_door_lock_example`로 설정되어 관리자 권한 없이 실패
- **근본 원인:** Flutter 템플릿이 generator expression(`$<TARGET_FILE_DIR:...>`)을 `CMAKE_INSTALL_PREFIX`에 사용하는데, 이 표현식은 configure 시점에 평가되지 않아 기본값이 사용됨

**3. native_assets 디렉토리 생성**

```cmake
install(CODE "file(MAKE_DIRECTORY \"${NATIVE_ASSETS_DIR}\")" COMPONENT Runtime)
```

- **원인:** native assets가 없는 경우 해당 디렉토리가 존재하지 않아 install 단계에서 오류 발생

### `example/windows/runner/CMakeLists.txt`

**post-build 자동 복사 명령 추가**

빌드 완료 후 다음 파일들을 exe 옆에 자동 복사:
- `flutter_windows.dll`
- `data/icudtl.dat`
- `data/flutter_assets/`
- `anyeats_door_lock_plugin.dll`

- **원인:** CMake install step이 Release 디렉토리가 아닌 다른 경로에 파일을 설치하는 경우에 대한 보완책
