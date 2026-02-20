import 'dart:typed_data';
import 'package:serial_port_win32/serial_port_win32.dart';
import 'door_lock_protocol.dart';

export 'door_lock_protocol.dart' show DoorLockResponse;

/// 잠금장치 시리얼 통신 컨트롤러
///
/// DLE-STX 프레임 프로토콜로 잠금장치를 제어합니다.
/// 시리얼 포트 통신은 [serial_port_win32] 패키지를 사용합니다.
class DoorLockController {
  SerialPort? _port;
  String _portName;
  final int _baudRate;
  final int _readTimeoutMs;

  DoorLockController({
    String port = 'COM2',
    int baudRate = 9600,
    int readTimeoutMs = 1000,
  })  : _portName = port,
        _baudRate = baudRate,
        _readTimeoutMs = readTimeoutMs;

  /// 현재 포트 이름
  String get portName => _portName;

  /// 연결 상태
  bool get isConnected => _port?.isOpened ?? false;

  /// 사용 가능한 COM 포트 목록
  static List<String> getAvailablePorts() {
    return SerialPort.getAvailablePorts();
  }

  /// 시리얼 포트에 연결
  bool connect({String? port}) {
    if (port != null) _portName = port;

    try {
      if (_port?.isOpened ?? false) {
        return true;
      }

      _port = SerialPort(
        _portName,
        openNow: true,
        ByteSize: 8,
        BaudRate: _baudRate,
        Parity: 0, // NOPARITY
        StopBits: 0, // ONESTOPBIT
        ReadIntervalTimeout: 50,
        ReadTotalTimeoutMultiplier: 10,
        ReadTotalTimeoutConstant: _readTimeoutMs,
      );

      // RTS/DTR 활성화
      _port!.setFlowControlSignal(SerialPort.SETDTR);
      _port!.setFlowControlSignal(SerialPort.SETRTS);

      return _port!.isOpened;
    } catch (e) {
      print('[DoorLock] 연결 실패: $e');
      return false;
    }
  }

  /// 시리얼 포트 연결 해제
  void disconnect() {
    _port?.close();
    _port = null;
  }

  /// 잠금장치 열기 (DLE-STX: 10 02 [id] 1B 31 FF 10 03)
  Future<bool> openLock({int deviceId = 1}) async {
    final frame = DoorLockProtocol.buildOpenFrame(deviceId);
    return _sendCommand(frame);
  }

  /// 잠금장치 닫기 (DLE-STX: 10 02 [id] 1B 30 FF 10 03)
  Future<bool> closeLock({int deviceId = 1}) async {
    final frame = DoorLockProtocol.buildCloseFrame(deviceId);
    return _sendCommand(frame);
  }

  /// Raw hex 문자열 직접 전송 (프로토콜 실험용)
  Future<bool> sendRaw(String hexString) async {
    try {
      final data = DoorLockProtocol.hexToBytes(hexString);
      return _sendCommand(data);
    } catch (e) {
      print('[DoorLock] Hex 파싱 실패: $e');
      return false;
    }
  }

  /// 명령 전송 및 응답 대기
  Future<bool> _sendCommand(Uint8List command) async {
    if (!connect()) return false;

    try {
      // RX 버퍼 비우기 (짧은 타임아웃으로 읽기)
      try {
        await _port!.readBytes(64, timeout: const Duration(milliseconds: 50));
      } catch (_) {}

      // 명령 전송
      await _port!.writeBytesFromUint8List(command);
      print('[DoorLock] 전송: ${_hexString(command)}');

      // 응답 읽기 시도
      try {
        final response = await _port!.readBytes(
          64,
          timeout: Duration(milliseconds: _readTimeoutMs),
        );
        if (response.isNotEmpty) {
          final parsed = DoorLockProtocol.parseResponse(response);
          if (parsed != null) {
            print('[DoorLock] 응답: $parsed');
          } else {
            print('[DoorLock] 응답 (미파싱): ${_hexString(response)}');
          }
        }
      } catch (_) {
        print('[DoorLock] 응답 없음 (타임아웃)');
      }

      return true;
    } catch (e) {
      print('[DoorLock] 전송 실패: $e');
      return false;
    }
  }

  static String _hexString(Uint8List data) {
    return data
        .map((b) => b.toRadixString(16).padLeft(2, '0').toUpperCase())
        .join(' ');
  }
}
