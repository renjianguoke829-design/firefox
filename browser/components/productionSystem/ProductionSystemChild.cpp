/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "ProductionSystemChild.h"

namespace mozilla::browser::production {

bool ProductionSystemChild::ValidateInjectRequest(const std::string& platform,
                                                  const std::string& text) {
  return !platform.empty() && !text.empty();
}

}  // namespace mozilla::browser::production
