/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_CommandInjector_h
#define mozilla_browser_productionSystem_CommandInjector_h

#include <atomic>
#include <string>

namespace mozilla::browser::production {

struct InjectionCommand {
  std::string action;
  std::string selector;
  std::string text;
  std::string platform;
};

class CommandInjector {
 public:
  CommandInjector();
  ~CommandInjector();

  bool Start(uint16_t port = 9998);
  void Stop();

 private:
  bool ReadOneCommand(InjectionCommand& outCommand);
  bool HandleCommand(const InjectionCommand& command);
  static bool ExtractJsonField(const std::string& json, const char* key,
                               std::string& out);

  std::atomic<bool> mRunning;
};

}  // namespace mozilla::browser::production

#endif
