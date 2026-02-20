
import 'anyeats_door_lock_platform_interface.dart';

class AnyeatsDoorLock {
  Future<String?> getPlatformVersion() {
    return AnyeatsDoorLockPlatform.instance.getPlatformVersion();
  }
}
