import 'package:flutter_test/flutter_test.dart';
import 'package:anyeats_door_lock/anyeats_door_lock.dart';
import 'package:anyeats_door_lock/anyeats_door_lock_platform_interface.dart';
import 'package:anyeats_door_lock/anyeats_door_lock_method_channel.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

class MockAnyeatsDoorLockPlatform
    with MockPlatformInterfaceMixin
    implements AnyeatsDoorLockPlatform {

  @override
  Future<String?> getPlatformVersion() => Future.value('42');
}

void main() {
  final AnyeatsDoorLockPlatform initialPlatform = AnyeatsDoorLockPlatform.instance;

  test('$MethodChannelAnyeatsDoorLock is the default instance', () {
    expect(initialPlatform, isInstanceOf<MethodChannelAnyeatsDoorLock>());
  });

  test('getPlatformVersion', () async {
    AnyeatsDoorLock anyeatsDoorLockPlugin = AnyeatsDoorLock();
    MockAnyeatsDoorLockPlatform fakePlatform = MockAnyeatsDoorLockPlatform();
    AnyeatsDoorLockPlatform.instance = fakePlatform;

    expect(await anyeatsDoorLockPlugin.getPlatformVersion(), '42');
  });
}
