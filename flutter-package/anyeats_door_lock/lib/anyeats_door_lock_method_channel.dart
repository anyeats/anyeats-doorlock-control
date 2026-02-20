import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'anyeats_door_lock_platform_interface.dart';

/// An implementation of [AnyeatsDoorLockPlatform] that uses method channels.
class MethodChannelAnyeatsDoorLock extends AnyeatsDoorLockPlatform {
  /// The method channel used to interact with the native platform.
  @visibleForTesting
  final methodChannel = const MethodChannel('anyeats_door_lock');

  @override
  Future<String?> getPlatformVersion() async {
    final version = await methodChannel.invokeMethod<String>('getPlatformVersion');
    return version;
  }
}
