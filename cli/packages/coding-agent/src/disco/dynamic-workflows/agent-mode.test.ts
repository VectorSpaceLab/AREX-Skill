import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ResourceLoader } from "../../core/resource-loader.ts";
import type { CreateAgentSessionOptions } from "../../core/sdk.ts";
import { SessionManager } from "../../core/session-manager.ts";
import { SettingsManager } from "../../core/settings-manager.ts";

const captured = vi.hoisted(() => ({ options: [] as unknown[] }));

vi.mock("../../core/sdk.ts", () => ({
	createCodingTools: () => [],
	createAgentSession: async (options: unknown) => {
		captured.options.push(options);
		return {
			session: {
				messages: [{ role: "assistant", content: [{ type: "text", text: "subagent complete" }] }],
				prompt: async () => {},
				abort: () => {},
				subscribe: () => () => {},
				getSessionStats: () => ({
					tokens: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
					cost: 0,
				}),
				dispose: () => {},
			},
		};
	},
}));

import { WorkflowAgent } from "./agent.ts";

describe("WorkflowAgent mode isolation", () => {
	beforeEach(() => {
		captured.options.length = 0;
	});

	it("forces the parent mode and replaces isolation-sensitive session overrides", async () => {
		const injectedManager = SessionManager.inMemory("/injected", { discoMode: "researcher" });
		const injectedLoader = {} as ResourceLoader;
		const agent = new WorkflowAgent({
			cwd: process.cwd(),
			discoMode: "creator",
			tools: [],
			session: {
				discoMode: "researcher",
				sessionManager: injectedManager,
				resourceLoader: injectedLoader,
				settingsManager: SettingsManager.inMemory(),
			},
		});

		await expect(agent.run("Complete the bounded task.")).resolves.toBe("subagent complete");
		expect(captured.options).toHaveLength(1);
		const options = captured.options[0] as CreateAgentSessionOptions;
		expect(options.discoMode).toBe("creator");
		expect(options.resourceLoader).toBeUndefined();
		expect(options.sessionManager).toBeInstanceOf(SessionManager);
		expect(options.sessionManager).not.toBe(injectedManager);
		expect(options.sessionManager?.getDiscoMode()).toBe("creator");
	});

	it("defaults standalone workflow agents to Researcher", async () => {
		const agent = new WorkflowAgent({
			cwd: process.cwd(),
			tools: [],
			session: { settingsManager: SettingsManager.inMemory() },
		});

		await agent.run("Complete the bounded task.");
		const options = captured.options[0] as CreateAgentSessionOptions;
		expect(options.discoMode).toBe("researcher");
		expect(options.sessionManager?.getDiscoMode()).toBe("researcher");
	});
});
