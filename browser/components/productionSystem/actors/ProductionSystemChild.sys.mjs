import { runInject } from "resource:///modules/productionSystem/ProductionSystemChild.js";

export class ProductionSystemChild extends JSWindowActorChild {
  receiveMessage(message) {
    if (message.name !== "InjectText") {
      return;
    }
    const { platform, text, delays } = message.data || {};
    runInject(this.contentWindow, platform || "", text || "", Array.isArray(delays) ? delays : []);
  }
}
