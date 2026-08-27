import { describe, expect, it } from "vitest";
import { getDiscoUserAgent } from "../src/utils/disco-user-agent.ts";

describe("getDiscoUserAgent", () => {
	it("formats the DisCo user agent", () => {
		const runtime = process.versions.bun ? `bun/${process.versions.bun}` : `node/${process.version}`;
		const userAgent = getDiscoUserAgent("1.2.3");

		expect(userAgent).toBe(`disco/1.2.3 (${process.platform}; ${runtime}; ${process.arch})`);
		expect(userAgent).toMatch(/^disco\/[^\s()]+ \([^;()]+;\s*[^;()]+;\s*[^()]+\)$/);
	});
});
