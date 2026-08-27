/**
 * Saved workflows as `/<name>` slash commands. Each saved workflow becomes a
 * command that runs its script, passing parsed arguments through as `args`.
 */

import type { ExtensionAPI, ExtensionCommandContext } from "../../core/extensions/types.ts";
import { createCodingTools } from "../../core/tools/index.ts";
import { runWorkflow, type WorkflowRunResult } from "./workflow.ts";
import type { WorkflowManager } from "./workflow-manager.ts";
import type { SavedWorkflow, WorkflowStorage } from "./workflow-saved.ts";

function isRegistered(pi: ExtensionAPI, name: string): boolean {
	try {
		return (pi.getCommands?.() ?? []).some((c: { name: string }) => c.name === name);
	} catch {
		return false;
	}
}

function reportText(result: WorkflowRunResult): string {
	const r = result.result as { report?: unknown } | undefined;
	if (r && typeof r.report === "string" && r.report.trim()) return r.report;
	return JSON.stringify(result.result, null, 2);
}

/**
 * Parse a command argument string into an `args` object for the script.
 * Supports `key=value` tokens; everything else collects into `_` (and `_raw`).
 * Declared parameter defaults fill in missing keys.
 */
export function parseCommandArgs(raw: string, parameters?: SavedWorkflow["parameters"]): Record<string, unknown> {
	const out: Record<string, unknown> = {};
	const positional: string[] = [];
	for (const tok of raw.trim().split(/\s+/).filter(Boolean)) {
		const eq = tok.indexOf("=");
		if (eq > 0) out[tok.slice(0, eq)] = tok.slice(eq + 1);
		else positional.push(tok);
	}
	out._ = positional.join(" ");
	out._raw = raw.trim();
	for (const [key, spec] of Object.entries(parameters ?? {})) {
		if (out[key] === undefined && spec.default !== undefined) out[key] = spec.default;
	}
	return out;
}

/** Register one saved workflow as a `/<name>` command (idempotent).
 * When a WorkflowManager is provided, the workflow runs through it (visible in
 * /workflows TUI, background execution, task panel). Otherwise falls back to
 * the inline runWorkflow() (foreground, no TUI tracking).
 *
 * DisCo has no `unregisterCommand`, so a command cannot be removed mid-session
 * after its workflow is deleted (it is correctly gone on next launch, since
 * registerAllSavedWorkflows only registers what's in storage). The optional
 * `exists` predicate lets the handler detect that case at invocation time and
 * tell the user to reload rather than silently re-running a deleted workflow. */
export function registerSavedWorkflow(
	pi: ExtensionAPI,
	cwd: string,
	wf: SavedWorkflow,
	manager?: WorkflowManager,
	exists?: () => boolean,
): void {
	if (isRegistered(pi, wf.name)) return;
	pi.registerCommand(wf.name, {
		description: wf.description || `Saved workflow: ${wf.name}`,
		async handler(args: string, ctx: ExtensionCommandContext) {
			if (exists && !exists()) {
				ctx.ui.notify(`/${wf.name} was deleted — reload the session to remove this command.`, "warning");
				return;
			}
			try {
				ctx.ui.notify(`Starting /${wf.name}…`, "info");

				let result: WorkflowRunResult;
				if (manager) {
					// Run through the WorkflowManager: background execution, visible in
					// /workflows TUI, task panel, pause/resume/stop support.
					const { runId, promise } = manager.startInBackground(wf.script, parseCommandArgs(args, wf.parameters));
					ctx.ui.setStatus(`wf:${wf.name}`, `${wf.name}: running (${runId})`);
					result = await promise;
				} else {
					// Fallback: inline runWorkflow (foreground, no TUI tracking).
					result = await runWorkflow(wf.script, {
						cwd,
						args: parseCommandArgs(args, wf.parameters),
						tools: createCodingTools(cwd),
						onPhase: (title) => ctx.ui.setStatus(`wf:${wf.name}`, `${wf.name}: ${title}`),
					});
				}

				ctx.ui.setStatus(`wf:${wf.name}`, undefined);
				await pi.sendMessage({ customType: `workflow:${wf.name}`, content: reportText(result), display: true });
			} catch (error) {
				ctx.ui.setStatus(`wf:${wf.name}`, undefined);
				ctx.ui.notify(`/${wf.name} failed: ${error instanceof Error ? error.message : error}`, "error");
			}
		},
	});
}

/** Register every saved workflow found in storage.
 * When a WorkflowManager is provided, workflows run through it (visible in
 * /workflows TUI, background execution, task panel). */
export function registerAllSavedWorkflows(
	pi: ExtensionAPI,
	cwd: string,
	storage: WorkflowStorage,
	manager?: WorkflowManager,
): void {
	for (const wf of storage.list()) {
		registerSavedWorkflow(pi, cwd, wf, manager, () => storage.list().some((w) => w.name === wf.name));
	}
}
