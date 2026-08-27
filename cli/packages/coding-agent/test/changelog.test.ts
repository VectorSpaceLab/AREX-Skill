import { describe, expect, test } from "vitest";
import { type ChangelogEntry, normalizeChangelogLinks } from "../src/utils/changelog.ts";

const entry: ChangelogEntry = {
	major: 0,
	minor: 1,
	patch: 1,
	content: "",
};

describe("normalizeChangelogLinks", () => {
	test("rewrites package-relative changelog links to tag-pinned GitHub source links", () => {
		const markdown = [
			"[Project Trust](README.md#project-trust)",
			"[Extensions](docs/extensions.md#project_trust)",
			"[Examples](examples/extensions/)",
			"[Root README](../README.md#supply-chain-hardening)",
		].join("\n");

		expect(normalizeChangelogLinks(markdown, entry)).toBe(
			[
				"[Project Trust](https://github.com/VectorSpaceLab/AREX-Skill/blob/v0.1.1/cli/README.md#project-trust)",
				"[Extensions](https://github.com/VectorSpaceLab/AREX-Skill/blob/v0.1.1/cli/docs/extensions.md#project_trust)",
				"[Examples](https://github.com/VectorSpaceLab/AREX-Skill/tree/v0.1.1/cli/examples/extensions/)",
				"[Root README](https://github.com/VectorSpaceLab/AREX-Skill/blob/v0.1.1/README.md#supply-chain-hardening)",
			].join("\n"),
		);
	});

	test("pins DisCo repository links without rewriting upstream or external links", () => {
		const markdown = [
			"[#5167](https://github.com/earendil-works/pi-mono/pull/5167)",
			"[#4163](https://github.com/badlogic/pi-mono/issues/4163)",
			"[DisCo README](https://github.com/VectorSpaceLab/AREX-Skill/blob/main/cli/README.md)",
			"[External](https://example.com/docs)",
			"[Local anchor](#settings)",
		].join("\n");

		expect(normalizeChangelogLinks(markdown, "0.1.1")).toBe(
			[
				"[#5167](https://github.com/earendil-works/pi-mono/pull/5167)",
				"[#4163](https://github.com/badlogic/pi-mono/issues/4163)",
				"[DisCo README](https://github.com/VectorSpaceLab/AREX-Skill/blob/v0.1.1/cli/README.md)",
				"[External](https://example.com/docs)",
				"[Local anchor](#settings)",
			].join("\n"),
		);
	});
});
