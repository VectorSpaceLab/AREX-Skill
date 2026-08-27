import { describe, expect, it } from "vitest";
import {
	isolateDisCoProcessFromPiEnvironment,
	PI_ENVIRONMENT_KEYS,
} from "../src/cli/pi-environment-isolation.ts";

describe("Pi environment isolation", () => {
	it("removes Pi-owned variables without changing DisCo or provider variables", () => {
		const env: NodeJS.ProcessEnv = {
			PI_CODING_AGENT_DIR: "/tmp/pi-agent",
			PI_CACHE_RETENTION: "long",
			PI_TUI_WRITE_LOG: "/tmp/pi-tui.log",
			PI_OAUTH_CALLBACK_HOST: "pi.internal",
			DISCO_CODING_AGENT_DIR: "/tmp/disco-agent",
			DISCO_CACHE_RETENTION: "short",
			OPENAI_API_KEY: "test-key",
		};

		isolateDisCoProcessFromPiEnvironment(env);

		for (const key of PI_ENVIRONMENT_KEYS) {
			expect(env[key]).toBeUndefined();
		}
		expect(env.DISCO_CODING_AGENT_DIR).toBe("/tmp/disco-agent");
		expect(env.DISCO_CACHE_RETENTION).toBe("short");
		expect(env.OPENAI_API_KEY).toBe("test-key");
	});
});
