import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { assertAgentEnvironment, normalizeAgentEnvironment } from "./agent.ts";
import type { AgentRunOptions, AgentUsage } from "./agent.ts";
import { WorkflowError, WorkflowErrorCode } from "./errors.ts";
import { deliverText, installResultDelivery } from "./task-panel.ts";
import { WorkflowManager } from "./workflow-manager.ts";
import { createWorkflowTool } from "./workflow-tool.ts";
import { NavigatorModel } from "./workflow-ui.ts";
import { extractWorkflowCoverage, parseWorkflowScript, runWorkflow } from "./workflow.ts";

const SCRIPT = `
export const meta = { name: "test_workflow", description: "test workflow" };
return await agent("do the test task", { label: "test-agent" });
`;

function runnerFrom(
	implementation: (prompt: string, options: AgentRunOptions) => Promise<string> | string,
): { run: (prompt: string, options?: AgentRunOptions) => Promise<string> } {
	return {
		run: async (prompt, options = {}) => implementation(prompt, options),
	};
}

function usage(total: number): AgentUsage {
	return { input: total, output: 0, cacheRead: 0, cacheWrite: 0, total, cost: 0 };
}

describe("workflow parser diagnostics", () => {
	it("reports line, column, source excerpt, caret, and the args hint for markdown backticks", () => {
		const script = [
			'export const meta = { name: "bad_script", description: "bad script" };',
			"return await agent(`The API uses `base_url` and `api_key`.`);",
		].join("\n");

		expect(() => parseWorkflowScript(script)).toThrowError(
			/line \d+, column \d+[\s\S]*The API uses[\s\S]*\^[\s\S]*move the prompt payload to args/i,
		);
	});

	it("does not attach the Markdown-backtick hint to an unrelated syntax error", () => {
		const script = [
			'export const meta = { name: "bad_script", description: "bad script" };',
			'return await agent("missing close";',
		].join("\n");

		try {
			parseWorkflowScript(script);
			throw new Error("expected parser failure");
		} catch (error) {
			expect(error).toBeInstanceOf(WorkflowError);
			const details = (error as WorkflowError).details as {
				line: number;
				column: number;
				sourceLine: string;
				caret: string;
				hint: string;
			};
			expect(details.line).toBe(2);
			expect(details.column).toBeGreaterThan(0);
			expect(details.sourceLine).toContain("missing close");
			expect(details.caret).toContain("^");
			expect(details.hint).toBe("");
		}
	});

	it("keeps the meta-first validation and tool-level fence stripping", () => {
		expect(() =>
			parseWorkflowScript(
				'log("before meta");\nexport const meta = { name: "late", description: "late meta" };',
			),
		).toThrowError(/must be the first statement/i);

		const tool = createWorkflowTool({ cwd: process.cwd() });
		const prepared = tool.prepareArguments?.({
			script: `\`\`\`js\n${SCRIPT.trim()}\n\`\`\``,
		});
		expect((prepared as { script?: string }).script).toBe(SCRIPT.trim());
	});

	it("passes Markdown-rich briefs through args without embedding them in the script", async () => {
		const brief = "Inspect `base_url` and `api_key`.\n```python\nprint('safe')\n```";
		let receivedPrompt: string | undefined;
		const script = `
export const meta = { name: "args_brief", description: "args brief" };
const job = args.jobs[0];
return await agent(job.prompt, { label: job.id, subSkill: job.id });
`;

		const result = await runWorkflow(script, {
			args: { jobs: [{ id: "markdown-job", prompt: brief }] },
			agent: runnerFrom(async (prompt) => {
				receivedPrompt = prompt;
				return "ok";
			}),
		});

		expect(receivedPrompt).toBe(brief);
		expect(result.result).toBe("ok");
	});
});

describe("workflow agent lifecycle", () => {
	it("aborts a timed-out attempt, waits for teardown, then retries without overlap", async () => {
		const events: string[] = [];
		let attempts = 0;
		let active = 0;
		let maxActive = 0;

		const agent = runnerFrom(async (_prompt, options) => {
			attempts++;
			active++;
			maxActive = Math.max(maxActive, active);
			if (attempts === 1) {
				await new Promise<void>((resolve) => {
					options.signal?.addEventListener(
						"abort",
						() => setTimeout(() => resolve(), 10),
						{ once: true },
					);
				});
				events.push("attempt-1-teardown");
				active--;
				return "late result";
			}
			events.push("attempt-2-start");
			active--;
			return "ok";
		});

		const result = await runWorkflow(SCRIPT, {
			agent,
			agentTimeoutMs: 5,
			concurrency: 1,
		});

		expect(result.result).toBe("ok");
		expect(attempts).toBe(2);
		expect(maxActive).toBe(1);
		expect(events).toEqual(["attempt-1-teardown", "attempt-2-start"]);
		expect(active).toBe(0);
	});

	it("uses terminal usage that arrives during timeout teardown instead of a prompt estimate", async () => {
		const agent = runnerFrom(async (_prompt, options) => {
			await new Promise<void>((resolve) => {
				options.signal?.addEventListener("abort", () => setTimeout(resolve, 5), { once: true });
			});
			options.onUsage?.(usage(42));
			return "late result";
		});

		const result = await runWorkflow(SCRIPT, {
			agent,
			agentTimeoutMs: 1,
			agentRetries: 0,
		});

		expect(result.result).toBeNull();
		expect(result.tokenUsage?.total).toBe(42);
		expect(result.tokenUsage?.estimated).not.toBe(true);
	});

	it("keeps live usage out of finalized accounting and reconciles retry usage once per attempt", async () => {
		let attempts = 0;
		const liveEvents: Array<{ finalized?: boolean; total: number }> = [];
		const agent = runnerFrom(async (_prompt, options) => {
			attempts++;
			options.onLiveUsage?.(usage(100 + attempts));
			options.onUsage?.(usage(attempts === 1 ? 10 : 20));
			if (attempts === 1) throw new Error("retryable provider error");
			return "ok";
		});

		const result = await runWorkflow(SCRIPT, {
			agent,
			agentRetries: 1,
			onTokenUsage: (value, info) => {
				if (info?.source === "live") liveEvents.push({ finalized: info.finalized, total: value.total });
			},
		});

		expect(result.result).toBe("ok");
		expect(result.tokenUsage?.total).toBe(30);
		expect(result.tokenUsage?.estimated).not.toBe(true);
		expect(liveEvents.length).toBeGreaterThan(0);
		expect(liveEvents.every((event) => event.finalized === false)).toBe(true);
	});

	it("does not retry an externally aborted attempt", async () => {
		const controller = new AbortController();
		let calls = 0;
		let notifyStarted!: () => void;
		const started = new Promise<void>((resolve) => {
			notifyStarted = resolve;
		});
		const agent = runnerFrom(async (_prompt, options) => {
			calls++;
			notifyStarted();
			await new Promise<void>((resolve) => {
				options.signal?.addEventListener("abort", () => setTimeout(resolve, 5), { once: true });
			});
			throw new Error("Subagent was aborted");
		});

		const promise = runWorkflow(SCRIPT, {
			agent,
			agentRetries: 5,
			agentTimeoutMs: 1_000,
			signal: controller.signal,
		});
		await started;
		controller.abort();

		await expect(promise).rejects.toMatchObject({ code: WorkflowErrorCode.WORKFLOW_ABORTED });
		expect(calls).toBe(1);
	});

	it("drains aborted siblings and preserves the original run-fatal error", async () => {
		const events: string[] = [];
		let notifySiblingStarted!: () => void;
		const siblingStarted = new Promise<void>((resolve) => {
			notifySiblingStarted = resolve;
		});
		const agent = runnerFrom(async (prompt, options) => {
			if (prompt === "fatal") {
				await siblingStarted;
				throw new WorkflowError(
					"prepared environment mismatch",
					WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
					{ recoverable: false },
				);
			}

			events.push("sibling-start");
			notifySiblingStarted();
			await new Promise<void>((resolve) => {
				options.signal?.addEventListener(
					"abort",
					() => setTimeout(() => {
						events.push("sibling-teardown");
						resolve();
					}, 5),
					{ once: true },
				);
			});
			throw new Error("Subagent was aborted");
		});
		const script = `
export const meta = { name: "fatal_parallel", description: "fatal parallel" };
return await parallel([
  () => agent("fatal", { label: "fatal", subSkill: "fatal" }),
  () => agent("sibling", { label: "sibling", subSkill: "sibling" }),
]);
`;

		await expect(
			runWorkflow(script, { agent, concurrency: 2, agentRetries: 5, agentTimeoutMs: 1_000 }),
		).rejects.toMatchObject({
			message: "prepared environment mismatch",
			code: WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
		});
		expect(events).toEqual(["sibling-start", "sibling-teardown"]);
	});
});

describe("workflow coverage and recovery contract", () => {
	it("extracts an incomplete ledger without treating null lanes as success", () => {
		const coverage = extractWorkflowCoverage({
			complete: false,
			rows: [
				{ id: "completed", ok: true, result: "done" },
				{ id: "missing", ok: false, result: null, error: "AGENT_TIMEOUT" },
			],
			missing: ["missing"],
			errors: [{ id: "missing", error: "AGENT_TIMEOUT" }],
		});

		expect(coverage).toEqual({
			complete: false,
			missing: ["missing"],
			errors: [{ id: "missing", error: "AGENT_TIMEOUT" }],
		});
	});

	it("recovers only the current missing IDs and stops after consecutive no-progress rounds", async () => {
		let calls: string[] = [];
		const agent = runnerFrom(async (prompt) => {
			calls.push(prompt);
			return prompt === "completed" ? "done" : null;
		});
		const script = `
export const meta = { name: "recovery_workflow", description: "recovery workflow" };
return await recoverMissing(
  [{ id: "completed" }, { id: "stuck" }],
  async (job) => agent(job.id, { label: job.id, subSkill: job.id }),
  { maxRounds: 50, noProgressRounds: 2 }
);
`;

		const result = await runWorkflow(script, { agent, concurrency: 2, agentRetries: 0 });
		const recovery = result.result as {
			complete: boolean;
			missing: string[];
			rounds: number;
			stoppedReason?: string;
		};

		expect(recovery.complete).toBe(false);
		expect(recovery.missing).toEqual(["stuck"]);
		expect(recovery.rounds).toBe(3);
		expect(recovery.stoppedReason).toBe("no-progress");
		expect(calls).toEqual(["completed", "stuck", "stuck", "stuck"]);
	});
});

describe("prepared environment assertions", () => {
	it("normalizes the prepare-env report fields into the canonical agent contract", () => {
		const normalized = normalizeAgentEnvironment({
			pythonExecutable: process.execPath,
			expectedDistribution: "target-package",
			expectedVersion: "1.2.3",
			assertBeforeStartup: true,
		});

		expect(normalized.environment).toEqual({
			executable: process.execPath,
			package: "target-package",
			version: "1.2.3",
		});
		expect(normalized.warnings).toHaveLength(1);
		expect(normalized.warnings[0]).toContain("pythonExecutable -> executable");
		expect(normalized.warnings[0]).toContain("expectedDistribution -> package");
		expect(normalized.warnings[0]).toContain("expectedVersion -> version");
		expect(normalized.warnings[0]).toContain("assertBeforeStartup");
	});

	it("accepts matching canonical and legacy fields but rejects conflicts without exposing values", () => {
		const matching = normalizeAgentEnvironment({
			executable: process.execPath,
			pythonExecutable: process.execPath,
			package: "target-package",
			expectedDistribution: "target-package",
		});

		expect(matching.environment).toEqual({ executable: process.execPath, package: "target-package" });
		expect(matching.warnings[0]).toContain("legacy prepared-environment fields");

		try {
			normalizeAgentEnvironment({
				executable: "/canonical/private/python",
				pythonExecutable: "/legacy/private/python",
			});
			throw new Error("expected environment conflict");
		} catch (error) {
			expect(error).toMatchObject({
				code: WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
				recoverable: false,
			});
			expect((error as Error).message).toContain("`executable`");
			expect((error as Error).message).toContain("`pythonExecutable`");
			expect((error as Error).message).not.toContain("/canonical/private/python");
			expect((error as Error).message).not.toContain("/legacy/private/python");
		}
	});

	it("gives an actionable error when report metadata has no executable", () => {
		expect(() =>
			normalizeAgentEnvironment({
				expectedDistribution: "target-package",
				expectedVersion: "1.2.3",
			}),
		).toThrowError(/Missing environment\.executable[\s\S]*pythonExecutable[\s\S]*expectedDistribution.*package/i);
	});

	it("rejects relative executables instead of resolving them through ambient PATH", () => {
		expect(() => normalizeAgentEnvironment({ executable: "python" })).toThrowError(
			/absolute path[\s\S]*ambient PATH lookup is disabled/i,
		);
	});

	it("checks the structured executable/version handoff before a session starts", async () => {
		await expect(
			assertAgentEnvironment({
				executable: process.execPath,
				versionArgs: ["-e", "console.log('prepared-runtime-1.0.0')"],
				version: "prepared-runtime-1.0.0",
			}),
		).resolves.toMatchObject({ version: "prepared-runtime-1.0.0" });
	});

	it("checks the legacy report handoff through the real assertion path", async () => {
		const warnings: string[] = [];
		await expect(
			assertAgentEnvironment(
				{
					pythonExecutable: process.execPath,
					versionArgs: ["-e", "console.log('prepared-runtime-legacy-1.0.0')"],
					expectedVersion: "prepared-runtime-legacy-1.0.0",
				},
				process.cwd(),
				{ onWarning: (warning) => warnings.push(warning) },
			),
		).resolves.toMatchObject({ version: "prepared-runtime-legacy-1.0.0" });
		expect(warnings).toHaveLength(1);
		expect(warnings[0]).toContain("pythonExecutable -> executable");
		expect(warnings[0]).toContain("expectedVersion -> version");
	});

	it("treats a prepared package version mismatch as a non-recoverable hard failure", async () => {
		await expect(
			assertAgentEnvironment({
				executable: process.execPath,
				package: "target-package",
				versionArgs: ["-e", "console.log('prepared-runtime-2.0.0')"],
				version: "prepared-runtime-1.0.0",
			}),
		).rejects.toMatchObject({
			code: WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
			recoverable: false,
		});
	});

	it("replays the Creator first-call shape with legacy report fields without reading runtime source", async () => {
		const received: AgentRunOptions[] = [];
		const script = `
export const meta = { name: "creator_first_call", description: "creator first call" };
const rows = await parallel(args.jobs.map((job) => () => agent(job.brief, {
  label: job.id,
  subSkill: job.id,
  environment: args.environment,
})));
return { complete: rows.every(Boolean), rows, missing: [], errors: [] };
`;

		const result = await runWorkflow(script, {
			persistLogs: false,
			args: {
				environment: {
					pythonExecutable: process.execPath,
					expectedDistribution: "target-package",
					expectedVersion: "1.2.3",
					assertBeforeStartup: true,
				},
				jobs: [
					{ id: "one", brief: "draft one" },
					{ id: "two", brief: "draft two" },
				],
			},
			agent: runnerFrom((_prompt, options) => {
				received.push(options);
				return "ok";
			}),
		});

		expect(result.complete).toBe(true);
		expect(received).toHaveLength(2);
		for (const options of received) {
			expect(options.environment).toEqual({
				executable: process.execPath,
				package: "target-package",
				version: "1.2.3",
			});
		}
		expect(result.logs.filter((line) => line.includes("legacy prepared-environment fields"))).toHaveLength(1);
	});

	it("normalizes a top-level workflow args environment before execution and preserves custom args", () => {
		const tool = createWorkflowTool({ cwd: process.cwd() });
		const prepared = tool.prepareArguments?.({
			script: SCRIPT,
			args: {
				environment: {
					pythonExecutable: process.execPath,
					expectedDistribution: "target-package",
					expectedVersion: "1.2.3",
				},
				jobs: [{ id: "one" }],
				customFlag: "preserved",
			},
		}) as { args: Record<string, unknown> };

		expect(prepared.args).toMatchObject({
				environment: {
					executable: process.execPath,
				package: "target-package",
				version: "1.2.3",
			},
			jobs: [{ id: "one" }],
			customFlag: "preserved",
		});
		expect(prepared.args.environment).toHaveProperty("pythonExecutable", process.execPath);
		expect(prepared.args.environment).toHaveProperty("expectedDistribution", "target-package");
		expect(prepared.args.environment).toHaveProperty("expectedVersion", "1.2.3");
	});

	it("surfaces a top-level legacy-field warning in the foreground result and persisted run logs", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-environment-warning-"));
		try {
			const manager = new WorkflowManager({ cwd, agent: runnerFrom(() => "ok") });
			const tool = createWorkflowTool({ cwd, manager });
			const prepared = tool.prepareArguments?.({
				script: SCRIPT,
				background: false,
				args: {
					environment: {
						pythonExecutable: process.execPath,
					},
				},
			});
			const result = await tool.execute(
				"environment-warning",
				structuredClone(prepared),
				undefined,
				undefined,
				{} as any,
			);
			const content = result.content[0];

			expect(content?.type === "text" ? content.text : "").toContain(
				"Warning: Prepared environment used legacy prepared-environment fields",
			);
			expect(manager.listRuns()[0]?.logs).toEqual(
				expect.arrayContaining([expect.stringContaining("legacy prepared-environment fields")]),
			);
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("includes prepared-environment deprecation warnings in background delivery text", () => {
		const message = deliverText({
			runId: "run-warning",
			status: "completed",
			background: true,
			startedAt: new Date(),
			controller: new AbortController(),
			journal: [],
			limits: {} as any,
			snapshot: {
				name: "warning_run",
				phases: [],
				agents: [],
				agentCount: 1,
				runningCount: 0,
				doneCount: 1,
				errorCount: 0,
				logs: [],
			},
			result: {
				meta: { name: "warning_run", description: "warning run" },
				result: "ok",
				logs: [
					"[warn] Prepared environment used legacy prepared-environment fields (pythonExecutable -> executable).",
				],
				phases: [],
				agentCount: 1,
				durationMs: 1,
			},
		} as any);

		expect(message).toContain("Warning: Prepared environment used legacy prepared-environment fields");
	});

	it("rejects conflicting top-level environment fields during workflow argument preparation", () => {
		const tool = createWorkflowTool({ cwd: process.cwd() });

		expect(() =>
			tool.prepareArguments?.({
				script: SCRIPT,
				args: {
					environment: {
						executable: "/canonical/private/python",
						pythonExecutable: "/legacy/private/python",
					},
				},
			}),
		).toThrowError(/environment contract conflict[\s\S]*executable[\s\S]*pythonExecutable/i);
	});
});

describe("workflow persistence", () => {
	it("defaults to one retry when a timeout is active, while explicit zero disables it", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			let attempts = 0;
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async (_prompt, options) => {
					attempts++;
					if (attempts === 1) {
						await new Promise<void>((resolve) => {
							options.signal?.addEventListener("abort", () => resolve(), { once: true });
						});
						return "late";
					}
					return "ok";
				}),
			});

			const result = await manager.runSync(SCRIPT, undefined, { agentTimeoutMs: 1 });
			expect(result.result).toBe("ok");
			expect(attempts).toBe(2);
			expect(manager.getPersistence().load(result.runId!)?.agentRetries).toBe(1);

			attempts = 0;
			const noRetry = await manager.runSync(SCRIPT, undefined, { agentTimeoutMs: 1, agentRetries: 0 });
			expect(noRetry.result).toBeNull();
			expect(attempts).toBe(1);
			expect(manager.getPersistence().load(noRetry.runId!)?.agentRetries).toBe(0);
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("persists per-run limits, recovery linkage, and finalized usage", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async (_prompt, options) => {
					options.onUsage?.(usage(9));
					return "ok";
				}),
			});
			const result = await manager.runSync(SCRIPT, undefined, {
				maxAgents: 5,
				concurrency: 2,
				agentTimeoutMs: 25,
				agentRetries: 1,
				tokenBudget: 500,
				recoveryOfRunId: "original-run",
				recoveryRound: 3,
				maxRecoveryRounds: 50,
			});

			const persisted = manager.getPersistence().load(result.runId!);
			expect(persisted).not.toBeNull();
			expect(persisted).toMatchObject({
				status: "completed",
				maxAgents: 5,
				concurrency: 2,
				agentTimeoutMs: 25,
				agentRetries: 1,
				tokenBudget: 500,
				recoveryOfRunId: "original-run",
				recoveryRound: 3,
				maxRecoveryRounds: 50,
			});
			expect(persisted?.tokenUsage?.total).toBe(9);
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("persists stable sub-skill IDs and marks an incomplete ledger as failed", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async () => null),
			});
			const script = `
export const meta = { name: "partial_workflow", description: "partial workflow" };
const rows = await parallel([
  () => agent("missing", { label: "same label", subSkill: "stable-job" }),
]);
return { rows: [{ id: "stable-job", ok: rows[0] !== null, result: rows[0] }], complete: false, missing: ["stable-job"], errors: [{ id: "stable-job", error: "AGENT_TIMEOUT" }] };
`;

			const result = await manager.runSync(script, undefined, { agentRetries: 0 });
			const persisted = manager.getPersistence().load(result.runId!);
			expect(persisted?.status).toBe("failed");
			expect(persisted?.complete).toBe(false);
			expect(persisted?.missing).toEqual(["stable-job"]);
			expect(persisted?.errorCode).toBe(WorkflowErrorCode.WORKFLOW_INCOMPLETE);
			expect(persisted?.recoverable).toBe(true);
			expect(persisted?.agents[0]?.stableId).toBe("stable-job");
			expect(persisted?.agents[0]?.attempts?.[0]?.status).toBe("error");
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("matches duplicate stable IDs by call index", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async (prompt, options) => {
					if (prompt === "first") await new Promise((resolve) => setTimeout(resolve, 2));
					options.onUsage?.(usage(prompt === "first" ? 10 : 20));
					return prompt;
				}),
			});
			const script = `
export const meta = { name: "duplicate_ids", description: "duplicate stable ids" };
return await parallel([
  () => agent("first", { label: "same", subSkill: "duplicate" }),
  () => agent("second", { label: "same", subSkill: "duplicate" }),
]);
`;

			const result = await manager.runSync(script, undefined, { concurrency: 2 });
			const persisted = manager.getPersistence().load(result.runId!);
			expect(persisted?.agents).toHaveLength(2);
			expect(persisted?.agents.find((agent) => agent.callIndex === 0)?.tokens).toBe(10);
			expect(persisted?.agents.find((agent) => agent.callIndex === 1)?.tokens).toBe(20);
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("waits for paused teardown, resumes historical agents in place, and does not retry the abort", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			let calls = 0;
			let notifySecondStarted!: () => void;
			const secondStarted = new Promise<void>((resolve) => {
				notifySecondStarted = resolve;
			});
			const events: string[] = [];
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async (_prompt, options) => {
					calls++;
					if (calls === 1) {
						options.onUsage?.(usage(3));
						return "first-result";
					}
					if (calls === 2) {
						events.push("second-start");
						notifySecondStarted();
						await new Promise<void>((resolve) => {
							options.signal?.addEventListener(
								"abort",
								() => setTimeout(() => {
									events.push("second-teardown");
									resolve();
								}, 10),
								{ once: true },
							);
						});
						throw new Error("Subagent was aborted");
					}
					events.push("resume-second-start");
					options.onUsage?.(usage(5));
					return "second-result";
				}),
			});
			const script = `
export const meta = { name: "resume_agents", description: "resume historical agents" };
const first = await agent("first", { label: "same label", subSkill: "job-a" });
const second = await agent("second", { label: "same label", subSkill: "job-b" });
return { first, second };
`;

			const { runId, promise } = manager.startInBackground(script, undefined, { agentTimeoutMs: 1_000 });
			await secondStarted;
			expect(manager.pause(runId)).toBe(true);
			const completed = new Promise<void>((resolve) => manager.once("complete", () => resolve()));
			const resumeRequest = manager.resume(runId);
			await expect(promise).rejects.toMatchObject({ code: WorkflowErrorCode.WORKFLOW_ABORTED });
			expect(await resumeRequest).toBe(true);
			await completed;

			const persisted = manager.getPersistence().load(runId);
			expect(events).toEqual(["second-start", "second-teardown", "resume-second-start"]);
			expect(calls).toBe(3);
			expect(persisted?.status).toBe("completed");
			expect(persisted?.agents).toHaveLength(2);
			expect(persisted?.agents.map((agent) => agent.stableId)).toEqual(["job-a", "job-b"]);
			expect(persisted?.tokenUsage?.total).toBe(8);
			expect(persisted?.errorCode).toBeUndefined();
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("keeps a stopped run aborted after late teardown and does not retry it", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			let calls = 0;
			let notifyStarted!: () => void;
			const started = new Promise<void>((resolve) => {
				notifyStarted = resolve;
			});
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async (_prompt, options) => {
					calls++;
					notifyStarted();
					await new Promise<void>((resolve) => {
						options.signal?.addEventListener("abort", () => setTimeout(resolve, 5), { once: true });
					});
					throw new Error("Subagent was aborted");
				}),
			});

			const { runId, promise } = manager.startInBackground(SCRIPT, undefined, { agentTimeoutMs: 1_000 });
			await started;
			expect(manager.stop(runId)).toBe(true);
			await expect(promise).rejects.toMatchObject({ code: WorkflowErrorCode.WORKFLOW_ABORTED });

			const persisted = manager.getPersistence().load(runId);
			expect(calls).toBe(1);
			expect(persisted).toMatchObject({
				status: "aborted",
				errorCode: WorkflowErrorCode.WORKFLOW_ABORTED,
				recoverable: false,
			});
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("persists a non-recoverable root cause", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			const manager = new WorkflowManager({
				cwd,
				agent: runnerFrom(async () => {
					throw new WorkflowError(
						"prepared environment mismatch",
						WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
						{ recoverable: false },
					);
				}),
			});

			await expect(manager.runSync(SCRIPT)).rejects.toMatchObject({
				code: WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
			});
			const persisted = manager.listRuns()[0];
			expect(persisted).toMatchObject({
				status: "failed",
				error: "prepared environment mismatch",
				errorCode: WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
				recoverable: false,
			});
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});
});

describe("workflow recovery delivery and persisted navigation", () => {
	it("delivers an incomplete background result as an explicit recovery follow-up", async () => {
		const cwd = mkdtempSync(join(tmpdir(), "disco-workflow-"));
		try {
			const manager = new WorkflowManager({ cwd, agent: runnerFrom(async () => null) });
			const sendMessage = vi.fn();
			installResultDelivery({ sendMessage } as any, manager);
			const script = `
export const meta = { name: "delivery_recovery", description: "delivery recovery" };
const result = await agent("missing", { label: "missing", subSkill: "job-missing" });
return { complete: false, rows: [{ id: "job-missing", ok: false, result }], missing: ["job-missing"], errors: [{ id: "job-missing", error: "AGENT_TIMEOUT" }] };
`;

			const { runId, promise } = manager.startInBackground(script);
			await promise;
			expect(sendMessage).toHaveBeenCalledTimes(1);
			const [message, options] = sendMessage.mock.calls[0];
			expect(message.content).toContain("requires recovery");
			expect(message.content).toContain(`Run ID: ${runId}`);
			expect(message.content).toContain("Missing IDs: job-missing");
			expect(message.content).toContain("Call the workflow tool again for only the missing IDs");
			expect(options).toEqual({ triggerTurn: true, deliverAs: "followUp" });
		} finally {
			rmSync(cwd, { recursive: true, force: true });
		}
	});

	it("restores persisted stable IDs, attempts, coverage, and usage in the navigator model", () => {
		const persisted = {
			runId: "persisted-run",
			workflowName: "persisted",
			script: SCRIPT,
			status: "failed" as const,
			phases: ["Build"],
			agents: [
				{
					id: 1,
					stableId: "job-a",
					callIndex: 0,
					label: "job a",
					phase: "Build",
					prompt: "do a",
					status: "error" as const,
					tokens: 12,
					attempts: [{ attempt: 1, status: "error" as const, tokens: 12 }],
				},
			],
			logs: [],
			complete: false,
			missing: ["job-a"],
			error: "incomplete",
			errorCode: WorkflowErrorCode.WORKFLOW_INCOMPLETE,
			recoverable: true,
			tokenUsage: { input: 0, output: 0, total: 12, estimated: true },
			liveTokenUsage: { input: 2, output: 3, total: 5 },
			startedAt: new Date().toISOString(),
			updatedAt: new Date().toISOString(),
		};
		const model = new NavigatorModel({
			listRuns: () => [persisted],
			getRun: () => undefined,
		} as any);

		expect(model.runStatus("persisted-run")).toContain("recovery required");
		expect(model.agentDetail("persisted-run", 1)).toMatchObject({
			stableId: "job-a",
			callIndex: 0,
			tokens: 12,
			attempts: [{ attempt: 1, status: "error", tokens: 12 }],
		});
	});
});
