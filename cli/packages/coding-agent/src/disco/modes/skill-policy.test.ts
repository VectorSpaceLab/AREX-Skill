import { describe, expect, it } from "vitest";
import { isSkillEligibleForDiscoMode, resolveDiscoSkillRole } from "./skill-policy.ts";
import { DEFAULT_DISCO_AGENT_MODE, parseDiscoAgentModeCommand, resolveDiscoAgentMode } from "./types.ts";

describe("DisCo mode resolution", () => {
	it("defaults missing and invalid values to Researcher", () => {
		expect(resolveDiscoAgentMode(undefined)).toEqual({ mode: DEFAULT_DISCO_AGENT_MODE });
		expect(resolveDiscoAgentMode("legacy")).toEqual({ mode: "researcher", invalidValue: "legacy" });
		expect(resolveDiscoAgentMode(null)).toEqual({ mode: "researcher", invalidValue: null });
	});

	it("accepts only the two exact mode values", () => {
		expect(resolveDiscoAgentMode("creator")).toEqual({ mode: "creator" });
		expect(resolveDiscoAgentMode("researcher")).toEqual({ mode: "researcher" });
		expect(resolveDiscoAgentMode("Creator").mode).toBe("researcher");
	});

	it("parses only canonical mode commands and reports arguments", () => {
		expect(parseDiscoAgentModeCommand("/creator")).toEqual({ mode: "creator", hasArguments: false });
		expect(parseDiscoAgentModeCommand("/researcher task")).toEqual({ mode: "researcher", hasArguments: true });
		expect(parseDiscoAgentModeCommand("/resarcher")).toBeUndefined();
		expect(parseDiscoAgentModeCommand("/creator-extra")).toBeUndefined();
	});
});

describe("DisCo skill role policy", () => {
	it("treats an absent role as operating without an invalid-value diagnostic", () => {
		expect(resolveDiscoSkillRole({})).toEqual({ role: "operating" });
		expect(resolveDiscoSkillRole({ metadata: {} })).toEqual({ role: "operating" });
		expect(resolveDiscoSkillRole({ metadata: "external metadata" })).toEqual({ role: "operating" });
	});

	it("accepts only exact meta, operating, and shared values", () => {
		expect(resolveDiscoSkillRole({ metadata: { "disco-role": "meta" } })).toEqual({ role: "meta" });
		expect(resolveDiscoSkillRole({ metadata: { "disco-role": "operating" } })).toEqual({ role: "operating" });
		expect(resolveDiscoSkillRole({ metadata: { "disco-role": "shared" } })).toEqual({ role: "shared" });

		for (const invalidValue of ["", "Meta", "researcher", "both", null, false, 1, []]) {
			expect(resolveDiscoSkillRole({ metadata: { "disco-role": invalidValue } })).toEqual({ invalidValue });
		}
	});

	it("exposes shared to both modes while preserving exclusive roles", () => {
		expect(isSkillEligibleForDiscoMode("meta", "creator")).toBe(true);
		expect(isSkillEligibleForDiscoMode("meta", "researcher")).toBe(false);
		expect(isSkillEligibleForDiscoMode("operating", "creator")).toBe(false);
		expect(isSkillEligibleForDiscoMode("operating", "researcher")).toBe(true);
		expect(isSkillEligibleForDiscoMode("shared", "creator")).toBe(true);
		expect(isSkillEligibleForDiscoMode("shared", "researcher")).toBe(true);
	});
});
