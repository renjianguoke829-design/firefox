/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_HumanSimulator_h
#define mozilla_browser_productionSystem_HumanSimulator_h

#include <string>
#include <vector>

namespace mozilla::browser::production {

struct HumanTypingPlan {
  std::string output;
  std::vector<uint32_t> delaysMs;
  bool typoSimulated = false;
};

class HumanSimulator {
 public:
  static HumanTypingPlan BuildPlan(const std::string& input);
};

}  // namespace mozilla::browser::production

#endif
