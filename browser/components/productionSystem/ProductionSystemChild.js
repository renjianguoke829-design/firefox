export const PLATFORM_SELECTORS = {
  "claude.ai": 'div.ProseMirror[contenteditable="true"]',
  claude: 'div.ProseMirror[contenteditable="true"]',
  "gemini.google.com": 'div.ql-editor[contenteditable="true"]',
  gemini: 'div.ql-editor[contenteditable="true"]',
  "grok.com": 'div[contenteditable="true"][data-testid]',
  grok: 'div[contenteditable="true"][data-testid]',
  "deepseek.com": 'textarea#chat-input, div[contenteditable="true"]',
  deepseek: 'textarea#chat-input, div[contenteditable="true"]',
  "kimi.moonshot.cn": 'div[contenteditable="true"].editor-input',
  kimi: 'div[contenteditable="true"].editor-input',
  "chatgpt.com": 'div#prompt-textarea[contenteditable="true"]',
  chatgpt: 'div#prompt-textarea[contenteditable="true"]',
  "web.telegram.org": 'div.input-message-input[contenteditable="true"]',
  telegram: 'div.input-message-input[contenteditable="true"]',
};

function resolveSelector(platform) {
  return PLATFORM_SELECTORS[platform] || PLATFORM_SELECTORS[platform?.toLowerCase()] ||
    'textarea, div[contenteditable="true"]';
}

function dispatchEnter(win, el) {
  el.dispatchEvent(
    new win.KeyboardEvent("keydown", {
      key: "Enter",
      code: "Enter",
      keyCode: 13,
      which: 13,
      bubbles: true,
      cancelable: true,
    })
  );
  el.dispatchEvent(
    new win.KeyboardEvent("keyup", {
      key: "Enter",
      code: "Enter",
      keyCode: 13,
      which: 13,
      bubbles: true,
      cancelable: true,
    })
  );
}

function insertContenteditable(win, el, text) {
  const sel = win.getSelection();
  if (!sel || sel.rangeCount === 0) {
    const range = win.document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    sel?.removeAllRanges();
    sel?.addRange(range);
  }
  const range = sel.getRangeAt(0);
  range.deleteContents();
  range.insertNode(win.document.createTextNode(text));
  range.collapse(false);
}

function insertInputLike(el, text) {
  const start = typeof el.selectionStart === "number" ? el.selectionStart : el.value.length;
  const current = el.value || "";
  el.value = `${current.slice(0, start)}${text}${current.slice(start)}`;
  const pos = start + text.length;
  el.selectionStart = pos;
  el.selectionEnd = pos;
}

export function injectToReactInput(win, selector, text, delays = []) {
  const el = win.document.querySelector(selector);
  if (!el) {
    return false;
  }

  el.focus();
  let i = 0;
  const typeNext = () => {
    if (i >= text.length) {
      dispatchEnter(win, el);
      return;
    }

    const d = Number(delays[i] ?? 80);
    const ch = text[i];
    el.dispatchEvent(new win.KeyboardEvent("keydown", { key: ch, bubbles: true, cancelable: true }));

    if (el.isContentEditable || el.contentEditable === "true") {
      insertContenteditable(win, el, ch);
    } else {
      insertInputLike(el, ch);
    }

    el.dispatchEvent(new win.InputEvent("input", { data: ch, inputType: "insertText", bubbles: true }));
    el.dispatchEvent(new win.KeyboardEvent("keyup", { key: ch, bubbles: true, cancelable: true }));

    i += 1;
    win.setTimeout(typeNext, Math.max(0, Math.abs(d)));
  };

  typeNext();
  return true;
}

export function injectToTelegram(win, selector, text, delays = []) {
  const el = win.document.querySelector(selector);
  if (!el) {
    return false;
  }

  el.focus();
  try {
    win.document.execCommand("selectAll", false, null);
  } catch (e) {}

  let i = 0;
  const typeNext = () => {
    if (i >= text.length) {
      dispatchEnter(win, el);
      return;
    }

    const d = Number(delays[i] ?? 80);
    const ch = text[i];
    win.document.execCommand("insertText", false, ch);
    i += 1;
    win.setTimeout(typeNext, Math.max(0, Math.abs(d)));
  };

  typeNext();
  return true;
}

export function runInject(win, platform, text, delays) {
  const selector = resolveSelector(platform);
  if ((platform || "").includes("telegram") || platform === "web.telegram.org") {
    return injectToTelegram(win, selector, text, delays);
  }
  return injectToReactInput(win, selector, text, delays);
}
