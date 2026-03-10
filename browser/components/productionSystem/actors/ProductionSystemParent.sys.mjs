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
      platform: obj.platform || "",
      text: obj.text || "",
      delays,
    };
  } catch (e) {
    return null;
  }
}

const ObserverImpl = {
  observe(subject, topic, data) {
    if (topic !== OBSERVER_TOPIC || !data) {
      return;
    }
    const payload = parsePayload(data);
    if (!payload) {
      return;
    }

    const win = Services.wm.getMostRecentWindow("navigator:browser");
    const browser = win?.gBrowser?.selectedBrowser;
    const actor = browser?.browsingContext?.currentWindowGlobal?.getActor("ProductionSystem");
    if (actor) {
      actor.sendAsyncMessage("InjectText", payload);
    }
  },
};

Services.obs.addObserver(ObserverImpl, OBSERVER_TOPIC);

export class ProductionSystemParent extends JSWindowActorParent {}
