import 'dart:typed_data';

/// DLE-STX 프레임 프로토콜 (제조사 시리얼 모니터 캡처에서 확인)
///
/// 명령 프레임: DLE(10) STX(02) [DeviceID] ESC(1B) [Cmd] [Param] DLE(10) ETX(03)
/// - Open:       10 02 01 1B 31 FF 10 03  (Cmd='1', Param=FF)
/// - Open(5sec): 10 02 01 1B 31 31 10 03  (Cmd='1', Param=31, 5초 자동잠금)
/// - Close:      10 02 01 1B 30 FF 10 03  (Cmd='0', Param=FF)
///
/// 상태 조회 프레임: DLE(10) STX(02) [DeviceID] 1C FF 00 DLE(10) ETX(03)
/// - Query:      10 02 01 1C FF 00 10 03
/// - 응답 상태코드: "00"=잠금해제(문닫힘), "01"=잠금(문닫힘), "10"=문열림
///
/// 응답 프레임: SOH(01) [ASCII 2bytes] DLE(10) ETX(03)
class DoorLockProtocol {
  static const int dle = 0x10;
  static const int stx = 0x02;
  static const int etx = 0x03;
  static const int esc = 0x1B;
  static const int soh = 0x01;

  /// Open 명령 프레임 생성
  static Uint8List buildOpenFrame(int deviceId) {
    return _buildFrame(deviceId, 0x31, 0xFF); // '1', param=FF
  }

  /// Open (5초 자동잠금) 명령 프레임 생성
  static Uint8List buildOpen5secFrame(int deviceId) {
    return _buildFrame(deviceId, 0x31, 0x31); // '1', param=31
  }

  /// Close 명령 프레임 생성
  static Uint8List buildCloseFrame(int deviceId) {
    return _buildFrame(deviceId, 0x30, 0xFF); // '0', param=FF
  }

  /// 상태 조회 프레임 생성: 10 02 [id] 1C FF 00 10 03
  static Uint8List buildStatusQueryFrame(int deviceId) {
    return Uint8List.fromList([
      dle, stx,
      deviceId,
      0x1C,
      0xFF, 0x00,
      dle, etx,
    ]);
  }

  /// DLE-STX 프레임 생성
  static Uint8List _buildFrame(int deviceId, int command, int param) {
    return Uint8List.fromList([
      dle, stx, // 프레임 시작
      deviceId, // 장치 ID
      esc, // ESC
      command, // 명령 ('1' or '0')
      param, // 파라미터 (FF=일반, 31=5초 자동잠금)
      dle, etx, // 프레임 끝
    ]);
  }

  /// 응답 파싱: SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)
  static DoorLockResponse? parseResponse(Uint8List data) {
    if (data.length < 5) return null;

    // SOH 프로토콜: SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)
    for (var i = 0; i <= data.length - 5; i++) {
      if (data[i] == soh && data[i + 3] == dle && data[i + 4] == etx) {
        final statusCode = String.fromCharCodes(data.sublist(i + 1, i + 3));
        return DoorLockResponse(statusCode: statusCode, rawData: data);
      }
    }

    // DLE-STX + 'S' 마커: STX(02) S(53) DeviceID Status1 Status2 DLE(10) ETX(03)
    for (var i = 0; i <= data.length - 7; i++) {
      if (data[i] == stx && data[i + 1] == 0x53) {
        final statusCode = String.fromCharCodes(data.sublist(i + 3, i + 5));
        return DoorLockResponse(statusCode: statusCode, rawData: data);
      }
    }

    return null;
  }

  /// 상태 조회 응답 파싱 → DoorLockStatus
  static DoorLockStatus? parseStatusResponse(Uint8List data) {
    final response = parseResponse(data);
    if (response == null) return null;

    return DoorLockStatus.fromCode(response.statusCode, data);
  }

  /// Hex 문자열을 바이트 배열로 변환
  static Uint8List hexToBytes(String hex) {
    final clean = hex.replaceAll(RegExp(r'[\s,]'), '').replaceAll('0x', '').replaceAll('0X', '');
    final bytes = <int>[];
    for (var i = 0; i + 1 < clean.length; i += 2) {
      bytes.add(int.parse(clean.substring(i, i + 2), radix: 16));
    }
    return Uint8List.fromList(bytes);
  }
}

class DoorLockResponse {
  final String statusCode;
  final Uint8List rawData;

  DoorLockResponse({required this.statusCode, required this.rawData});

  @override
  String toString() =>
      'DoorLockResponse(statusCode: $statusCode, raw: ${rawData.map((b) => b.toRadixString(16).padLeft(2, '0')).join(' ')})';
}

/// 잠금장치 상태 조회 결과
///
/// 상태코드: "00"=잠금해제(문닫힘), "01"=잠금(문닫힘), "10"=문열림
class DoorLockStatus {
  final String statusCode;
  final bool isLockOpen;
  final bool isDoorOpen;
  final String description;
  final Uint8List rawData;

  DoorLockStatus({
    required this.statusCode,
    required this.isLockOpen,
    required this.isDoorOpen,
    required this.description,
    required this.rawData,
  });

  static const _statusMap = {
    '00': (lock: true, door: false, desc: '잠금 해제 (문 닫힘)'),
    '01': (lock: false, door: false, desc: '잠금 (문 닫힘)'),
    '10': (lock: true, door: true, desc: '문 열림'),
  };

  factory DoorLockStatus.fromCode(String code, Uint8List rawData) {
    final info = _statusMap[code];
    return DoorLockStatus(
      statusCode: code,
      isLockOpen: info?.lock ?? false,
      isDoorOpen: info?.door ?? false,
      description: info?.desc ?? '알 수 없는 상태: $code',
      rawData: rawData,
    );
  }

  @override
  String toString() =>
      'DoorLockStatus(code: $statusCode, lock: ${isLockOpen ? "open" : "closed"}, door: ${isDoorOpen ? "open" : "closed"})';
}
