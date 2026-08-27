import type { AuthContext } from "@earendil-works/pi-ai";
import { describe, expect, it } from "vitest";
import { AuthStorage } from "../src/core/auth-storage.ts";
import { ModelRuntime } from "../src/core/model-runtime.ts";
import {
	anthropicOAuth,
	createDiscoProviderAuthContext,
	getDiscoOAuthCallbackHost,
	openaiCodexOAuth,
	openRouterOAuth,
} from "../src/core/oauth/index.ts";

describe("OAuth environment isolation", () => {
	it("uses only the DisCo callback-host variable", () => {
		expect(getDiscoOAuthCallbackHost({ PI_OAUTH_CALLBACK_HOST: "pi.internal" })).toBe("127.0.0.1");
		expect(
			getDiscoOAuthCallbackHost({
				PI_OAUTH_CALLBACK_HOST: "pi.internal",
				DISCO_OAUTH_CALLBACK_HOST: "disco.internal",
			}),
		).toBe("disco.internal");
	});

	it("filters every PI_* lookup from provider auth contexts", async () => {
		const reads: string[] = [];
		const base: AuthContext = {
			env: async (name) => {
				reads.push(name);
				return `${name}-value`;
			},
			fileExists: async () => true,
		};
		const context = createDiscoProviderAuthContext(base);

		await expect(context.env("PI_OAUTH_CALLBACK_HOST")).resolves.toBeUndefined();
		await expect(context.env("PI_CODING_AGENT_DIR")).resolves.toBeUndefined();
		await expect(context.env("ANTHROPIC_API_KEY")).resolves.toBe("ANTHROPIC_API_KEY-value");
		expect(reads).toEqual(["ANTHROPIC_API_KEY"]);
		await expect(context.fileExists("/tmp/credential")).resolves.toBe(true);
	});

	it("replaces the three callback-based Pi OAuth flows in ModelRuntime", async () => {
		const runtime = await ModelRuntime.create({ credentials: AuthStorage.inMemory(), modelsPath: null });

		expect(runtime.getProvider("anthropic")?.auth.oauth).toBe(anthropicOAuth);
		expect(runtime.getProvider("openai-codex")?.auth.oauth).toBe(openaiCodexOAuth);
		expect(runtime.getProvider("openrouter")?.auth.oauth).toBe(openRouterOAuth);
	});
});
