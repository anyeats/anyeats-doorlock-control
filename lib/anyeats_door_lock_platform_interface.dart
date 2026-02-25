import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'anyeats_door_lock_method_channel.dart';

abstract class AnyeatsDoorLockPlatform extends PlatformInterface {
  AnyeatsDoorLockPlatform() : super(token: _token);

  static final Object _token = Object();

  static AnyeatsDoorLockPlatform _instance = MethodChannelAnyeatsDoorLock();

  static AnyeatsDoorLockPlatform get instance => _instance;

  static set instance(AnyeatsDoorLockPlatform instance) {
    PlatformInterface.verifyToken(instance, _token);
    _instance = instance;
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('getPlatformVersion() has not been implemented.');
  }
}
