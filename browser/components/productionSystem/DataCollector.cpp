/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include <cstdlib>
#include <string>

namespace mozilla::browser::production {

namespace {

bool DomainEndsWith(const std::string& domain, const char* suffix) {
  const std::string s(suffix);
  if (domain.size() < s.size()) {
    return false;
  }
  return domain.compare(domain.size() - s.size(), s.size(), s) == 0;
}

}  // namespace

class DataCollector {
 public:
  DataCollector() {
    const char* v = std::getenv("BROWSER_VARIANT");
    if (v) {
      mVariant = v;
    }
  }

  bool IsPriorityDomain(const std::string& domain) const {
    if (mVariant == "international") {
      return DomainEndsWith(domain, "claude.ai") || DomainEndsWith(domain, "grok.com") ||
             DomainEndsWith(domain, "gemini.google.com") ||
             DomainEndsWith(domain, "reddit.com") || DomainEndsWith(domain, "twitter.com") ||
             DomainEndsWith(domain, "huggingface.co");
    }

    return DomainEndsWith(domain, "weibo.com") || DomainEndsWith(domain, "zhihu.com") ||
           DomainEndsWith(domain, "bilibili.com") || DomainEndsWith(domain, "douyin.com") ||
           DomainEndsWith(domain, "baidu.com") || DomainEndsWith(domain, "kimi.moonshot.cn");
  }

 private:
  std::string mVariant = "domestic";
};

}  // namespace mozilla::browser::production
