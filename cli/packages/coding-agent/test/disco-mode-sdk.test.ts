import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createAgentSessionServices } from "../src/core/agent-session-services.ts";
import { ModelRuntime } from "../src/core/model-runtime.ts";
import { createAgentSession } from "../src/core/sdk.ts";
import { SessionManager } from "../src/core/session-manager.ts";
import { createTestResourceLoader } from "./utilities.ts";

describe("DisCo mode SDK boundaries", () => {
	const cleanupPaths: string[] = [];

	afterEach(() => {
		for (const path of cleanupPaths.splice(0)) rmSync(path, { recursive: true, force: true });
	});

	function createRoot(): string {
		const root = mkdtempSync(join(tmpdir(), "disco-mode-sdk-"));
		cleanupPaths.push(root);
		return root;
	}

	async function createModelRuntime(): Promise<ModelRuntime> {
		return ModelRuntime.create({ modelsPath: null, allowModelNetwork: false });
	}

	it("rejects an explicit mode that conflicts with the session manager", async () => {
		const root = createRoot();
		const sessionManager = SessionManager.inMemory(root, { discoMode: "researcher" });

		await expect(
			createAgentSession({
				cwd: root,
				agentDir: root,
				discoMode: "creator",
				sessionManager,
				modelRuntime: await createModelRuntime(),
			}),
		).rejects.toThrow("Session manager mode researcher does not match requested discoMode creator");
	});

	it("rejects a resource loader whose mode conflicts with the session", async () => {
		const root = createRoot();
		const resourceLoader = {
			...createTestResourceLoader(),
			getDiscoMode: () => "researcher" as const,
		};

		await expect(
			createAgentSession({
				cwd: root,
				agentDir: root,
				sessionManager: SessionManager.inMemory(root, { discoMode: "creator" }),
				resourceLoader,
				modelRuntime: await createModelRuntime(),
			}),
		).rejects.toThrow("Resource loader mode researcher does not match session mode creator");
	});

	it("reports an invalid persisted header value while falling back to Researcher", async () => {
		const root = createRoot();
		const services = await createAgentSessionServices({
			cwd: root,
			agentDir: root,
			discoMode: "Creator",
			modelRuntime: await createModelRuntime(),
			resourceLoaderOptions: {
				includeDisCoDefaults: false,
				noSkills: true,
				noPromptTemplates: true,
				noThemes: true,
			},
		});

		expect(services.discoMode).toBe("researcher");
		expect(services.resourceLoader.getDiscoMode?.()).toBe("researcher");
		expect(services.diagnostics).toContainEqual({
			type: "warning",
			message: 'Invalid session discoMode "Creator"; using researcher',
		});
	});
});
