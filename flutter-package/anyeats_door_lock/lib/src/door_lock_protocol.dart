import 'dart:typed_data';

/// DLE-STX 프레임 프로토콜 (제조사 시리얼 모니터 캡처 IMG_0778에서 확인)
///
/// 명령 프레임: DLE(10) STX(02) [DeviceID] ESC(1B) [Cmd] FF DLE(10) ETX(03)
/// - Open:  10 02 01 1B 31 FF 10 03  (Cmd='1'=0x31)
/// - Close: 10 02 01 1B 30 FF 10 03  (Cmd='0'=0x30)
///
/// 응답 프레임: SOH(01) [ASCII 2bytes] DLE(10) ETX(03)
class DoorLockProtocol {
  static const int dle = 0x10;
  static const int stx = 0x02;
  static const int etx = 0x03;
  static const int esc = 0x1B;
  static const int soh = 0x01;
  static const int fixedByte = 0xFF;

  /// Open 명령 프레임 생성
  static Uint8List buildOpenFrame(int deviceId) {
    return _buildFrame(deviceId, 0x31); // '1'
  }

  /// Close 명령 프레임 생성
  static Uint8List buildCloseFrame(int deviceId) {
    return _buildFrame(deviceId, 0x30); // '0'
  }

  /// DLE-STX 프레임 생성
  static Uint8List _buildFrame(int deviceId, int command) {
    return Uint8List.fromList([
      dle, stx, // 프레임 시작
      deviceId, // 장치 ID
      esc, // ESC
      command, // 명령 ('1' or '0')
      fixedByte, // 고정값 FF
      dle, etx, // 프레임 끝
    ]);
  }

  /// 응답 파싱: SOH(01) + ASCII 2bytes + DLE(10) + ETX(03)
  static DoorLockResponse? parseResponse(Uint8List data) {
    if (data.length < 5) return null;
    if (data[0] != soh) return null;
    if (data[3] != dle || data[4] != etx) return null;

    final statusCode = String.fromCharCodes(data.sublist(1, 3));
    return DoorLockResponse(
      statusCode: statusCode,
      rawData: data,
    );
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
