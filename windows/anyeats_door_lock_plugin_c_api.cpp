#include "include/anyeats_door_lock/anyeats_door_lock_plugin_c_api.h"

#include <flutter/plugin_registrar_windows.h>

#include "anyeats_door_lock_plugin.h"

void AnyeatsDoorLockPluginCApiRegisterWithRegistrar(
    FlutterDesktopPluginRegistrarRef registrar) {
  anyeats_door_lock::AnyeatsDoorLockPlugin::RegisterWithRegistrar(
      flutter::PluginRegistrarManager::GetInstance()
          ->GetRegistrar<flutter::PluginRegistrarWindows>(registrar));
}
