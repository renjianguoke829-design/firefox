/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "PipelineController.h"

#include "prnetdb.h"
#include "prio.h"

namespace mozilla::browser::production {

PipelineController::PipelineController() : mRunning(false) {}

PipelineController::~PipelineController() { Stop(); }

bool PipelineController::Start(uint16_t port) {
  if (mRunning.exchange(true)) {
    return true;
  }

  PRFileDesc* server = PR_OpenTCPSocket(PR_AF_INET);
  if (!server) {
    mRunning = false;
    return false;
  }

  PRNetAddr addr;
  PR_InitializeNetAddr(PR_IpAddrLoopback, port, &addr);
  if (PR_Bind(server, &addr) != PR_SUCCESS || PR_Listen(server, 16) != PR_SUCCESS) {
    PR_Close(server);
    mRunning = false;
    return false;
  }

  while (mRunning) {
    PRFileDesc* client = PR_Accept(server, nullptr, PR_INTERVAL_NO_TIMEOUT);
    if (!client) {
      continue;
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

    if (!payload.empty()) {
      ForwardToPort(payload, 9998);
      ForwardToPort(payload, 9999);
    }
  }

  PR_Close(server);
  return true;
}

void PipelineController::Stop() { mRunning = false; }

bool PipelineController::ForwardToPort(const std::string& payload, uint16_t port) {
  PRFileDesc* fd = PR_OpenTCPSocket(PR_AF_INET);
  if (!fd) {
    return false;
  }

  PRNetAddr addr;
  PR_InitializeNetAddr(PR_IpAddrLoopback, port, &addr);
  if (PR_Connect(fd, &addr, PR_MillisecondsToInterval(100)) != PR_SUCCESS) {
    PR_Close(fd);
    return false;
  }

  const auto sent = PR_Send(fd, payload.data(), payload.size(), 0,
                            PR_MillisecondsToInterval(100));
  PR_Close(fd);
  return sent > 0;
}

}  // namespace mozilla::browser::production
