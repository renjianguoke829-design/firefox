const PLATFORM_SELECTORS = {
  "claude.ai": { name: "Claude", input: "div[contenteditable]" },
  "grok.com": { name: "Grok", input: "textarea" },
  "gemini.google.com": { name: "Gemini", input: "div[contenteditable]" },
  "chat.deepseek.com": { name: "DeepSeek", input: "textarea" },
  "kimi.moonshot.cn": { name: "Kimi", input: "div[contenteditable]" }
};

function detectPlatform() {
  const hostname = window.location.hostname;
  for (const [domain, config] of Object.entries(PLATFORM_SELECTORS)) {
    if (hostname === domain || hostname.endsWith(`.${domain}`)) {
      return config;
    }
  }
  return { name: "unknown", input: null };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function humanType(element, text) {
  await sleep(500 + Math.floor(Math.random() * 1500));
  element.focus();

  for (const char of text) {
    if (Math.random() < 0.05) {
      const typo = String.fromCharCode(97 + Math.floor(Math.random() * 26));
      await typeChar(element, typo);
      await sleep(50 + Math.floor(Math.random() * 100));
      await backspace(element);
    }
    await typeChar(element, char);
    await sleep(50 + Math.floor(Math.random() * 100));
  }
  await sleep(1000 + Math.floor(Math.random() * 2000));
}

async function typeChar(element, char) {
  if (element.matches("textarea,input")) {
    element.value += char;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    return;
  }
  document.execCommand("insertText", false, char);
}

async function backspace(element) {
  if (element.matches("textarea,input")) {
    element.value = element.value.slice(0, -1);
    element.dispatchEvent(new Event("input", { bubbles: true }));
    return;
  }
  document.execCommand("delete", false);
}

function extractOutputText() {
  const selectors = ["main", "[role='main']", ".assistant", ".message", "article"];
  for (const selector of selectors) {
    const nodes = document.querySelectorAll(selector);
    if (nodes.length) {
      const last = nodes[nodes.length - 1];
      const text = (last.textContent || "").trim();
      if (text) {
        return text;
      }
    }
  }
  return "";
}

let outputDebounce;
function setupOutputObserver() {
  const root = document.body;
  const observer = new MutationObserver(() => {
    window.clearTimeout(outputDebounce);
    outputDebounce = window.setTimeout(() => {
      const output = extractOutputText();
      if (output) {
        browser.runtime.sendMessage({ type: "AI_OUTPUT", output });
      }
    }, 1500);
  });

  observer.observe(root, { childList: true, subtree: true, characterData: true });
}

browser.runtime.onMessage.addListener(async (message) => {
  if (message?.type !== "INJECT_PROMPT") {
    return undefined;
  }

  const platform = detectPlatform();
  if (!platform.input) {
    return { ok: false, error: "Unsupported platform" };
  }

  const input = document.querySelector(platform.input);
  if (!input) {
    return { ok: false, error: `Input not found: ${platform.input}` };
  }

  const promptPrefix = message.projectMode === "marxist" ? "[马列框架] " : "[空白对照] ";
  await humanType(input, `${promptPrefix}${message.prompt || ""}`);
  return { ok: true };
});

const platform = detectPlatform();
browser.runtime.sendMessage({ type: "PLATFORM_DETECTED", platform: platform.name });
setupOutputObserver();
