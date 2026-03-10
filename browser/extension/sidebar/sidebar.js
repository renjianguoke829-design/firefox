const stageEl = document.getElementById("stage");
const progressEl = document.getElementById("progress");
const platformEl = document.getElementById("platform");
const outputEl = document.getElementById("output");
const promptEl = document.getElementById("prompt");
const recordingEl = document.getElementById("recording");

function renderState(state) {
  stageEl.textContent = `当前工序：${state.stageName || "未开始"}`;
  progressEl.textContent = `进度：${state.progress || "0/0"}`;
  platformEl.textContent = `平台：${state.currentPlatform || "unknown"}`;
  outputEl.textContent = state.latestOutput || "暂无输出";
  recordingEl.checked = Boolean(state.recordingEnabled);
}

async function requestState() {
  const response = await browser.runtime.sendMessage({ type: "SIDEBAR_GET_STATE" });
  if (response?.ok) {
    renderState(response.state);
  }
}

async function sendPrompt() {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    return;
  }
  const response = await browser.runtime.sendMessage({ type: "SIDEBAR_SEND_PROMPT", prompt });
  if (response?.ok) {
    promptEl.value = "";
  }
}

async function setMode(mode) {
  await browser.runtime.sendMessage({ type: "SIDEBAR_SET_MODE", mode });
  await requestState();
}

async function exportRecords() {
  const response = await browser.runtime.sendMessage({ type: "SIDEBAR_EXPORT_RECORDS" });
  if (!response?.ok || !Array.isArray(response.data)) {
    return;
  }

  const payload = JSON.stringify(response.data, null, 2);
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  await browser.downloads.download({
    url,
    filename: `ai-dialog-records-${Date.now()}.json`,
    saveAs: true
  });
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

recordingEl.addEventListener("change", async (event) => {
  await browser.runtime.sendMessage({
    type: "SIDEBAR_SET_RECORDING",
    enabled: event.target.checked
  });
});

document.getElementById("sendPrompt").addEventListener("click", sendPrompt);
document.getElementById("syncStage").addEventListener("click", requestState);
document.getElementById("modeMarxist").addEventListener("click", () => setMode("marxist"));
document.getElementById("modeBlank").addEventListener("click", () => setMode("blank"));
document.getElementById("exportJson").addEventListener("click", exportRecords);

browser.runtime.onMessage.addListener((message) => {
  if (message?.type === "SIDEBAR_STATE_UPDATED") {
    renderState(message.state || {});
  }
});

requestState();
