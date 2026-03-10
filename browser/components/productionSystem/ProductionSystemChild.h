/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_ProductionSystemChild_h
#define mozilla_browser_productionSystem_ProductionSystemChild_h

#include <string>

namespace mozilla::browser::production {

class ProductionSystemChild {
 public:
  static bool ValidateInjectRequest(const std::string& platform,
                                    const std::string& text);
};

}  // namespace mozilla::browser::production

#endif
