/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "ProductionSystemParent.h"

#include "mozilla/Components.h"
#include "nsIObserverService.h"
#include "nsPrintfCString.h"

namespace mozilla::browser::production {

namespace {

nsCString EscapeJson(const std::string& value) {
  nsCString out(value.c_str());
  out.ReplaceSubstring("\\", "\\\\");
  out.ReplaceSubstring("\"", "\\\"");
  return out;
}

}  // namespace

void ProductionSystemParent::TriggerInject(const std::string& platform,
                                           const std::string& text,
                                           const std::vector<int>& delays) {
  nsAutoCString delaysCsv;
  for (size_t i = 0; i < delays.size(); ++i) {
    if (i) {
      delaysCsv.Append(',');
    }
    delaysCsv.AppendInt(delays[i]);
  }

  const nsCString escapedPlatform = EscapeJson(platform);
  const nsCString escapedText = EscapeJson(text);
  nsAutoCString payload = nsPrintfCString(
      "{\"platform\":\"%s\",\"text\":\"%s\",\"delays\":\"%s\"}",
      escapedPlatform.get(), escapedText.get(), delaysCsv.get());

  nsCOMPtr<nsIObserverService> observerService =
      mozilla::components::Observer::Service();
  if (!observerService) {
    return;
  }

  observerService->NotifyObservers(nullptr, "production-system-inject",
                                   NS_ConvertUTF8toUTF16(payload).get());
}

}  // namespace mozilla::browser::production
