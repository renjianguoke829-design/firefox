/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 2 -*- */

#include "PipelineController.h"

#include <string>
#include <vector>

#include "nsPrintfCString.h"
#include "prnetdb.h"
#include "prio.h"
#include "prtime.h"

namespace mozilla::browser::production {

namespace {

struct VariantPlan {
  const char* name;
  const char* project;
  const char* prompt;
};

struct StagePlan {
  const char* stage;
  VariantPlan marxist;
  VariantPlan control;
};

const StagePlan kPipelinePlan[] = {
    {"数据入口",
     {"marxist", "马列主义版", "按阶级矛盾和生产关系分类数据，输出核心对立面。"},
     {"control", "挑战对照版", "按主流叙事与表面信息分类数据，输出热门叙事路径。"}},
    {"提炼",
     {"marxist", "马列主义版", "提炼阶级矛盾核心事实，聚焦生产关系与物质利益。"},
     {"control", "挑战对照版", "提炼表面信息核心，聚焦观点和事件表象。"}},
    {"决策",
     {"marxist", "马列主义版", "从生产关系角度给出决策方向与执行顺序。"},
     {"control", "挑战对照版", "从常规逻辑角度给出决策方向与执行顺序。"}},
    {"生产",
     {"marxist", "马列主义版", "生成马列框架内容并标注矛盾链条。"},
     {"control", "挑战对照版", "生成对照内容并强调叙事可读性。"}},
    {"审查",
     {"marxist", "马列主义版", "审查质量与框架一致性，检查四问覆盖。"},
     {"control", "挑战对照版", "审查逻辑与表达质量，检查可传播性。"}},
};

bool ContainsDecisionAssistantTrigger(const std::string& payload) {
  return payload.find("decision_assistant") != std::string::npos ||
         payload.find("决策助手") != std::string::npos;
}

nsCString BuildCommand(const StagePlan& stage, const VariantPlan& plan,
                       const std::string& input) {
  nsCString escapedInput(input.c_str());
  escapedInput.ReplaceSubstring("\"", "\\\"");
  return nsPrintfCString(
      "{\"action\":\"input\",\"selector\":\"div[contenteditable],textarea\","
      "\"platform\":\"pipeline\",\"text\":\"[%s-%s] %s 输入:%s\"}",
      stage.stage, plan.project, plan.prompt, escapedInput.get());
}

nsCString BuildPipelineLog(const StagePlan& stage, const VariantPlan& plan,
                           const char* status, bool requireConfirm,
                           const std::string& input) {
  const auto ts = static_cast<long long>(PR_Now() / PR_USEC_PER_MSEC);
  nsCString escapedInput(input.c_str());
  escapedInput.ReplaceSubstring("\"", "\\\"");
  return nsPrintfCString(
      "{\"table\":\"pipeline_logs\",\"pipeline_name\":\"完整生产流水线\","
      "\"stage\":\"%s\",\"ai_model\":\"%s\",\"project_name\":\"%s\","
      "\"input\":\"%s\",\"output\":\"%s\",\"duration_ms\":0,"
      "\"quality_score\":0,\"requires_confirm\":%s,\"created_at\":%lld}\n",
      stage.stage, plan.name, plan.project, escapedInput.get(), status,
      requireConfirm ? "true" : "false", ts);
}

nsCString BuildDecisionAssistantLog(const std::string& input) {
  const auto ts = static_cast<long long>(PR_Now() / PR_USEC_PER_MSEC);
  nsCString escapedInput(input.c_str());
  escapedInput.ReplaceSubstring("\"", "\\\"");
  return nsPrintfCString(
      "{\"table\":\"pipeline_logs\",\"pipeline_name\":\"第11个项目\","
      "\"stage\":\"决策助手\",\"ai_model\":\"decision-assistant\","
      "\"project_name\":\"独立会话\",\"input\":\"%s\","
      "\"output\":\"调用决策数据库\",\"duration_ms\":0,"
      "\"quality_score\":0,\"requires_confirm\":false,\"created_at\":%lld}\n",
      escapedInput.get(), ts);
}

}  // namespace

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
      const auto rv =
          PR_Recv(client, buffer, sizeof(buffer), 0, PR_INTERVAL_NO_TIMEOUT);
      if (rv <= 0) {
        break;
      }
      payload.append(buffer, static_cast<size_t>(rv));
    }
    PR_Close(client);

    if (payload.empty()) {
      continue;
    }

    for (const auto& stage : kPipelinePlan) {
      const nsCString marxistCommand = BuildCommand(stage, stage.marxist, payload);
      const nsCString controlCommand = BuildCommand(stage, stage.control, payload);
      ForwardToPort(std::string(marxistCommand.get()), 9998);
      ForwardToPort(std::string(controlCommand.get()), 9998);

      ForwardToPort(
          std::string(BuildPipelineLog(stage, stage.marxist, "stage_completed",
                                       true, payload)
                          .get()),
          9999);
      ForwardToPort(
          std::string(BuildPipelineLog(stage, stage.control, "stage_completed",
                                       true, payload)
                          .get()),
          9999);
    }

    if (ContainsDecisionAssistantTrigger(payload)) {
      ForwardToPort(std::string(BuildDecisionAssistantLog(payload).get()), 9999);
    }
  }

  PR_Close(server);
  return true;
}

void PipelineController::Stop() { mRunning = false; }

bool PipelineController::ForwardToPort(const std::string& payload,
                                       uint16_t port) {
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
