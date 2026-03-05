/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_ProxyBridge_h
#define mozilla_browser_productionSystem_ProxyBridge_h

#include <atomic>
#include <cstdint>
#include <string>

namespace mozilla::browser::production {

struct ProxyConfig {
  bool enabled = false;
  std::string host;
  uint16_t port = 0;
  std::string scheme = "http";
};

class ProxyBridge {
 public:
  ProxyBridge();
  ~ProxyBridge();

  bool Start(uint16_t updatePort = 9996,
             const char* configPath = "/tmp/production_proxy.conf");
  void Stop();

 private:
  bool LoadConfigFromFile(const char* configPath, ProxyConfig& outConfig);
  bool ApplyConfig(const ProxyConfig& config);
  bool ListenForUpdates(uint16_t port);
  bool ParseJsonUpdate(const std::string& payload, ProxyConfig& outConfig);

  std::atomic<bool> mRunning;
};

}  // namespace mozilla::browser::production

#endif
