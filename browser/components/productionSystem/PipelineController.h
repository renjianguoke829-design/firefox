/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_PipelineController_h
#define mozilla_browser_productionSystem_PipelineController_h

#include <atomic>
#include <string>

namespace mozilla::browser::production {

class PipelineController {
 public:
  PipelineController();
  ~PipelineController();

  bool Start(uint16_t port = 9997);
  void Stop();

 private:
  bool ForwardToPort(const std::string& payload, uint16_t port);

  std::atomic<bool> mRunning;
};

}  // namespace mozilla::browser::production

#endif
