/**
 * Workflow manager for background execution, pause/resume, and run management.
 */

import { EventEmitter } from "node:events";
import type { ModelRegistry } from "../../core/model-registry.ts";
import { DEFAULT_DISCO_AGENT_MODE, type DiscoAgentMode } from "../modes/types.ts";
import type { WorkflowAgent } from "./agent.ts";
import {
	DEFAULT_AGENT_RETRIES,
	DEFAULT_MAX_RECOVERY_ROUNDS,
	MAX_AGENT_RETRIES,
	MAX_AGENTS_PER_RUN,
	MAX_CONCURRENCY,
	MAX_RECOVERY_ROUNDS,
} from "./config.ts";
import type { TokenUsageTotals } from "./agent-usage.ts";
import {
	preview,
	recomputeWorkflowSnapshot,
	type WorkflowAgentSnapshot,
	type WorkflowSnapshot,
} from "./display.ts";
import { WorkflowError, WorkflowErrorCode, wrapError } from "./errors.ts";
import {
	createRunPersistence,
	generateRunId,
	type PersistedAgentState,
	type PersistedRunLimits,
	type PersistedRunState,
	type RunLease,
	type RunPersistence,
	type RunStatus,
} from "./run-persistence.ts";
import {
	extractWorkflowCoverage,
	type JournalEntry,
	parseWorkflowScript,
	runWorkflow,
	type WorkflowRunResult,
} from "./workflow.ts";

export interface ManagedRun {
	runId: string;
	status: RunStatus;
	snapshot: WorkflowSnapshot;
	result?: WorkflowRunResult;
	error?: WorkflowError;
	controller: AbortController;
	startedAt: Date;
	/** The real script, kept so the run can be resumed. */
	script: string;
	args?: unknown;
	/** Accumulated agent results for resume (deterministic call index -> result). */
	journal: JournalEntry[];
	/** Cross-process execution lease for this run, when it is actively executing. */
	lease?: RunLease;
	/** Resolved limits captured at creation and reused on resume. */
	limits: PersistedRunLimits;
	recoveryOfRunId?: string;
	recoveryRound?: number;
	/** Resolves once the current executeRun invocation has fully drained. */
	settled?: Promise<void>;
	/**
	 * True when the run was started in the background (or resumed) and the caller is
	 * not awaiting its result inline. Only background runs deliver their result back
	 * into the conversation; a foreground sync run already returns it as the tool
	 * result, so re-delivering would duplicate it.
	 */
	background: boolean;
}

/** Per-execution options shared by sync, background, and resume runs. */
export interface ExecOptions {
	/** Replay these journaled agent results for the unchanged prefix (resume). */
	resumeJournal?: Map<number, JournalEntry>;
	/** Cap on total agents for this run. */
	maxAgents?: number;
	/** Per-agent timeout in milliseconds. null/omitted means no hard timeout. */
	agentTimeoutMs?: number | null;
	/** Host signal (e.g. tool/Esc) that should abort this run when fired. */
	externalSignal?: AbortSignal;
	/** Called with the live snapshot on every progress event. */
	onProgress?: (snapshot: WorkflowSnapshot) => void;
	/** Hard token budget for this run; once spent reaches it, agent() throws. */
	tokenBudget?: number | null;
	/** Max concurrent agents for this execution. */
	concurrency?: number;
	/** Retry attempts after recoverable agent failures for this execution. */
	agentRetries?: number;
	/** Maximum recovery rounds for recoverMissing(). */
	maxRecoveryRounds?: number;
	/** Parent run ID when this is a recovery workflow. */
	recoveryOfRunId?: string;
	/** Recovery round number when this is a recovery workflow. */
	recoveryRound?: number;
	/** Seed usage when resuming a persisted run. */
	initialTokenUsage?: TokenUsageTotals;
	/** Preflight diagnostics that must be persisted and shown with the workflow run. */
	initialLogs?: string[];
	/** Resolve a checkpoint() question with a human reply (only for UI-bearing runs). */
	confirm?: (promptText: string, options: unknown) => Promise<unknown>;
}

export interface WorkflowManagerOptions {
	cwd?: string;
	concurrency?: number;
	/** Resolve a saved-workflow name to its script, enabling nested `workflow('name')`. */
	loadSavedWorkflow?: (name: string) => string | undefined;
	/** Inject a custom agent runner (tests); defaults to a real subagent session. */
	agent?: Pick<WorkflowAgent, "run">;
	/** The session's main model (provider/id), for auto-tiering explore agents. */
	mainModel?: string;
	/** Current session model registry used by real subagent runners. */
	modelRegistry?: ModelRegistry;
	/** The pi session id to tag runs with (see setSessionId). */
	sessionId?: string;
	/** Default per-agent timeout when a run does not pass agentTimeoutMs. null means no hard timeout. */
	defaultAgentTimeoutMs?: number | null;
	/** Default retry attempts after recoverable agent failures. */
	defaultAgentRetries?: number;
	/** Parent session mode inherited by every workflow subagent. */
	discoMode?: DiscoAgentMode;
}

export class WorkflowManager extends EventEmitter {
	private runs = new Map<string, ManagedRun>();
	private persistence: RunPersistence;
	private cwd: string;
	private concurrency: number;
	private loadSavedWorkflow?: (name: string) => string | undefined;
	private agent?: Pick<WorkflowAgent, "run">;
	/** The session's main model (provider/id), for auto-tiering explore agents. */
	private mainModel?: string;
	private modelRegistry?: ModelRegistry;
	/** The current pi session id; runs are stamped with it and listRuns() filters by it. */
	private sessionId?: string;
	private defaultAgentTimeoutMs: number | null;
	private defaultAgentRetries?: number;
	private discoMode: DiscoAgentMode;

	constructor(options: WorkflowManagerOptions = {}) {
		super();
		this.cwd = options.cwd ?? process.cwd();
		this.concurrency = options.concurrency ?? 8;
		this.loadSavedWorkflow = options.loadSavedWorkflow;
		this.agent = options.agent;
		this.mainModel = options.mainModel;
		this.modelRegistry = options.modelRegistry;
		this.sessionId = options.sessionId;
		this.defaultAgentTimeoutMs = options.defaultAgentTimeoutMs ?? null;
		this.defaultAgentRetries = options.defaultAgentRetries;
		this.discoMode = options.discoMode ?? DEFAULT_DISCO_AGENT_MODE;
		this.persistence = createRunPersistence(this.cwd);
		this.recoverStaleRuns();
	}

	/** Bind the manager to the current pi session, so new runs are tagged with it and
	 * the navigator/task-panel show only this session's runs (set on session_start). */
	setSessionId(id: string | undefined): void {
		this.sessionId = id;
	}

	/**
	 * On startup, any persisted run still marked "running" belongs to a process
	 * that died mid-run (this fresh manager has it nowhere in memory). Reconcile it
	 * to "paused" — never "failed" — so its journal is preserved and resume() can
	 * replay the completed prefix and finish the rest.
	 */
	private recoverStaleRuns(): void {
		try {
			for (const p of this.listAllRuns()) {
				if (p.status === "running" && !this.runs.has(p.runId)) {
					const lease = this.persistence.acquireRunLease(p.runId);
					if (!lease) continue;
					try {
						this.persistence.save({ ...p, status: "paused" });
					} finally {
						this.persistence.releaseRunLease(lease);
					}
				}
			}
		} catch {
			// Recovery is best-effort; never let it block manager construction.
		}
	}

	/** Set the session's main model (provider/id). Used to auto-tier explore agents. */
	setMainModel(spec: string | undefined): void {
		this.mainModel = spec;
	}

	setModelRegistry(modelRegistry: ModelRegistry): void {
		this.modelRegistry = modelRegistry;
	}

	private resolveLimits(exec: ExecOptions): PersistedRunLimits {
		const maxAgents = normalizePositiveInteger(exec.maxAgents ?? MAX_AGENTS_PER_RUN, 1, MAX_AGENTS_PER_RUN);
		const concurrency = normalizePositiveInteger(exec.concurrency ?? this.concurrency, 1, MAX_CONCURRENCY);
		const agentTimeoutMs = exec.agentTimeoutMs !== undefined ? exec.agentTimeoutMs : this.defaultAgentTimeoutMs;
		const configuredRetries = exec.agentRetries !== undefined ? exec.agentRetries : this.defaultAgentRetries;
		const agentRetries = normalizeInteger(
			configuredRetries ?? (agentTimeoutMs !== null ? DEFAULT_AGENT_RETRIES : 0),
			0,
			MAX_AGENT_RETRIES,
		);
		const maxRecoveryRounds = normalizePositiveInteger(
			exec.maxRecoveryRounds ?? DEFAULT_MAX_RECOVERY_ROUNDS,
			1,
			MAX_RECOVERY_ROUNDS,
		);
		return {
			maxAgents,
			concurrency,
			agentTimeoutMs,
			agentRetries,
			tokenBudget: exec.tokenBudget !== undefined ? exec.tokenBudget : null,
			maxRecoveryRounds,
		};
	}

	/**
	 * Start a workflow in the background.
	 * Returns immediately with a run ID; the workflow executes asynchronously.
	 */
	startInBackground(
		script: string,
		args?: unknown,
		exec: ExecOptions = {},
	): { runId: string; promise: Promise<WorkflowRunResult> } {
		const runId = generateRunId();
		const controller = new AbortController();
		const parsed = parseWorkflowScript(script);
		const limits = this.resolveLimits(exec);
		const lease = this.persistence.acquireRunLease(runId);
		if (!lease) throw new Error(`Could not acquire workflow run lease for ${runId}`);

		const managed: ManagedRun = {
			runId,
			status: "running",
			snapshot: {
				name: parsed.meta.name,
				description: parsed.meta.description,
				phases: parsed.meta.phases?.map((p) => p.title) ?? [],
				logs: [],
				agents: [],
				agentCount: 0,
				runningCount: 0,
				doneCount: 0,
				errorCount: 0,
			},
			controller,
			startedAt: new Date(),
			script,
			args,
			journal: [],
			background: true,
			lease,
			limits,
		};

		this.runs.set(runId, managed);

		try {
			// Persist initial state
			this.persistence.save({
				runId,
				workflowName: parsed.meta.name,
				script,
				args,
				sessionId: this.sessionId,
				status: "running",
				...persistedLimitFields(limits),
				recoveryOfRunId: exec.recoveryOfRunId,
				recoveryRound: exec.recoveryRound,
				maxRecoveryRounds: limits.maxRecoveryRounds,
				phases: managed.snapshot.phases,
				agents: [],
				logs: [],
				startedAt: managed.startedAt.toISOString(),
				updatedAt: managed.startedAt.toISOString(),
			});
		} catch (err) {
			this.releaseRunLease(managed);
			this.runs.delete(runId);
			throw err;
		}

		// Run workflow asynchronously.
		// Attach a side-channel catch to prevent Node.js unhandled-rejection crashes
		// when a workflow is aborted/paused/stopped — executeRun()'s catch block
		// already records status/event/persist, but the promise still rejects.
		// The original promise is returned so callers can await it in try/catch.
		const promise = this.executeRun(managed, script, args, exec);
		managed.settled = promise.then(() => undefined, () => undefined);
		promise.catch(() => {});

		return { runId, promise };
	}

	/**
	 * Execute a workflow synchronously (blocking) while still tracking it like a
	 * background run, so the `/workflows` navigator and the live task panel see it.
	 * `onProgress` fires on every progress event with the current snapshot, letting
	 * a caller (e.g. the workflow tool) drive its own inline display.
	 */
	async runSync(script: string, args?: unknown, exec: ExecOptions = {}): Promise<WorkflowRunResult> {
		const managed = this.createManaged(script, args, this.resolveLimits(exec), exec);
		const lease = this.persistence.acquireRunLease(managed.runId);
		if (!lease) throw new Error(`Could not acquire workflow run lease for ${managed.runId}`);
		managed.lease = lease;
		this.runs.set(managed.runId, managed);
		// Persist the initial state immediately so listRuns()/the task panel can see
		// the run the moment it starts, not only after the first agent journals.
		this.persistRun(managed);
		const promise = this.executeRun(managed, script, args, exec);
		managed.settled = promise.then(() => undefined, () => undefined);
		return promise;
	}

	/** Build a fresh managed run with an empty snapshot. */
	private createManaged(
		script: string,
		args: unknown,
		limits: PersistedRunLimits,
		exec: ExecOptions = {},
	): ManagedRun {
		const parsed = parseWorkflowScript(script);
		return {
			runId: generateRunId(),
			status: "running",
			snapshot: {
				name: parsed.meta.name,
				description: parsed.meta.description,
				phases: parsed.meta.phases?.map((p) => p.title) ?? [],
				logs: [],
				agents: [],
				agentCount: 0,
				runningCount: 0,
				doneCount: 0,
				errorCount: 0,
			},
			controller: new AbortController(),
			startedAt: new Date(),
			script,
			args,
			journal: [],
			background: false,
			limits,
			recoveryOfRunId: exec.recoveryOfRunId,
			recoveryRound: exec.recoveryRound,
		};
	}

	private async executeRun(
		managed: ManagedRun,
		script: string,
		args?: unknown,
		exec: ExecOptions = {},
	): Promise<WorkflowRunResult> {
		const {
			resumeJournal,
			maxAgents,
			agentTimeoutMs,
			externalSignal,
			onProgress,
			tokenBudget,
			concurrency,
			agentRetries,
			maxRecoveryRounds,
			recoveryOfRunId,
			recoveryRound,
			initialTokenUsage,
			confirm,
		} = exec;
		const resolvedLimits: PersistedRunLimits = {
			maxAgents: maxAgents !== undefined ? normalizePositiveInteger(maxAgents, 1, MAX_AGENTS_PER_RUN) : managed.limits.maxAgents,
			concurrency: concurrency !== undefined ? normalizePositiveInteger(concurrency, 1, MAX_CONCURRENCY) : managed.limits.concurrency,
			agentTimeoutMs: agentTimeoutMs !== undefined ? agentTimeoutMs : managed.limits.agentTimeoutMs,
			agentRetries: agentRetries !== undefined ? normalizeInteger(agentRetries, 0, MAX_AGENT_RETRIES) : managed.limits.agentRetries,
			tokenBudget: tokenBudget !== undefined ? tokenBudget : managed.limits.tokenBudget,
			maxRecoveryRounds:
				maxRecoveryRounds !== undefined
					? normalizePositiveInteger(maxRecoveryRounds, 1, MAX_RECOVERY_ROUNDS)
					: managed.limits.maxRecoveryRounds,
		};
		managed.limits = resolvedLimits;
		managed.recoveryOfRunId = recoveryOfRunId ?? managed.recoveryOfRunId;
		managed.recoveryRound = recoveryRound ?? managed.recoveryRound;
		if (initialTokenUsage && !managed.snapshot.tokenUsage) managed.snapshot.tokenUsage = initialTokenUsage;
		const refreshSnapshotCounts = () => {
			managed.snapshot = recomputeWorkflowSnapshot(managed.snapshot);
		};
		const progress = () => {
			refreshSnapshotCounts();
			onProgress?.(managed.snapshot);
		};
		// Let a host abort (e.g. Esc during a blocking tool call) cancel this run.
		if (externalSignal) {
			if (externalSignal.aborted) managed.controller.abort();
			else externalSignal.addEventListener("abort", () => managed.controller.abort(), { once: true });
		}
		try {
			const result = await runWorkflow(script, {
				cwd: this.cwd,
				discoMode: this.discoMode,
				args,
				agent: this.agent,
				mainModel: this.mainModel,
				modelRegistry: this.modelRegistry,
				signal: managed.controller.signal,
				concurrency: resolvedLimits.concurrency,
				agentRetries: resolvedLimits.agentRetries,
				maxAgents: resolvedLimits.maxAgents,
				agentTimeoutMs: resolvedLimits.agentTimeoutMs,
				tokenBudget: resolvedLimits.tokenBudget,
				maxRecoveryRounds: resolvedLimits.maxRecoveryRounds,
				recoveryOfRunId: managed.recoveryOfRunId,
				recoveryRound: managed.recoveryRound,
				initialTokenUsage,
				initialLogs: exec.initialLogs,
				runId: managed.runId,
				confirm,
				loadSavedWorkflow: this.loadSavedWorkflow,
				resumeJournal,
				resumeFromRunId: resumeJournal ? managed.runId : undefined,
				onAgentJournal: (entry) => {
					// Append (crash-safe-ish): keep the latest entry per index, then persist.
					managed.journal = managed.journal.filter((e) => e.index !== entry.index);
					managed.journal.push(entry);
					this.persistRun(managed);
				},
				onLog: (message) => {
					managed.snapshot.logs.push(message);
					this.emit("log", { runId: managed.runId, message });
					progress();
				},
				onPhase: (title) => {
					managed.snapshot.currentPhase = title;
					if (!managed.snapshot.phases.includes(title)) {
						managed.snapshot.phases.push(title);
					}
					this.emit("phase", { runId: managed.runId, title });
					progress();
				},
				onAgentStart: (event) => {
					const existing = findSnapshotAgent(managed.snapshot.agents, event);
					if (existing) {
						existing.stableId = event.stableId;
						existing.callIndex = event.callIndex;
						existing.label = event.label;
						existing.subSkill = event.subSkill;
						existing.phase = event.phase;
						existing.prompt = event.prompt;
						existing.status = "running";
						existing.error = undefined;
						existing.errorCode = undefined;
						existing.recoverable = undefined;
						if (event.model) existing.model = event.model;
					} else {
						managed.snapshot.agents.push({
							id: nextAgentId(managed.snapshot.agents),
							stableId: event.stableId,
							callIndex: event.callIndex,
							label: event.label,
							subSkill: event.subSkill,
							phase: event.phase,
							prompt: event.prompt,
							status: "running",
							model: event.model,
						});
					}
					this.emit("agentStart", { runId: managed.runId, ...event });
					this.persistRun(managed);
					progress();
				},
				onAgentAttemptEnd: (event) => {
					const agent = findSnapshotAgent(managed.snapshot.agents, event, true);
					if (agent) {
						agent.tokens = (agent.tokens ?? 0) + event.tokens;
						agent.attempts ??= [];
						const priorAttempt = agent.attempts.reduce((max, item) => Math.max(max, item.attempt), 0);
						agent.attempts.push({
							attempt: priorAttempt + 1,
							status: event.result === null ? "error" : "done",
							tokens: event.tokens,
							usage: event.usage,
							error: event.error,
							errorCode: event.errorCode,
							recoverable: event.recoverable,
							endedAt: new Date().toISOString(),
						});
					}
					if (event.usage) addSnapshotUsage(managed.snapshot, event.usage);
					this.emit("agentAttemptEnd", { runId: managed.runId, ...event });
					this.persistRun(managed);
					progress();
				},
				onAgentEnd: (event) => {
					const agent = findSnapshotAgent(managed.snapshot.agents, event, true);
					if (agent) {
						agent.status = event.result === null ? "error" : "done";
						agent.resultPreview = preview(event.result);
						agent.error = event.error;
						agent.errorCode = event.errorCode;
						agent.recoverable = event.recoverable;
						if (event.tokens !== undefined && !agent.attempts?.length) agent.tokens = event.tokens;
						if (event.model) agent.model = event.model;
					}
					this.emit("agentEnd", { runId: managed.runId, ...event });
					this.persistRun(managed);
					progress();
				},
				onAgentHistory: (event) => {
					const agent = findSnapshotAgent(managed.snapshot.agents, event, true);
					if (agent) {
						agent.history = event.history;
					}
					this.emit("agentHistory", { runId: managed.runId, ...event });
					progress();
				},
				onTokenUsage: (usage, info) => {
					if (info?.source === "live") managed.snapshot.liveTokenUsage = normalizeTokenUsage(usage);
					else managed.snapshot.tokenUsage = usage;
					this.emit("tokenUsage", { runId: managed.runId, usage, info });
					progress();
				},
			});

			managed.result = result;
			managed.snapshot.result = result.result;
			managed.snapshot.durationMs = result.durationMs;
			managed.snapshot.runId = result.runId;
			managed.snapshot.complete = result.complete;
			managed.snapshot.missing = result.missing;
			managed.snapshot.errors = result.errors;
			const coverage = extractWorkflowCoverage(result.result);
			if (coverage && !coverage.complete) {
				managed.status = "failed";
				managed.error = new WorkflowError(
					`Workflow returned incomplete coverage; missing: ${coverage.missing.join(", ") || "unknown"}`,
					WorkflowErrorCode.WORKFLOW_INCOMPLETE,
					{ recoverable: true, details: coverage },
				);
				managed.snapshot.error = managed.error.message;
				managed.snapshot.errorCode = managed.error.code;
				managed.snapshot.recoverable = managed.error.recoverable;
				this.emit("incomplete", { runId: managed.runId, result, coverage });
			} else {
				managed.status = "completed";
				managed.error = undefined;
				managed.snapshot.error = undefined;
				managed.snapshot.errorCode = undefined;
				managed.snapshot.recoverable = undefined;
				this.emit("complete", { runId: managed.runId, result });
			}

			// Persist final state
			this.persistRun(managed);
			return result;
		} catch (error) {
			let workflowError = error instanceof WorkflowError ? error : wrapError(error);

			if (managed.controller.signal.aborted) {
				// Intentional abort (pause/stop/Esc) — preserve status set by pause()/stop()
				if (managed.status === "running") {
					managed.status = "aborted";
				}
				workflowError = new WorkflowError(
					managed.status === "paused" ? "workflow paused" : "workflow aborted",
					WorkflowErrorCode.WORKFLOW_ABORTED,
					{ recoverable: managed.status === "paused" },
				);
			} else {
				managed.status = "failed";
			}
			managed.error = workflowError;
			managed.snapshot.error = workflowError.message;
			managed.snapshot.errorCode = workflowError.code;
			managed.snapshot.recoverable = workflowError.recoverable;
			if (managed.status !== "paused" && managed.status !== "aborted") {
				if (this.listenerCount("error") > 0) {
					this.emit("error", { runId: managed.runId, error: workflowError });
				}
			}

			// Persist final state
			throw workflowError;
		} finally {
			this.persistRun(managed);
			this.releaseRunLease(managed);
		}
	}

	private releaseRunLease(managed: ManagedRun): void {
		if (!managed.lease) return;
		this.persistence.releaseRunLease(managed.lease);
		managed.lease = undefined;
	}

	private persistRun(managed: ManagedRun) {
		try {
			managed.snapshot = recomputeWorkflowSnapshot(managed.snapshot);
			this.persistence.save({
				runId: managed.runId,
				workflowName: managed.snapshot.name,
				// Persist the real script + journal so the run can be resumed. Runs live
				// in workflow run storage — protect via directory permissions, not blanking.
				script: managed.script,
				args: managed.args,
				sessionId: this.sessionId,
				journal: managed.journal,
				status: managed.status,
				...persistedLimitFields(managed.limits),
				recoveryOfRunId: managed.recoveryOfRunId,
				recoveryRound: managed.recoveryRound,
				phases: managed.snapshot.phases,
				currentPhase: managed.snapshot.currentPhase,
				agents: managed.snapshot.agents.map((a) => ({
					...a,
					startedAt: managed.startedAt.toISOString(),
					endedAt: new Date().toISOString(),
				})),
				logs: managed.snapshot.logs,
				result: managed.result?.result,
				complete: managed.result?.complete ?? managed.snapshot.complete,
				missing: managed.result?.missing ?? managed.snapshot.missing,
				errors: managed.result?.errors ?? managed.snapshot.errors,
				error: managed.error?.message ?? managed.snapshot.error,
				errorCode: managed.error?.code ?? managed.snapshot.errorCode,
				recoverable: managed.error?.recoverable ?? managed.snapshot.recoverable,
				tokenUsage: managed.snapshot.tokenUsage
					? {
							input: managed.snapshot.tokenUsage.input,
							output: managed.snapshot.tokenUsage.output,
							total: managed.snapshot.tokenUsage.total,
							cost: managed.snapshot.tokenUsage.cost,
							cacheRead: managed.snapshot.tokenUsage.cacheRead,
							cacheWrite: managed.snapshot.tokenUsage.cacheWrite,
							estimated: managed.snapshot.tokenUsage.estimated,
						}
					: undefined,
				liveTokenUsage: managed.snapshot.liveTokenUsage,
				startedAt: managed.startedAt.toISOString(),
				updatedAt: new Date().toISOString(),
				completedAt: managed.status === "completed" ? new Date().toISOString() : undefined,
				durationMs: managed.result?.durationMs,
			});
		} catch (err) {
			// Persistence is best-effort: the run is still healthy in memory.
			// Log so an operator debugging state-loss has a lead, but never crash
			// the workflow over a disk-full situation.
			console.warn("[workflow-manager] Persist run failed:", err);
		}
	}

	/**
	 * Pause a running workflow.
	 */
	pause(runId: string): boolean {
		const managed = this.runs.get(runId);
		if (managed?.status !== "running") return false;

		managed.controller.abort();
		managed.status = "paused";
		this.emit("paused", { runId });
		this.persistRun(managed);
		return true;
	}

	/**
	 * Resume an interrupted run: replay journaled results for the unchanged prefix
	 * and run the rest live. Returns false if there is nothing resumable.
	 */
	async resume(runId: string): Promise<boolean> {
		// Guard: refuse to resume a run that is already running, or one that was
		// intentionally aborted (pause/stop/Esc). Paused and failed runs can restart.
		const active = this.runs.get(runId);
		if (active?.status === "running") return false;
		if (active?.status === "aborted") return false;
		if (active?.settled) await active.settled;

		const persisted = this.persistence.load(runId);
		if (!persisted?.script || persisted.status === "completed" || persisted.status === "aborted") return false;
		const lease = this.persistence.acquireRunLease(runId);
		if (!lease) return false;

		const controller = new AbortController();
		const managed: ManagedRun = {
			runId,
			status: "running",
			snapshot: {
				name: persisted.workflowName,
				phases: persisted.phases ?? [],
				currentPhase: persisted.currentPhase,
				logs: persisted.logs ?? [],
				agents: (persisted.agents ?? []).map(persistedAgentToSnapshot),
				agentCount: persisted.agents?.length ?? 0,
				runningCount: 0,
				doneCount: 0,
				errorCount: 0,
				result: persisted.result,
				durationMs: persisted.durationMs,
				complete: persisted.complete,
				missing: persisted.missing,
				errors: persisted.errors,
				error: persisted.error,
				errorCode: persisted.errorCode,
				recoverable: persisted.recoverable,
				runId: persisted.runId,
			},
			controller,
			startedAt: new Date(),
			script: persisted.script,
			args: persisted.args,
			journal: persisted.journal ?? [],
			background: true,
			lease,
			limits: this.resolveLimits({
				maxAgents: persisted.maxAgents,
				concurrency: persisted.concurrency,
				agentTimeoutMs: persisted.agentTimeoutMs,
				agentRetries: persisted.agentRetries,
				tokenBudget: persisted.tokenBudget,
				maxRecoveryRounds: persisted.maxRecoveryRounds,
			}),
			recoveryOfRunId: persisted.recoveryOfRunId,
			recoveryRound: persisted.recoveryRound,
		};
		managed.snapshot = recomputeWorkflowSnapshot(managed.snapshot);
		this.runs.set(runId, managed);

		const resumeJournal = new Map((persisted.journal ?? []).map((e) => [e.index, e] as const));
		managed.snapshot.tokenUsage = persisted.tokenUsage;
		managed.snapshot.liveTokenUsage = persisted.liveTokenUsage ? normalizeTokenUsage(persisted.liveTokenUsage) : undefined;
		this.emit("resumed", { runId });
		// Run in the background; executeRun records status/errors on the managed run.
		const promise = this.executeRun(managed, persisted.script, persisted.args, {
			resumeJournal,
			maxAgents: persisted.maxAgents,
			concurrency: persisted.concurrency,
			agentTimeoutMs: persisted.agentTimeoutMs,
			agentRetries: persisted.agentRetries,
			tokenBudget: persisted.tokenBudget,
			maxRecoveryRounds: persisted.maxRecoveryRounds,
			recoveryOfRunId: persisted.recoveryOfRunId,
			recoveryRound: persisted.recoveryRound,
			initialTokenUsage: persisted.tokenUsage ? normalizeTokenUsage(persisted.tokenUsage) : undefined,
		});
		managed.settled = promise.then(() => undefined, () => undefined);
		void promise.catch(() => {});
		return true;
	}

	/**
	 * Stop a running workflow.
	 */
	stop(runId: string): boolean {
		const managed = this.runs.get(runId);
		if (!managed || (managed.status !== "running" && managed.status !== "paused")) return false;

		managed.controller.abort();
		managed.status = "aborted";
		this.emit("stopped", { runId });
		this.persistRun(managed);
		return true;
	}

	/**
	 * Get status of a specific run.
	 */
	getRun(runId: string): ManagedRun | undefined {
		return this.runs.get(runId);
	}

	/**
	 * List all runs (active + persisted).
	 */
	/**
	 * Runs for the navigator/task panel. Once bound to a session (setSessionId), only
	 * that session's runs are returned — runs from other sessions stay on disk and
	 * reappear when you switch back. Unbound (tests/legacy) returns everything.
	 */
	listRuns(): PersistedRunState[] {
		const all = this.persistence.list();
		return this.sessionId ? all.filter((r) => r.sessionId === this.sessionId) : all;
	}

	/** All persisted runs regardless of session (used by cross-session recovery). */
	listAllRuns(): PersistedRunState[] {
		return this.persistence.list();
	}

	/**
	 * Get snapshot of a run.
	 */
	getSnapshot(runId: string): WorkflowSnapshot | null {
		return this.runs.get(runId)?.snapshot ?? null;
	}

	/**
	 * Delete a persisted run.
	 */
	deleteRun(runId: string): boolean {
		const managed = this.runs.get(runId);
		if (managed) this.releaseRunLease(managed);
		this.runs.delete(runId);
		return this.persistence.delete(runId);
	}

	/**
	 * Get the persistence layer (for saving workflows).
	 */
	getPersistence(): RunPersistence {
		return this.persistence;
	}
}

function findSnapshotAgent(
	agents: WorkflowAgentSnapshot[],
	event: { stableId: string; callIndex: number; label?: string },
	runningOnly = false,
): WorkflowAgentSnapshot | undefined {
	const candidates = runningOnly ? agents.filter((agent) => agent.status === "running") : agents;
	const reversed = [...candidates].reverse();
	return (
		reversed.find((agent) => agent.stableId === event.stableId && agent.callIndex === event.callIndex) ??
		reversed.find(
			(agent) =>
				agent.callIndex === event.callIndex && (agent.stableId === undefined || agent.stableId === event.stableId),
		) ??
		reversed.find(
			(agent) =>
				agent.stableId === event.stableId && (agent.callIndex === undefined || agent.callIndex === event.callIndex),
		) ??
		reversed.find(
			(agent) =>
				agent.stableId === undefined &&
				agent.callIndex === undefined &&
				event.label !== undefined &&
				agent.label === event.label,
		)
	);
}

function nextAgentId(agents: WorkflowAgentSnapshot[]): number {
	return agents.reduce((max, agent) => Math.max(max, agent.id), 0) + 1;
}

function persistedAgentToSnapshot(agent: PersistedAgentState): WorkflowAgentSnapshot {
	return {
		id: agent.id,
		stableId: agent.stableId,
		callIndex: agent.callIndex,
		label: agent.label,
		subSkill: agent.subSkill,
		phase: agent.phase,
		prompt: agent.prompt,
		status: agent.status,
		resultPreview: agent.resultPreview ?? (agent.result === undefined ? undefined : preview(agent.result)),
		error: agent.error,
		errorCode: agent.errorCode,
		recoverable: agent.recoverable,
		history: agent.history,
		tokens: agent.tokens,
		model: agent.model,
		attempts: agent.attempts?.map((attempt) => ({
			...attempt,
			usage: attempt.usage ? { ...attempt.usage } : undefined,
		})),
	};
}

function addSnapshotUsage(
	snapshot: WorkflowSnapshot,
	usage: { input: number; output: number; cacheRead: number; cacheWrite: number; total: number; cost: number; source: string },
): void {
	const total = snapshot.tokenUsage ?? {
		input: 0,
		output: 0,
		cacheRead: 0,
		cacheWrite: 0,
		total: 0,
		cost: 0,
	};
	total.input += usage.input;
	total.output += usage.output;
	total.cacheRead = (total.cacheRead ?? 0) + usage.cacheRead;
	total.cacheWrite = (total.cacheWrite ?? 0) + usage.cacheWrite;
	total.total += usage.total;
	total.cost = (total.cost ?? 0) + usage.cost;
	if (usage.source === "estimated") total.estimated = true;
	snapshot.tokenUsage = total;
}

function normalizePositiveInteger(value: number, min: number, max: number): number {
	if (!Number.isFinite(value) || value < min) return min;
	return Math.min(max, Math.floor(value));
}

function normalizeInteger(value: number, min: number, max: number): number {
	if (!Number.isFinite(value) || value < min) return min;
	return Math.min(max, Math.floor(value));
}

function normalizeTokenUsage(value: {
	input: number;
	output: number;
	total: number;
	cost?: number;
	cacheRead?: number;
	cacheWrite?: number;
	estimated?: boolean;
}): TokenUsageTotals {
	return {
		input: value.input ?? 0,
		output: value.output ?? 0,
		cacheRead: value.cacheRead ?? 0,
		cacheWrite: value.cacheWrite ?? 0,
		total: value.total ?? 0,
		cost: value.cost ?? 0,
		estimated: value.estimated,
	};
}

function persistedLimitFields(limits: PersistedRunLimits): Pick<
	PersistedRunState,
	"maxAgents" | "concurrency" | "agentTimeoutMs" | "agentRetries" | "tokenBudget" | "maxRecoveryRounds"
> {
	return {
		maxAgents: limits.maxAgents,
		concurrency: limits.concurrency,
		agentTimeoutMs: limits.agentTimeoutMs,
		agentRetries: limits.agentRetries,
		tokenBudget: limits.tokenBudget,
		maxRecoveryRounds: limits.maxRecoveryRounds,
	};
}
