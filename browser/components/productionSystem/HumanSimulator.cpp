/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "HumanSimulator.h"

#include <random>

namespace mozilla::browser::production {

HumanTypingPlan HumanSimulator::BuildPlan(const std::string& input) {
  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_int_distribution<uint32_t> charDelay(50, 150);
  std::uniform_int_distribution<int> typoChance(1, 100);
  std::uniform_int_distribution<int> typoChar('a', 'z');

  HumanTypingPlan plan;
  plan.output.reserve(input.size() + 4);

  const bool injectTypo = !input.empty() && typoChance(gen) <= 5;
  const size_t typoPos = injectTypo ? static_cast<size_t>(gen() % input.size()) : 0;

  for (size_t i = 0; i < input.size(); ++i) {
    if (injectTypo && i == typoPos) {
      plan.output.push_back(static_cast<char>(typoChar(gen)));
      plan.delaysMs.push_back(charDelay(gen));
      plan.output.push_back('\b');
      plan.delaysMs.push_back(charDelay(gen));
      plan.typoSimulated = true;
    }
    plan.output.push_back(input[i]);
    plan.delaysMs.push_back(charDelay(gen));
  }

  return plan;
}

}  // namespace mozilla::browser::production
