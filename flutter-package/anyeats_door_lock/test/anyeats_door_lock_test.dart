import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:anyeats_door_lock/src/door_lock_protocol.dart';

void main() {
  group('DoorLockProtocol', () {
    test('buildOpenFrame generates correct DLE-STX frame', () {
      final frame = DoorLockProtocol.buildOpenFrame(1);
      expect(frame, equals(Uint8List.fromList(
        [0x10, 0x02, 0x01, 0x1B, 0x31, 0xFF, 0x10, 0x03],
      )));
    });

    test('buildCloseFrame generates correct DLE-STX frame', () {
      final frame = DoorLockProtocol.buildCloseFrame(1);
      expect(frame, equals(Uint8List.fromList(
        [0x10, 0x02, 0x01, 0x1B, 0x30, 0xFF, 0x10, 0x03],
      )));
    });

    test('buildOpenFrame with different deviceId', () {
      final frame = DoorLockProtocol.buildOpenFrame(2);
      expect(frame[2], equals(2));
    });

    test('parseResponse parses valid response', () {
      // SOH + '0' + '0' + DLE + ETX
      final data = Uint8List.fromList([0x01, 0x30, 0x30, 0x10, 0x03]);
      final response = DoorLockProtocol.parseResponse(data);
      expect(response, isNotNull);
      expect(response!.statusCode, equals('00'));
    });

    test('parseResponse returns null for invalid data', () {
      final data = Uint8List.fromList([0x00, 0x30, 0x30, 0x10, 0x03]);
      expect(DoorLockProtocol.parseResponse(data), isNull);
    });

    test('parseResponse returns null for short data', () {
      final data = Uint8List.fromList([0x01, 0x30]);
      expect(DoorLockProtocol.parseResponse(data), isNull);
    });

    test('hexToBytes converts hex string correctly', () {
      final bytes = DoorLockProtocol.hexToBytes('10 02 01 1B 31 FF 10 03');
      expect(bytes, equals(Uint8List.fromList(
        [0x10, 0x02, 0x01, 0x1B, 0x31, 0xFF, 0x10, 0x03],
      )));
    });
  });
}
