import { describe, expect, it } from "vitest";
import { initTheme } from "../src/modes/interactive/theme/theme.ts";

describe("theme global isolation", () => {
	it("initializes only the DisCo global symbol", () => {
		const globals = globalThis as Record<symbol, unknown>;
		const discoKey = Symbol.for("@auto-ml-skills/disco:theme");
		const piKey = Symbol.for("@earendil-works/pi-coding-agent:theme");
		const legacyPiKey = Symbol.for("@mariozechner/pi-coding-agent:theme");
		const previousDisco = globals[discoKey];
		const previousPi = globals[piKey];
		const previousLegacyPi = globals[legacyPiKey];
		const piSentinel = { owner: "pi" };
		const legacyPiSentinel = { owner: "legacy-pi" };

		try {
			globals[piKey] = piSentinel;
			globals[legacyPiKey] = legacyPiSentinel;
			initTheme("dark");

			expect(globals[discoKey]).toBeDefined();
			expect(globals[piKey]).toBe(piSentinel);
			expect(globals[legacyPiKey]).toBe(legacyPiSentinel);
		} finally {
			if (previousDisco === undefined) delete globals[discoKey];
			else globals[discoKey] = previousDisco;
			if (previousPi === undefined) delete globals[piKey];
			else globals[piKey] = previousPi;
			if (previousLegacyPi === undefined) delete globals[legacyPiKey];
			else globals[legacyPiKey] = previousLegacyPi;
		}
	});
});
