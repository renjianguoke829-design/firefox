const AI_HOSTS = new Set([
  "claude.ai",
  "grok.com",
  "gemini.google.com",
  "chat.deepseek.com",
  "kimi.moonshot.cn"
]);

const NATIVE_HOST = "production_system_native";
const conversationState = new Map();
const records = [];

function normalizePlatform(hostname) {
  if (hostname.includes("claude.ai")) return "Claude";
  if (hostname.includes("grok.com")) return "Grok";
  if (hostname.includes("gemini.google.com")) return "Gemini";
  if (hostname.includes("chat.deepseek.com")) return "DeepSeek";
  if (hostname.includes("kimi.moonshot.cn")) return "Kimi";
  return "unknown";
}

function parseJsonSafely(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function conversationIdFromUrl(url) {
  try {
    const parsed = new URL(url);
    return (
      parsed.searchParams.get("conversation_id") ||
      parsed.searchParams.get("conversationId") ||
      parsed.searchParams.get("id") ||
      parsed.pathname.split("/").filter(Boolean).pop() ||
      "unknown"
    );
  } catch {
    return "unknown";
  }
}

function extractInput(bodyText) {
  const parsed = parseJsonSafely(bodyText);
  if (!parsed) return bodyText;

  if (typeof parsed.prompt === "string") return parsed.prompt;
  if (typeof parsed.input === "string") return parsed.input;
  if (typeof parsed.query === "string") return parsed.query;

  if (Array.isArray(parsed.messages)) {
    const userMessage = parsed.messages
      .slice()
      .reverse()
      .find((m) => m?.role === "user");
    if (typeof userMessage?.content === "string") return userMessage.content;
    if (Array.isArray(userMessage?.content)) {
      return userMessage.content.map((part) => part?.text || "").join("\n").trim();
    }
  }

  return bodyText;
}

function extractOutput(bodyText) {
  const parsed = parseJsonSafely(bodyText);
  if (!parsed) return bodyText;

  if (typeof parsed.output === "string") return parsed.output;
  if (typeof parsed.response === "string") return parsed.response;
  if (typeof parsed.text === "string") return parsed.text;

  if (Array.isArray(parsed.choices) && parsed.choices[0]?.message?.content) {
    return parsed.choices[0].message.content;
  }

  if (Array.isArray(parsed.content)) {
    return parsed.content.map((item) => item?.text || "").join("\n").trim();
  }

  return bodyText;
}

async function writeNativeRecord(record) {
  try {
    await browser.runtime.sendNativeMessage(NATIVE_HOST, {
      type: "record_ai_dialog",
      payload: record
    });
    return true;
  } catch {
    return false;
  }
}

async function persistRecord(record) {
  records.push(record);
  await browser.storage.local.set({ aiRecords: records.slice(-1000) });
  await writeNativeRecord(record);
}

function shouldTrack(url) {
  try {
    const parsed = new URL(url);
    return [...AI_HOSTS].some((host) => parsed.hostname === host || parsed.hostname.endsWith(`.${host}`));
  } catch {
    return false;
  }
}

function decodeRequestBody(requestBody) {
  if (!requestBody?.raw?.length) return "";
  const chunks = requestBody.raw
    .map((entry) => {
      if (!entry.bytes) return "";
      return new TextDecoder().decode(entry.bytes);
    })
    .filter(Boolean);
  return chunks.join("");
}

function registerRequestCapture() {
  browser.webRequest.onBeforeRequest.addListener(
    async (details) => {
      if (!shouldTrack(details.url)) return;

      const bodyText = decodeRequestBody(details.requestBody);
      const key = details.requestId;
      const platform = normalizePlatform(new URL(details.url).hostname);
      conversationState.set(key, {
        platform,
        conversationId: conversationIdFromUrl(details.url),
        input: extractInput(bodyText)
      });
    },
    { urls: ["<all_urls>"] },
    ["requestBody"]
  );
}

function registerResponseCapture() {
  browser.webRequest.onBeforeRequest.addListener(
    (details) => {
      if (!shouldTrack(details.url)) return;

      const filter = browser.webRequest.filterResponseData(details.requestId);
      const decoder = new TextDecoder("utf-8");
      const encoder = new TextEncoder();
      let full = "";

      filter.ondata = (event) => {
        full += decoder.decode(event.data, { stream: true });
        filter.write(event.data);
      };

      filter.onstop = async () => {
        full += decoder.decode();
        const base = conversationState.get(details.requestId) || {
          platform: normalizePlatform(new URL(details.url).hostname),
          conversationId: conversationIdFromUrl(details.url),
          input: ""
        };

        const record = {
          platform: base.platform,
          timestamp: new Date().toISOString(),
          input: base.input,
          output: extractOutput(full),
          conversationId: base.conversationId
        };

        await persistRecord(record);
        conversationState.delete(details.requestId);
        filter.close();
      };

      filter.onerror = () => {
        filter.disconnect();
      };
    },
    { urls: ["<all_urls>"] },
    ["blocking"]
  );
}

browser.runtime.onMessage.addListener((message) => {
  if (message?.type === "RECORDER_EXPORT_JSON") {
    return Promise.resolve({ ok: true, data: records });
  }

  if (message?.type === "RECORDER_CLEAR") {
    records.length = 0;
    browser.storage.local.set({ aiRecords: [] });
    return Promise.resolve({ ok: true });
  }

  return undefined;
});

async function loadExistingRecords() {
  const stored = await browser.storage.local.get("aiRecords");
  if (Array.isArray(stored.aiRecords)) {
    records.push(...stored.aiRecords);
  }
}

async function initRecorder() {
  await loadExistingRecords();
  registerRequestCapture();
  registerResponseCapture();
}

initRecorder();
