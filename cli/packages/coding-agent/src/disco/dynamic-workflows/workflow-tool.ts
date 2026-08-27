import { Text } from "@earendil-works/pi-tui";
import { Type } from "typebox";
import { defineTool, type ToolDefinition } from "../../core/extensions/types.ts";
import { listAvailableModelSpecs } from "./agent.ts";
import { listAgentTypes, loadAgentRegistry } from "./agent-registry.ts";
import {
	createToolUpdateWorkflowDisplay,
	createWorkflowSnapshot,
	recomputeWorkflowSnapshot,
	renderWorkflowText,
	type WorkflowSnapshot,
} from "./display.ts";
import { WorkflowError, WorkflowErrorCode } from "./errors.ts";
import { parseWorkflowScript, type WorkflowRunResult } from "./workflow.ts";
import { WorkflowManager } from "./workflow-manager.ts";
import { createWorkflowStorage, type WorkflowStorage } from "./workflow-saved.ts";
import { loadWorkflowSettings } from "./workflow-settings.ts";

/** A concise model-routing reminder for workflow authors. */
export function modelRoutingGuideline(): string {
	const available = listAvailableModelSpecs();
	const list = available.length
		? `The user's currently available models (route only to these) are: ${available.join(", ")}.`
		: "Use models the user has configured.";
	return `For workflow agents, choose opts.tier ('small', 'medium', or 'big') to match the role; opts.model selects an exact configured provider/model and overrides the tier. ${list}`;
}

/**
 * Tells the LLM which named subagent definitions (agentType) are available, so
 * it can route an agent() to a reusable role that binds tools+model+prompt.
 * Returns undefined when no definitions are registered (nothing to advertise).
 */
export function agentTypeGuideline(cwd: string = process.cwd()): string | undefined {
	let types: Array<{ name: string; description?: string }>;
	try {
		types = listAgentTypes(loadAgentRegistry(cwd));
	} catch {
		return undefined;
	}
	if (!types.length) return undefined;
	const list = types.map((t) => (t.description ? `${t.name} (${t.description})` : t.name)).join(", ");
	return `For workflow, opts.agentType routes an agent to a named definition that binds its tools, model, and role prompt. Available agentTypes: ${list}. An explicit opts.model still overrides the definition's model.`;
}

const workflowToolSchema = Type.Object({
	script: Type.String({
		description: [
			"Required raw JavaScript workflow script, with no Markdown fences.",
			"First statement: export const meta = { name: 'short_snake_case', description: 'non-empty description', phases: [{ title: 'Phase' }] }",
			"Use phase('Name'), agent(prompt, opts), parallel(arrayOfFunctions), pipeline(items, ...stages), log(message), args, and budget. DisCo also supports agent(prompt, { subSkill: 'planned-sub-skill-id' }) for progress display. The workflow must call agent() at least once.",
			"parallel() requires functions, not promises: await parallel(items.map(item => () => agent(...))).",
		].join(" "),
	}),
	args: Type.Optional(
		Type.Any({ description: "Optional JSON value exposed to the workflow script as global `args`." }),
	),
	background: Type.Optional(
		Type.Boolean({
			description:
				"Run the workflow in the background. Default: true — the tool returns immediately with a run ID, the turn ends so the user isn't blocked, and the result is delivered back into the conversation when it finishes. Set to false only when you need the result inline in this same turn (the call will block until the workflow completes).",
		}),
	),
	maxAgents: Type.Optional(
		Type.Number({
			description: "Maximum number of agents allowed in this run. Default: 1000.",
		}),
	),
	concurrency: Type.Optional(
		Type.Number({
			description:
				"Maximum concurrent agents for this run. Clamped to the runtime maximum. Use when provider/transport stability matters.",
		}),
	),
	agentRetries: Type.Optional(
		Type.Number({
			description:
				"Retry attempts for recoverable agent failures such as timeout, connection failure, or empty assistant output. Default 0 unless configured.",
		}),
	),
	agentTimeoutMs: Type.Optional(
		Type.Number({
			description:
				"Timeout per agent in milliseconds. Omit for no hard timeout by default. Set only when the user asks to bound time.",
		}),
	),
	tokenBudget: Type.Optional(
		Type.Number({
			description:
				"Hard total-token budget for the whole run. Once spent reaches it, further agent() calls fail and the run stops. Omit for no limit. Set it when the user asks to cap spend.",
		}),
	),
});

export type WorkflowToolInput = {
	script: string;
	args?: unknown;
	background?: boolean;
	maxAgents?: number;
	concurrency?: number;
	agentRetries?: number;
	agentTimeoutMs?: number;
	tokenBudget?: number;
};

export interface WorkflowToolOptions {
	cwd?: string;
	concurrency?: number;
	/** Shared manager so background runs are reachable from the `/workflows` command. */
	manager?: WorkflowManager;
	/** Shared saved-workflow storage. */
	storage?: WorkflowStorage;
	/** Default per-agent timeout for runs created by this tool. null means no hard timeout. */
	defaultAgentTimeoutMs?: number | null;
	/** Default max concurrent agents when no tool-level concurrency is passed. */
	defaultConcurrency?: number;
	/** Default retry attempts after recoverable agent failures. */
	defaultAgentRetries?: number;
}

export function createWorkflowTool(options: WorkflowToolOptions = {}): ToolDefinition<typeof workflowToolSchema, any> {
	const storage = options.storage ?? createWorkflowStorage(options.cwd ?? process.cwd());
	const cwd = options.cwd ?? process.cwd();
	const defaults = resolveWorkflowToolDefaults(options, cwd);
	const manager =
		options.manager ??
		new WorkflowManager({
			cwd: options.cwd,
			concurrency: defaults.concurrency,
			loadSavedWorkflow: (name: string) => storage.load(name)?.script,
			defaultAgentTimeoutMs: defaults.agentTimeoutMs,
			defaultAgentRetries: defaults.agentRetries,
		});

	return defineTool({
		name: "workflow",
		label: "DisCo Workflow",
		description: [
			"Execute a deterministic JavaScript workflow that orchestrates multiple subagents with agent(), parallel(), and pipeline().",
			"Use it only for deliberately decomposable work that benefits from coordinated subagents.",
			"script is required raw JavaScript. It must start with export const meta = { name, description, phases? } and must call agent() at least once.",
		].join(" "),
		promptSnippet:
			"Run a deterministic JavaScript workflow. Required script header: export const meta = { name: 'short_snake_case', description: 'non-empty description', phases: [{ title: 'Phase' }] }.",
		promptGuidelines: [
			"Use workflow only when coordinated subagents materially help or the user explicitly requests parallel or dynamic workflow execution; use ordinary tools for simple sequential work.",
			"Follow the workflow tool schema for script syntax, execution options, and result handling.",
			"Give every agent a focused task and a concise label; choose a tier that fits its role when using tiered routing.",
			modelRoutingGuideline(),
			agentTypeGuideline(),
			"For workflow, runs are background by default: the tool returns immediately with a run ID, the turn ends so the user isn't blocked, and the result is delivered back into the conversation when the run finishes. Pass background: false only when you must use the result inline in this same turn (it will block).",
			"For workflow, you may call `await workflow('saved-name', argsObject)` to run a saved workflow inline and use its result; nesting is one level deep only, and the global 16-concurrent / 1000-total caps hold across the nesting.",
		].filter((g): g is string => typeof g === "string" && g.length > 0),
		parameters: workflowToolSchema,
		prepareArguments(args) {
			return normalizeWorkflowToolArgs(args);
		},
		async execute(_toolCallId, params, signal, onUpdate, ctx) {
			const script = normalizeWorkflowScript(params.script);
			const parsed = parseWorkflowScript(script);

			// checkpoint() reaches the human only on a UI-bearing foreground run; a
			// background run is detached, so checkpoint() falls back to its headless
			// default. Map a checkpoint to ctx.ui.confirm (a yes/no gate) when available.
			const uiCtx = ctx as
				| { hasUI?: boolean; ui?: { confirm?(title: string, message: string): Promise<boolean> } }
				| undefined;
			const uiConfirm = uiCtx?.hasUI ? uiCtx.ui?.confirm : undefined;
			const confirm = uiConfirm
				? (promptText: string) => uiConfirm.call(uiCtx?.ui, "Workflow checkpoint", promptText)
				: undefined;

			// Background execution is the default: return immediately so the turn ends
			// and the user isn't blocked. The result is delivered back into the
			// conversation when the run finishes (see installResultDelivery). Only an
			// explicit `background: false` blocks for the result inline.
			if (params.background ?? true) {
				const { runId } = manager.startInBackground(script, params.args, {
					maxAgents: params.maxAgents,
					concurrency: params.concurrency,
					agentRetries: params.agentRetries,
					agentTimeoutMs: params.agentTimeoutMs,
					tokenBudget: params.tokenBudget,
				});
				return {
					content: [{ type: "text", text: backgroundStartedText(parsed.meta.name, runId) }],
					details: { runId, background: true },
				};
			}

			// Synchronous execution (blocking) — but routed through the manager so the
			// run shows up live in the /workflows navigator and the task panel while it
			// runs, then stays in history afterwards. We still block on the result and
			// return it inline, so the model gets the full output in the same turn.
			let snapshot: WorkflowSnapshot = createWorkflowSnapshot(parsed.meta);
			const display = createToolUpdateWorkflowDisplay(onUpdate, undefined, {
				key: "workflow",
				streamToolUpdates: true,
				maxAgents: 4,
				showResultPreviews: false,
			});

			let result: WorkflowRunResult;
			try {
				result = await manager.runSync(script, params.args, {
					maxAgents: params.maxAgents,
					concurrency: params.concurrency,
					agentRetries: params.agentRetries,
					agentTimeoutMs: params.agentTimeoutMs,
					tokenBudget: params.tokenBudget,
					confirm,
					externalSignal: signal,
					onProgress(live) {
						snapshot = recomputeWorkflowSnapshot(live);
						display.update(snapshot);
					},
				});
			} catch (error) {
				if (
					signal?.aborted ||
					(error instanceof WorkflowError && error.code === WorkflowErrorCode.WORKFLOW_ABORTED)
				) {
					for (const agent of snapshot.agents) {
						if (agent.status === "running") {
							agent.status = "skipped";
							agent.error = "aborted";
						}
					}
					snapshot = recomputeWorkflowSnapshot(snapshot);
					display.complete(snapshot);
					throw new Error("Workflow was aborted");
				}
				throw error;
			}

			if (result.agentCount === 0) {
				throw new Error(
					"workflow scripts must call agent() at least once; this workflow declared phases but did not run any subagents",
				);
			}

			snapshot.result = result.result;
			snapshot.durationMs = result.durationMs;
			snapshot = recomputeWorkflowSnapshot(snapshot);
			display.complete(snapshot);

			// Format token usage (include cost when the provider reports it)
			const tokenInfo = result.tokenUsage
				? `\n\nToken usage: ${result.tokenUsage.total.toLocaleString()} tokens${
						result.tokenUsage.cost ? ` ($${result.tokenUsage.cost.toFixed(4)})` : ""
					}`
				: "";

			const formattedResult =
				result.result !== undefined ? `\n\`\`\`json\n${JSON.stringify(result.result, null, 2)}\n\`\`\`` : "";

			return {
				content: [
					{
						type: "text",
						text: `Workflow **${result.meta.name}** completed with **${result.agentCount}** agent(s).${tokenInfo}\n\n## Result${formattedResult}`,
					},
				],
				details: {
					...snapshot,
					meta: result.meta,
					phases: result.phases,
					logs: result.logs,
					result: result.result,
					durationMs: result.durationMs,
					tokenUsage: result.tokenUsage,
					runId: result.runId,
				},
			};
		},
		renderCall(_args, theme) {
			return new Text(theme.fg("toolTitle", theme.bold("workflow")), 0, 0);
		},
		renderResult(result, { isPartial }, theme) {
			const snapshot = result.details as WorkflowSnapshot | undefined;
			if (snapshot?.name) {
				return new Text(renderWorkflowText(snapshot, !isPartial), 0, 0);
			}
			// Fallback: strip markdown syntax so the TUI doesn't display raw asterisks/hashes.
			// The `content` field is for the LLM (where markdown is preserved), but the TUI
			// renderer (Text component) shows text literally — so we strip markdown here.
			const text = result.content?.[0];
			const raw = text?.type === "text" ? text.text : theme.fg("muted", "workflow");
			const clean = raw
				.replace(/\*\*/g, "")
				.replace(/```[a-z]*\n/g, "")
				.replace(/```/g, "")
				.replace(/^##+\s*/gm, "")
				.trim();
			return new Text(clean || theme.fg("muted", "workflow"), 0, 0);
		},
	});
}

function resolveWorkflowToolDefaults(
	options: WorkflowToolOptions,
	cwd: string,
): { agentTimeoutMs: number | null; concurrency?: number; agentRetries: number } {
	const settings = loadWorkflowSettings({ cwd });
	return {
		agentTimeoutMs:
			options.defaultAgentTimeoutMs !== undefined
				? options.defaultAgentTimeoutMs
				: (settings.defaultAgentTimeoutMs ?? null),
		concurrency: options.defaultConcurrency ?? options.concurrency ?? settings.defaultConcurrency,
		agentRetries: options.defaultAgentRetries ?? settings.defaultAgentRetries ?? 0,
	};
}

/**
 * The tool result returned when a workflow starts in the background. It both
 * informs the model and tells it to reassure the user: the run continues on its
 * own and the conversation will resume automatically when it finishes, so the
 * user can just wait here (or go do something else).
 */
export function backgroundStartedText(name: string, runId: string): string {
	return [
		`Workflow "${name}" started in the background.`,
		`Run ID: ${runId}`,
		"It keeps running on its own. When it finishes, the result is delivered back",
		"here and the conversation continues automatically — the user does not need to",
		"do anything. Tell the user they can simply wait here for it to finish (it will",
		"resume the conversation by itself), or keep chatting / working on other things",
		"in the meantime; either way the result will come back to this conversation.",
		`They can also track or cancel it with /workflows status ${runId} or /workflows stop ${runId}.`,
	].join("\n");
}

function normalizeWorkflowToolArgs(args: unknown): WorkflowToolInput {
	if (!args || typeof args !== "object") throw new Error("workflow requires an object argument with a script string");
	const value = args as Record<string, unknown>;
	if (typeof value.script !== "string") throw new Error("workflow requires `script` to be a string");
	return { ...value, script: normalizeWorkflowScript(value.script) } as WorkflowToolInput;
}

function normalizeWorkflowScript(script: string): string {
	let text = script.trim();
	const fence = text.match(/^```(?:js|javascript)?\s*\n([\s\S]*?)\n```$/i);
	if (fence) text = fence[1].trim();
	return text;
}

function _isAbortError(error: unknown): boolean {
	if (!(error instanceof Error)) return false;
	return /\babort(?:ed)?\b/i.test(error.message);
}
