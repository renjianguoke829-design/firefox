/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#ifndef mozilla_browser_productionSystem_ProductionSystemParent_h
#define mozilla_browser_productionSystem_ProductionSystemParent_h

#include <string>
#include <vector>

namespace mozilla::browser::production {

class ProductionSystemParent {
 public:
  static void TriggerInject(const std::string& platform,
                            const std::string& text,
                            const std::vector<int>& delays);
};

}  // namespace mozilla::browser::production

#endif
