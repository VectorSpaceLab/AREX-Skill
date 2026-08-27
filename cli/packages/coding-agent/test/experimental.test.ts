import { afterEach, describe, expect, it } from "vitest";
import { areExperimentalFeaturesEnabled } from "../src/core/experimental.ts";

describe("areExperimentalFeaturesEnabled", () => {
	const originalDiscoExperimental = process.env.DISCO_EXPERIMENTAL;

	afterEach(() => {
		if (originalDiscoExperimental === undefined) {
			delete process.env.DISCO_EXPERIMENTAL;
		} else {
			process.env.DISCO_EXPERIMENTAL = originalDiscoExperimental;
		}
	});

	it("returns false when DISCO_EXPERIMENTAL is unset", () => {
		delete process.env.DISCO_EXPERIMENTAL;

		expect(areExperimentalFeaturesEnabled()).toBe(false);
	});

	it("returns false when DISCO_EXPERIMENTAL is empty", () => {
		process.env.DISCO_EXPERIMENTAL = "";

		expect(areExperimentalFeaturesEnabled()).toBe(false);
	});

	it("returns true when DISCO_EXPERIMENTAL is set to 1", () => {
		process.env.DISCO_EXPERIMENTAL = "1";

		expect(areExperimentalFeaturesEnabled()).toBe(true);
	});

	it("returns false when DISCO_EXPERIMENTAL is set to 0", () => {
		process.env.DISCO_EXPERIMENTAL = "0";

		expect(areExperimentalFeaturesEnabled()).toBe(false);
	});

	it("returns false when DISCO_EXPERIMENTAL is set to a non-1 value", () => {
		process.env.DISCO_EXPERIMENTAL = "true";

		expect(areExperimentalFeaturesEnabled()).toBe(false);
	});
});
