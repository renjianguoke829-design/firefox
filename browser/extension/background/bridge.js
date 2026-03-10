importScripts("recorder.js");

const state = {
  projectMode: "marxist",
  recordingEnabled: false,
  currentPlatform: "unknown",
  stageName: "未开始",
  progress: "0/0",
  latestOutput: ""
};

async function getActiveTab() {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function sendToActiveTab(message) {
  const tab = await getActiveTab();
  if (!tab?.id) {
    return { ok: false, error: "No active tab" };
  }
  try {
    const response = await browser.tabs.sendMessage(tab.id, message);
    return response || { ok: true };
  } catch (error) {
    return { ok: false, error: String(error) };
  }
}

async function persistState() {
  await browser.storage.local.set({ sidebarState: state });
}

browser.runtime.onInstalled.addListener(persistState);

browser.runtime.onMessage.addListener((message, sender) => {
  if (message?.type === "SIDEBAR_GET_STATE") {
    return Promise.resolve({ ok: true, state });
  }

  if (message?.type === "SIDEBAR_SET_MODE") {
    state.projectMode = message.mode === "blank" ? "blank" : "marxist";
    persistState();
    return Promise.resolve({ ok: true, state });
  }

  if (message?.type === "SIDEBAR_SET_RECORDING") {
    state.recordingEnabled = Boolean(message.enabled);
    persistState();
    return Promise.resolve({ ok: true, state });
  }

  if (message?.type === "SIDEBAR_SET_STAGE") {
    if (typeof message.stageName === "string") {
      state.stageName = message.stageName;
    }
    if (typeof message.progress === "string") {
      state.progress = message.progress;
    }
    persistState();
    return Promise.resolve({ ok: true, state });
  }

  if (message?.type === "SIDEBAR_SEND_PROMPT") {
    return sendToActiveTab({
      type: "INJECT_PROMPT",
      prompt: message.prompt || "",
      projectMode: state.projectMode
    });
  }

  if (message?.type === "PLATFORM_DETECTED") {
    state.currentPlatform = message.platform || "unknown";
    persistState();
    browser.runtime.sendMessage({ type: "SIDEBAR_STATE_UPDATED", state });
    return Promise.resolve({ ok: true });
  }

  if (message?.type === "SIDEBAR_EXPORT_RECORDS") {
    return browser.runtime.sendMessage({ type: "RECORDER_EXPORT_JSON" });
  }

  if (message?.type === "AI_OUTPUT") {
    state.latestOutput = message.output || "";
    persistState();
    browser.runtime.sendMessage({ type: "SIDEBAR_STATE_UPDATED", state });
    return Promise.resolve({ ok: true });
  }

  return undefined;
});
