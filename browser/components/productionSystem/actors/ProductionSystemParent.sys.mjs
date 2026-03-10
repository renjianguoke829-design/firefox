import { Services } from "resource://gre/modules/Services.sys.mjs";

const OBSERVER_TOPIC = "production-system-inject";

function parsePayload(subject) {
  if (!subject) {
    return null;
  }
  try {
    const obj = JSON.parse(subject);
    const delays = String(obj.delays || "")
      .split(",")
      .filter(Boolean)
      .map(v => parseInt(v, 10))
      .filter(v => !Number.isNaN(v));
    return {
      platform: String(obj.platform || "").toLowerCase(),
      text: obj.text || "",
      delays,
    };
  } catch (e) {
    return null;
  }
}

function hostMatchesPlatform(host, platform) {
  if (!platform) {
    return true;
  }
  const normalizedHost = String(host || "").toLowerCase();
  return (
    normalizedHost.includes(platform) ||
    normalizedHost.startsWith(`${platform}.`) ||
    normalizedHost.endsWith(`.${platform}`)
  );
}

function findMatchingBrowser(platform) {
  const enumerator = Services.wm.getEnumerator("navigator:browser");
  while (enumerator.hasMoreElements()) {
    const win = enumerator.getNext();
    const gBrowser = win?.gBrowser;
    if (!gBrowser?.browsers) {
      continue;
    }
    for (const browser of gBrowser.browsers) {
      const host = browser?.currentURI?.host;
      if (hostMatchesPlatform(host, platform)) {
        return browser;
      }
    }
  }
  return Services.wm.getMostRecentWindow("navigator:browser")?.gBrowser?.selectedBrowser || null;
}

const ObserverImpl = {
  observe(subject, topic, data) {
    if (topic !== OBSERVER_TOPIC || !data) {
      return;
    }
    const payload = parsePayload(data);
    if (!payload || !payload.text) {
      return;
    }

    const browser = findMatchingBrowser(payload.platform);
    const actor = browser?.browsingContext?.currentWindowGlobal?.getActor("ProductionSystem");
    if (actor) {
      actor.sendAsyncMessage("InjectText", payload);
    }
  },
};

Services.obs.addObserver(ObserverImpl, OBSERVER_TOPIC);

export class ProductionSystemParent extends JSWindowActorParent {}
