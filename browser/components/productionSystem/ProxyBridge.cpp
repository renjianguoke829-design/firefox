/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "ProxyBridge.h"

#include <cstdlib>
#include <fstream>

#include "mozilla/Preferences.h"
#include "prnetdb.h"
#include "prio.h"

namespace mozilla::browser::production {

namespace {

bool ExtractJsonString(const std::string& json, const char* key,
                       std::string& out) {
  const std::string token = std::string{"\""} + key + "\"";
  const size_t keyPos = json.find(token);
  if (keyPos == std::string::npos) {
    return false;
  }
  size_t colon = json.find(':', keyPos + token.size());
  if (colon == std::string::npos) {
    return false;
  }
  size_t firstQuote = json.find('"', colon + 1);
  if (firstQuote == std::string::npos) {
    return false;
  }
  size_t secondQuote = json.find('"', firstQuote + 1);
  if (secondQuote == std::string::npos) {
    return false;
  }
  out = json.substr(firstQuote + 1, secondQuote - firstQuote - 1);
  return true;
}

}  // namespace

ProxyBridge::ProxyBridge() : mRunning(false) {}

ProxyBridge::~ProxyBridge() { Stop(); }

bool ProxyBridge::Start(uint16_t updatePort, const char* configPath) {
  ProxyConfig config;
  if (LoadConfigFromFile(configPath, config)) {
    ApplyConfig(config);
  }

  if (mRunning.exchange(true)) {
    return true;
  }

  return ListenForUpdates(updatePort);
}

void ProxyBridge::Stop() { mRunning = false; }

bool ProxyBridge::LoadConfigFromFile(const char* configPath,
                                     ProxyConfig& outConfig) {
  std::ifstream in(configPath);
  if (!in.is_open()) {
    return false;
  }

  std::string line;
  while (std::getline(in, line)) {
    const size_t sep = line.find('=');
    if (sep == std::string::npos) {
      continue;
    }
    const std::string key = line.substr(0, sep);
    const std::string value = line.substr(sep + 1);
    if (key == "enabled") {
      outConfig.enabled = (value == "1" || value == "true");
    } else if (key == "host") {
      outConfig.host = value;
    } else if (key == "port") {
      outConfig.port = static_cast<uint16_t>(std::atoi(value.c_str()));
    } else if (key == "scheme") {
      outConfig.scheme = value;
    }
  }

  return true;
}

bool ProxyBridge::ApplyConfig(const ProxyConfig& config) {
  const int32_t proxyType = config.enabled ? 1 : 0;
  (void)Preferences::SetInt("network.proxy.type", proxyType);

  if (!config.enabled || config.host.empty() || config.port == 0) {
    return true;
  }

  if (config.scheme == "socks") {
    (void)Preferences::SetCString("network.proxy.socks", config.host.c_str());
    (void)Preferences::SetInt("network.proxy.socks_port", config.port);
  } else {
    (void)Preferences::SetCString("network.proxy.http", config.host.c_str());
    (void)Preferences::SetInt("network.proxy.http_port", config.port);
    (void)Preferences::SetCString("network.proxy.ssl", config.host.c_str());
    (void)Preferences::SetInt("network.proxy.ssl_port", config.port);
  }

  return true;
}

bool ProxyBridge::ListenForUpdates(uint16_t port) {
  PRFileDesc* server = PR_OpenTCPSocket(PR_AF_INET);
  if (!server) {
    return false;
  }

  PRNetAddr addr;
  PR_InitializeNetAddr(PR_IpAddrLoopback, port, &addr);
  if (PR_Bind(server, &addr) != PR_SUCCESS || PR_Listen(server, 16) != PR_SUCCESS) {
    PR_Close(server);
    return false;
  }

  while (mRunning) {
    PRFileDesc* client = PR_Accept(server, nullptr, PR_INTERVAL_NO_TIMEOUT);
    if (!client) {
      continue;
    }

    std::string payload;
    char buffer[2048];
    while (true) {
      int32_t rv = PR_Recv(client, buffer, sizeof(buffer), 0, PR_INTERVAL_NO_TIMEOUT);
      if (rv <= 0) {
        break;
      }
      payload.append(buffer, static_cast<size_t>(rv));
    }
    PR_Close(client);

    ProxyConfig config;
    if (ParseJsonUpdate(payload, config)) {
      ApplyConfig(config);
    }
  }

  PR_Close(server);
  return true;
}

bool ProxyBridge::ParseJsonUpdate(const std::string& payload,
                                  ProxyConfig& outConfig) {
  std::string enabled;
  std::string port;
  ExtractJsonString(payload, "enabled", enabled);
  ExtractJsonString(payload, "host", outConfig.host);
  ExtractJsonString(payload, "port", port);
  ExtractJsonString(payload, "scheme", outConfig.scheme);

  outConfig.enabled = (enabled == "1" || enabled == "true");
  if (!port.empty()) {
    outConfig.port = static_cast<uint16_t>(std::atoi(port.c_str()));
  }

  return true;
}

}  // namespace mozilla::browser::production
