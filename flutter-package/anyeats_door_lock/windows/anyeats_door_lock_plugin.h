#ifndef FLUTTER_PLUGIN_ANYEATS_DOOR_LOCK_PLUGIN_H_
#define FLUTTER_PLUGIN_ANYEATS_DOOR_LOCK_PLUGIN_H_

#include <flutter/method_channel.h>
#include <flutter/plugin_registrar_windows.h>

#include <memory>

namespace anyeats_door_lock {

class AnyeatsDoorLockPlugin : public flutter::Plugin {
 public:
  static void RegisterWithRegistrar(flutter::PluginRegistrarWindows *registrar);

  AnyeatsDoorLockPlugin();

  virtual ~AnyeatsDoorLockPlugin();

  // Disallow copy and assign.
  AnyeatsDoorLockPlugin(const AnyeatsDoorLockPlugin&) = delete;
  AnyeatsDoorLockPlugin& operator=(const AnyeatsDoorLockPlugin&) = delete;

  // Called when a method is called on this plugin's channel from Dart.
  void HandleMethodCall(
      const flutter::MethodCall<flutter::EncodableValue> &method_call,
      std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
};

}  // namespace anyeats_door_lock

#endif  // FLUTTER_PLUGIN_ANYEATS_DOOR_LOCK_PLUGIN_H_
