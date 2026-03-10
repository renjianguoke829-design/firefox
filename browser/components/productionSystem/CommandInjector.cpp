/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "CommandInjector.h"

#include "HumanSimulator.h"
#include "ProductionSystemParent.h"

#include <algorithm>
#include <vector>

#include "prnetdb.h"
#include "prio.h"
#include "prthread.h"

namespace mozilla::browser::production {

CommandInjector::CommandInjector() : mRunning(false) {}

CommandInjector::~CommandInjector() { Stop(); }

bool CommandInjector::Start(uint16_t port) {
  if (mRunning.exchange(true)) {
    return true;
  }

  while (mRunning) {
    InjectionCommand command;
    if (!ReadOneCommand(command)) {
      break;
    }
    HandleCommand(command);
  }

  return true;
}

void CommandInjector::Stop() { mRunning = false; }

bool CommandInjector::ReadOneCommand(InjectionCommand& outCommand) {
  PRFileDesc* server = PR_OpenTCPSocket(PR_AF_INET);
  if (!server) {
    return false;
  }

  PRNetAddr addr;
  PR_InitializeNetAddr(PR_IpAddrLoopback, 9998, &addr);
  if (PR_Bind(server, &addr) != PR_SUCCESS || PR_Listen(server, 16) != PR_SUCCESS) {
    PR_Close(server);
    return false;
  }

  PRFileDesc* client = PR_Accept(server, nullptr, PR_INTERVAL_NO_TIMEOUT);
  PR_Close(server);
  if (!client) {
    return false;
  }

  std::string payload;
  char buffer[4096];
  while (true) {
    const auto rv = PR_Recv(client, buffer, sizeof(buffer), 0, PR_INTERVAL_NO_TIMEOUT);
    if (rv <= 0) {
      break;
    }
    payload.append(buffer, static_cast<size_t>(rv));
  }
  PR_Close(client);

  if (payload.empty()) {
    return false;
  }

  if (!ExtractJsonField(payload, "action", outCommand.action) ||
      !ExtractJsonField(payload, "text", outCommand.text) ||
      !ExtractJsonField(payload, "platform", outCommand.platform)) {
    return false;
  }

  ExtractJsonField(payload, "selector", outCommand.selector);
  return true;
}

bool CommandInjector::HandleCommand(const InjectionCommand& command) {
  if (command.action != "input" && command.action != "inject_prompt") {
    return false;
  }

  HumanTypingPlan plan = HumanSimulator::BuildPlan(command.text);
  std::vector<int> delays;
  delays.reserve(plan.delaysMs.size());
  for (uint32_t delay : plan.delaysMs) {
    delays.push_back(static_cast<int>(delay));
  }
  ProductionSystemParent::TriggerInject(command.platform, command.text, delays);

  return !plan.output.empty();
}

bool CommandInjector::ExtractJsonField(const std::string& json, const char* key,
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

}  // namespace mozilla::browser::production
