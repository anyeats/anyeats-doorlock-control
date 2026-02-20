import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'anyeats_door_lock_method_channel.dart';

abstract class AnyeatsDoorLockPlatform extends PlatformInterface {
  /// Constructs a AnyeatsDoorLockPlatform.
  AnyeatsDoorLockPlatform() : super(token: _token);

  static final Object _token = Object();

  static AnyeatsDoorLockPlatform _instance = MethodChannelAnyeatsDoorLock();

  /// The default instance of [AnyeatsDoorLockPlatform] to use.
  ///
  /// Defaults to [MethodChannelAnyeatsDoorLock].
  static AnyeatsDoorLockPlatform get instance => _instance;

  /// Platform-specific implementations should set this with their own
  /// platform-specific class that extends [AnyeatsDoorLockPlatform] when
  /// they register themselves.
  static set instance(AnyeatsDoorLockPlatform instance) {
    PlatformInterface.verifyToken(instance, _token);
    _instance = instance;
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('platformVersion() has not been implemented.');
  }
}
