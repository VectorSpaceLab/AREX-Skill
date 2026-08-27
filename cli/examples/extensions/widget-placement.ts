import type { ExtensionAPI } from "@auto-ml-skills/disco";

export default function widgetPlacementExtension(disco: ExtensionAPI) {
	disco.on("session_start", (_event, ctx) => {
		if (!ctx.hasUI) return;
		ctx.ui.setWidget("widget-above", ["Above editor widget"]);
		ctx.ui.setWidget("widget-below", ["Below editor widget"], { placement: "belowEditor" });
	});
}
