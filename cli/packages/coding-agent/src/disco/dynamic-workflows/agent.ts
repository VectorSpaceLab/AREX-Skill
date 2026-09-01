import { execFile } from "node:child_process";
import { isAbsolute } from "node:path";
import { promisify } from "node:util";
import type { AssistantMessage, Model, TextContent } from "@earendil-works/pi-ai";
import type { Static, TSchema } from "typebox";
import { Check, Convert } from "typebox/value";
import { getAgentDir } from "../../config.ts";
import { ModelRegistry } from "../../core/model-registry.ts";
import { ModelRuntime } from "../../core/model-runtime.ts";
import {
	type CreateAgentSessionOptions,
	createAgentSession,
	createCodingTools,
	type ToolDefinition,
} from "../../core/sdk.ts";
import { SessionManager } from "../../core/session-manager.ts";
import { SettingsManager } from "../../core/settings-manager.ts";
import { DEFAULT_DISCO_AGENT_MODE, type DiscoAgentMode } from "../modes/types.ts";
import { type AgentHistoryEntry, compactAgentHistory } from "./agent-history.ts";
import { applyToolPolicy } from "./agent-registry.ts";
import { WorkflowError, WorkflowErrorCode } from "./errors.ts";
import { loadModelTierConfig, type ModelTierConfig, resolveTierModel } from "./model-tier-config.ts";
import { createStructuredOutputTool, type StructuredOutputCapture } from "./structured-output.ts";
import type { AgentUsage } from "./agent-usage.ts";

const execFileAsync = promisify(execFile);

export type { AgentUsage } from "./agent-usage.ts";

/** Extract a best-effort live usage snapshot from a session stream event. */
export function extractLiveAgentUsage(event: unknown): AgentUsage | undefined {
	if (!event || typeof event !== "object") return undefined;
	const value = event as {
		type?: string;
		message?: Partial<AssistantMessage>;
		assistantMessageEvent?: { partial?: Partial<AssistantMessage> };
	};
	const candidate =
		value.message?.role === "assistant"
			? value.message.usage
			: value.type === "message_update"
				? value.assistantMessageEvent?.partial?.usage
				: undefined;
	if (!candidate || candidate.totalTokens <= 0) return undefined;
	return {
		input: candidate.input,
		output: candidate.output,
		cacheRead: candidate.cacheRead,
		cacheWrite: candidate.cacheWrite,
		total: candidate.totalTokens,
		cost: candidate.cost.total,
	};
}

/**
 * Find a JSON object/array in free-form text: a fenced ```json block if present,
 * else the first balanced {...} or [...]. Best-effort (the schema check is the
 * real gate). Returns the raw JSON string, or undefined when none is found.
 */
function findJsonBlock(text: string): string | undefined {
	const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
	if (fence?.[1]) return fence[1].trim();
	const start = text.search(/[{[]/);
	if (start === -1) return undefined;
	const open = text[start];
	const close = open === "{" ? "}" : "]";
	let depth = 0;
	for (let i = start; i < text.length; i++) {
		if (text[i] === open) depth++;
		else if (text[i] === close && --depth === 0) return text.slice(start, i + 1);
	}
	return undefined;
}

/**
 * Last-resort structured-output recovery: extract a JSON block from prose, coerce
 * it toward the schema, and accept it only if it then validates. Never fabricates
 * — returns undefined unless the parsed value genuinely satisfies the schema.
 */
export function extractValidated<T>(text: string, schema: TSchema): T | undefined {
	const json = findJsonBlock(text);
	if (json === undefined) return undefined;
	let parsed: unknown;
	try {
		parsed = JSON.parse(json);
	} catch {
		return undefined;
	}
	try {
		const converted = Convert(schema, parsed);
		if (Check(schema, converted)) return converted as T;
	} catch {
		// typebox can throw on exotic schemas; treat as no match.
	}
	return undefined;
}

/** Minimal session surface resolveStructuredOutput needs (real session or a test double). */
export interface StructuredSession {
	prompt(text: string): Promise<void>;
	setActiveToolsByName?(names: string[]): void;
	messages: unknown[];
}

/**
 * Resolve a schema agent's result. If the tool was called, return the captured
 * value. Otherwise re-prompt up to maxSchemaRetries (tools restricted to
 * structured_output), then try strict schema-validated prose extraction, else
 * throw SCHEMA_NONCOMPLIANCE (non-recoverable — surfaced, never a silent null).
 * Module-level with an injected `lastText` so it is unit-testable.
 */
export async function resolveStructuredOutput<T>(
	session: StructuredSession,
	capture: StructuredOutputCapture<T>,
	schema: TSchema,
	options: { maxSchemaRetries?: number; signal?: AbortSignal; label?: string },
	lastText: (messages: unknown[]) => string,
): Promise<T> {
	if (capture.called) return capture.value as T;

	const maxRetries = Math.max(0, options.maxSchemaRetries ?? 2);
	// Restrict to the schema tool so the only useful next action is calling it
	// (takes effect on the next prompt turn). Best-effort.
	try {
		session.setActiveToolsByName?.(["structured_output"]);
	} catch {
		// ignore — the re-prompt alone still drives most models to comply
	}
	for (let attempt = 0; attempt < maxRetries && !capture.called; attempt++) {
		if (options.signal?.aborted) throw new Error("Subagent was aborted");
		await session.prompt(
			"You did not call the structured_output tool. Call structured_output now as your only action, with the required fields filled in. Do not write a prose answer.",
		);
	}
	if (capture.called) return capture.value as T;

	const extracted = extractValidated<T>(lastText(session.messages), schema);
	if (extracted !== undefined) {
		console.warn(
			"[workflow] structured_output recovered from prose extraction (the model never called the tool); prefer a tool-reliable model",
		);
		return extracted;
	}

	throw new WorkflowError(
		"Subagent did not produce valid structured_output after repair attempts",
		WorkflowErrorCode.SCHEMA_NONCOMPLIANCE,
		{ recoverable: false, agentLabel: options.label },
	);
}

/**
 * Resolve which concrete model spec a subagent should use. Precedence, most
 * specific first:
 *   1. options.model — an explicit per-agent model (also carries agentType /
 *      phase model, which the workflow layer folds into options.model).
 *   2. options.tier  — resolved via the model-tiers config, falling back to the
 *      session's main model when the tier has no configured entry.
 *   3. DEFAULT TIER — when neither is set but the user has a model-tiers config,
 *      untagged agents default to the "medium" tier so a configured tier set
 *      actually affects the whole workflow (not just agents the script tagged).
 *      Fresh-install medium == the session model, so this is a no-op until the
 *      user customizes tiers via /workflows-models.
 * Returns undefined when nothing applies, so the session default is used.
 *
 * `loadConfig` is injectable for testing; it defaults to reading from disk.
 */
export function resolveAgentModelSpec(
	options: { model?: string; tier?: string },
	mainModel: string | undefined,
	loadConfig: () => ModelTierConfig | null = loadModelTierConfig,
): string | undefined {
	if (options.model) return options.model;
	const config = loadConfig();
	if (options.tier) {
		return (config ? resolveTierModel(options.tier, config) : undefined) ?? mainModel;
	}
	// Untagged agent: default to the configured medium tier when one exists.
	if (config) {
		const medium = resolveTierModel("medium", config);
		if (medium) return medium;
	}
	return undefined;
}

export interface WorkflowAgentOptions {
	cwd?: string;
	/** Extra tools available to the subagent in addition to the structured output tool. */
	tools?: ToolDefinition[];
	/** Override non-isolation-sensitive createAgentSession options such as model and auth runtime. */
	session?: Partial<CreateAgentSessionOptions>;
	/** Extra system guidance prepended to every subagent task. */
	instructions?: string;
	/** Current session model registry. Falls back to a lazily created runtime when omitted. */
	modelRegistry?: ModelRegistry;
	/**
	 * The session's main model (`provider/modelId`). Used as a fallback when
	 * resolving opts.tier and no model-tiers.json config exists. Without this,
	 * a workflow using `{ tier: "small" }` would log a warning and fall through
	 * to the session default when no config is saved yet.
	 */
	mainModel?: string;
	/** Parent mode inherited by every in-memory subagent session. */
	discoMode?: DiscoAgentMode;
}

/**
 * List the user's currently available models (those with auth configured) as
 * `provider/modelId` specs. Used to tell the workflow author which models it may
 * route agents to. Best-effort: returns [] if the registry can't be built.
 */
export function listAvailableModelSpecs(registry?: ModelRegistry): string[] {
	try {
		return registry?.getAvailable().map((m: Model<any>) => `${m.provider}/${m.id}`) ?? [];
	} catch {
		return [];
	}
}

export interface AgentEnvironmentSpec {
	/** The prepared environment's executable, e.g. a venv's `python` binary. */
	executable: string;
	/** Arguments that select the executable/runtime before the inspection command. */
	args?: string[];
	/** Directory in which the assertion should run. Defaults to the agent cwd. */
	cwd?: string;
	/** Package/module whose installed version must be checked. */
	package?: string;
	/** Exact expected package version. */
	version?: string;
	/** Explicit version/inspection argv. Defaults to Python package metadata inspection. */
	versionArgs?: string[];
}

/** Known prepare-env report fields accepted only as a migration safety net. */
export interface LegacyAgentEnvironmentSpec {
	pythonExecutable?: string;
	expectedDistribution?: string;
	expectedVersion?: string;
	assertBeforeStartup?: boolean;
}

/** Untrusted environment input received from a workflow script. */
export type AgentEnvironmentInput = Partial<AgentEnvironmentSpec> & LegacyAgentEnvironmentSpec;

export interface NormalizedAgentEnvironment {
	environment: AgentEnvironmentSpec;
	warnings: string[];
}

const ENVIRONMENT_SHAPE = "{ executable, cwd?, package?, version?, args?, versionArgs? }";
const LEGACY_ENVIRONMENT_FIELDS = [
	["pythonExecutable", "executable"],
	["expectedDistribution", "package"],
	["expectedVersion", "version"],
] as const;

function environmentContractError(message: string): never {
	throw new WorkflowError(message, WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED, { recoverable: false });
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

function optionalString(source: Record<string, unknown>, key: keyof AgentEnvironmentSpec): string | undefined {
	const value = source[key];
	if (value === undefined) return undefined;
	if (typeof value !== "string" || !value.trim()) {
		environmentContractError(
			`Subagent environment contract error: environment.${key} must be a non-empty string. Use ${ENVIRONMENT_SHAPE}.`,
		);
	}
	return value;
}

function optionalStringArray(source: Record<string, unknown>, key: "args" | "versionArgs"): string[] | undefined {
	const value = source[key];
	if (value === undefined) return undefined;
	if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string")) {
		environmentContractError(
			`Subagent environment contract error: environment.${key} must be an array of strings. Use ${ENVIRONMENT_SHAPE}.`,
		);
	}
	return [...value] as string[];
}

/**
 * Convert only the prepare-repo-skill-env report fields observed in the Creator
 * trajectory. Unknown guesses and ambient executable fallbacks are deliberately
 * unsupported.
 */
export function normalizeAgentEnvironment(input: unknown): NormalizedAgentEnvironment {
	if (!isRecord(input)) {
		environmentContractError(
			`Subagent environment contract error: expected an object shaped as ${ENVIRONMENT_SHAPE}.`,
		);
	}

	const source: Record<string, unknown> = { ...input };
	const legacyMappings: string[] = [];
	for (const [legacyKey, canonicalKey] of LEGACY_ENVIRONMENT_FIELDS) {
		const legacyValue = source[legacyKey];
		if (legacyValue === undefined) continue;
		legacyMappings.push(`${legacyKey} -> ${canonicalKey}`);
		const canonicalValue = source[canonicalKey];
		if (canonicalValue !== undefined && canonicalValue !== legacyValue) {
			environmentContractError(
				`Subagent environment contract conflict: canonical \`${canonicalKey}\` and legacy \`${legacyKey}\` disagree. Use only canonical fields ${ENVIRONMENT_SHAPE}.`,
			);
		}
		if (canonicalValue === undefined) source[canonicalKey] = legacyValue;
	}

	if (Object.prototype.hasOwnProperty.call(source, "assertBeforeStartup")) {
		legacyMappings.push("assertBeforeStartup (ignored; assertion is always required)");
	}

	const executable = optionalString(source, "executable");
	if (!executable) {
		environmentContractError(
			`Subagent environment contract error: Missing environment.executable for subagent startup. The prepare-env report maps pythonExecutable -> executable, expectedDistribution -> package, and expectedVersion -> version. Use ${ENVIRONMENT_SHAPE}; ambient Python fallback is disabled.`,
		);
	}
	if (!isAbsolute(executable)) {
		environmentContractError(
			`Subagent environment contract error: environment.executable must be an absolute path; ambient PATH lookup is disabled. Use ${ENVIRONMENT_SHAPE}.`,
		);
	}

	const environment: AgentEnvironmentSpec = { executable };
	const args = optionalStringArray(source, "args");
	const cwd = optionalString(source, "cwd");
	const packageName = optionalString(source, "package");
	const version = optionalString(source, "version");
	const versionArgs = optionalStringArray(source, "versionArgs");
	if (args) environment.args = args;
	if (cwd) environment.cwd = cwd;
	if (packageName) environment.package = packageName;
	if (version) environment.version = version;
	if (versionArgs) environment.versionArgs = versionArgs;

	return {
		environment,
		warnings:
			legacyMappings.length > 0
				? [
						`Prepared environment used legacy prepared-environment fields (${legacyMappings.join(", ")}). Use environment: ${ENVIRONMENT_SHAPE}.`,
				  ]
				: [],
	};
}

function redactEnvironmentPaths(message: string, environment: AgentEnvironmentSpec, defaultCwd: string): string {
	let redacted = message;
	for (const path of [environment.executable, environment.cwd, defaultCwd]) {
		if (path && path.length > 1) {
			redacted = redacted.split(path).join(path === environment.executable ? "<prepared executable>" : "<prepared cwd>");
		}
	}
	return redacted;
}

/**
 * Assert the structured environment handoff before a subagent session starts.
 * This intentionally runs without a shell so a missing entry cannot silently
 * fall back to ambient Python or another ambient executable.
 */
export async function assertAgentEnvironment(
	input: AgentEnvironmentInput,
	defaultCwd = process.cwd(),
	options: { onWarning?: (message: string) => void } = {},
): Promise<{ output: string; version?: string }> {
	const normalized = normalizeAgentEnvironment(input);
	const environment = normalized.environment;
	for (const warning of normalized.warnings) {
		if (options.onWarning) options.onWarning(warning);
		else console.warn(`[workflow] ${warning}`);
	}

	const args = [...(environment.args ?? [])];
	const inspectArgs =
		environment.versionArgs ??
		(environment.package
			? [
					"-c",
					`import importlib.metadata as _m; print(_m.version(${JSON.stringify(environment.package)}))`,
			  ]
			: ["--version"]);

	try {
		const result = await execFileAsync(environment.executable, [...args, ...inspectArgs], {
			cwd: environment.cwd ?? defaultCwd,
			timeout: 15_000,
			maxBuffer: 64 * 1024,
		});
		const output = `${result.stdout ?? ""}\n${result.stderr ?? ""}`.trim();
		const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
		const detectedVersion = environment.package || environment.versionArgs || environment.version ? lines.at(-1) : undefined;
		if (environment.version && detectedVersion !== environment.version) {
			throw new Error(
				`expected ${environment.package ?? "runtime"} version ${environment.version}, got ${detectedVersion ?? "no version output"}`,
			);
		}
		return { output, version: detectedVersion };
	} catch (error) {
		const message = redactEnvironmentPaths(error instanceof Error ? error.message : String(error), environment, defaultCwd);
		throw new WorkflowError(
			`Subagent environment assertion failed while executing the prepared environment: ${message}`,
			WorkflowErrorCode.ENVIRONMENT_ASSERTION_FAILED,
			{ recoverable: false, details: error },
		);
	}
}

export interface AgentRunOptions<TSchemaDef extends TSchema | undefined = undefined> {
	label?: string;
	schema?: TSchemaDef;
	tools?: ToolDefinition[];
	instructions?: string;
	signal?: AbortSignal;
	/**
	 * Called once with this subagent's real usage, read from the session right
	 * before disposal. Fires on both the success and error paths so partial
	 * usage is never lost. `total === 0` means the provider reported no usage.
	 */
	onUsage?: (usage: AgentUsage) => void;
	/** Called with a best-effort live usage snapshot while the session streams. */
	onLiveUsage?: (usage: AgentUsage) => void;
	/**
	 * Model spec for this subagent: either `provider/modelId` (unambiguous) or a
	 * bare `modelId`. When it can't be resolved, the session default is used and
	 * a warning is logged. When omitted, the session default applies.
	 */
	model?: string;
	/**
	 * Model tier name (e.g. "small", "medium", "big"). When set (and no explicit
	 * `model` is given), the model is resolved from the user's model-tiers.json
	 * config before `run()` starts, falling back to the session's main model when
	 * the tier has no configured entry. An explicit `model` always takes priority,
	 * so workflow scripts can use `{ tier: "small" }` for coarse routing without
	 * caring which concrete model backs that tier.
	 */
	tier?: string;
	/** Called with the resolved model id once known (for display/telemetry). */
	onModelResolved?: (modelId: string) => void;
	/** Called when `model`/`tier`/phase resolved to a spec that wasn't found (fell back to session default). */
	onModelFallback?: (requestedSpec: string) => void;
	/** Called with a compact snapshot of this subagent's message/tool history. */
	onHistory?: (history: AgentHistoryEntry[]) => void;
	/**
	 * DisCo create-skill progress/file-ownership hint. When set, append a
	 * Creator-only sub-skill file contract after the task prompt so a drafting
	 * agent writes files directly instead of handing file bodies back to the
	 * parent workflow.
	 */
	subSkill?: string;
	/** Run this agent in a different working directory (e.g. an isolated worktree). */
	cwd?: string;
	/**
	 * Restrict the subagent's coding tools to these names (an agentType
	 * definition's `tools` allowlist). Undefined = all coding tools. The
	 * structured_output tool is always added after this filter, so a schema
	 * still works under a restrictive allowlist.
	 */
	toolNames?: string[];
	/** Remove these coding-tool names after the allowlist (an agentType `disallowedTools` denylist). */
	disallowedToolNames?: string[];
	/** Prepared environment assertion; failure is a hard subagent failure. */
	environment?: AgentEnvironmentInput;
	/**
	 * With `schema`: how many extra repair turns to allow if the model finishes
	 * without calling structured_output. Each retry re-prompts (tools restricted to
	 * structured_output) before falling back to strict prose extraction. Default 2.
	 */
	maxSchemaRetries?: number;
}

export type AgentRunResult<TSchemaDef extends TSchema | undefined> = TSchemaDef extends TSchema
	? Static<TSchemaDef>
	: string;

export class WorkflowAgent {
	private readonly cwd: string;
	private readonly baseTools: ToolDefinition[];
	private readonly sessionOptions: Partial<CreateAgentSessionOptions>;
	private readonly instructions?: string;
	private readonly mainModel?: string;
	private readonly discoMode: DiscoAgentMode;
	/** Lazily built once; shares the SDK's agentDir/auth so resolved models are authed. */
	private registry?: ModelRegistry;
	private registryPromise?: Promise<ModelRegistry>;

	constructor(options: WorkflowAgentOptions = {}) {
		this.cwd = options.cwd ?? process.cwd();
		this.baseTools = options.tools ?? createCodingTools(this.cwd);
		this.sessionOptions = options.session ?? {};
		this.instructions = options.instructions;
		this.mainModel = options.mainModel;
		this.discoMode = options.discoMode ?? DEFAULT_DISCO_AGENT_MODE;
		this.registry = options.modelRegistry;
	}

	private async getRegistry(): Promise<ModelRegistry> {
		if (this.registry) return this.registry;
		this.registryPromise ??= ModelRuntime.create({ allowModelNetwork: false }).then(
			(runtime) => new ModelRegistry(runtime),
		);
		this.registry = await this.registryPromise;
		return this.registry;
	}

	/**
	 * Resolve a model spec to a Model. Accepts `provider/modelId` (unambiguous)
	 * or a bare `modelId` (prefers auth-configured models, then any known model).
	 * Returns undefined when nothing matches.
	 */
	private async resolveModel(spec: string): Promise<Model<any> | undefined> {
		const registry = await this.getRegistry();
		const slash = spec.indexOf("/");
		if (slash > 0) {
			return registry.find(spec.slice(0, slash), spec.slice(slash + 1));
		}
		return (
			registry.getAvailable().find((m: Model<any>) => m.id === spec) ??
			registry.getAll().find((m: Model<any>) => m.id === spec)
		);
	}

	async run<TSchemaDef extends TSchema | undefined = undefined>(
		prompt: string,
		options: AgentRunOptions<TSchemaDef> = {},
	): Promise<AgentRunResult<TSchemaDef>> {
		const capture: StructuredOutputCapture<any> = { called: false, value: undefined };
		// Per-call cwd (e.g. a worktree) needs coding tools bound to that directory,
		// since tools capture their cwd at construction and can't be relocated.
		const runCwd = options.cwd ?? this.cwd;
		const baseTools = runCwd === this.cwd ? this.baseTools : createCodingTools(runCwd);
		// Apply the agentType tool policy BEFORE adding structured_output, so a
		// restrictive allowlist never strips the schema tool.
		const customTools: ToolDefinition[] = applyToolPolicy(
			[...baseTools, ...(options.tools ?? [])],
			options.toolNames,
			options.disallowedToolNames,
		);

		if (options.schema) {
			customTools.push(createStructuredOutputTool({ schema: options.schema, capture }) as unknown as ToolDefinition);
		}

		// Resolve the model spec (explicit model > tier > session default). This
		// composes with phase-based routing in workflow.ts, which only supplies
		// options.model when a phase pattern matches — so an explicit model wins.
		const modelSpec = resolveAgentModelSpec(options, this.mainModel);
		if (options.environment) await assertAgentEnvironment(options.environment, runCwd);

		// Resolve a requested model spec to a Model object. A given-but-unresolved
		// spec falls back to the session default (with a warning) rather than failing.
		let resolvedModel: Model<any> | undefined;
		if (modelSpec) {
			resolvedModel = await this.resolveModel(modelSpec);
			if (resolvedModel) {
				options.onModelResolved?.(`${resolvedModel.provider}/${resolvedModel.id}`);
			} else {
				console.warn(`[workflow] model "${modelSpec}" not found; using session default`);
				options.onModelFallback?.(modelSpec);
			}
		}

		const agentDir = getAgentDir();
		const safeSessionOptions = { ...this.sessionOptions };
		delete safeSessionOptions.discoMode;
		delete safeSessionOptions.resourceLoader;
		delete safeSessionOptions.sessionManager;
		const { session } = await createAgentSession({
			...safeSessionOptions,
			cwd: runCwd,
			agentDir,
			discoMode: this.discoMode,
			sessionManager: SessionManager.inMemory(runCwd, { discoMode: this.discoMode }),
			// Use real SettingsManager to inherit user's default provider/model settings.
			// SettingsManager.inMemory() doesn't load ~/.disco/agent/settings.json, so subagents
			// would fall back to the first available model (e.g. openai-codex) which may
			// not have valid auth, causing silent empty responses.
			settingsManager: safeSessionOptions.settingsManager ?? SettingsManager.create(runCwd, agentDir),
			customTools,
			// Per-call model wins over any sessionOptions.model.
			...(resolvedModel ? { model: resolvedModel } : {}),
		});

		let removeAbortListener: (() => void) | undefined;
		let removeHistoryListener: (() => void) | undefined;
		let abortPromise: Promise<void> | undefined;
		const abortSession = (): Promise<void> => {
			abortPromise ??= Promise.resolve(session.abort()).catch(() => {});
			return abortPromise;
		};
		let lastHistoryEmit = 0;
		const emitHistory = () => options.onHistory?.(compactAgentHistory(session.messages));
		const maybeEmitHistory = () => {
			if (!options.onHistory) return;
			const now = Date.now();
			if (now - lastHistoryEmit < 250) return;
			lastHistoryEmit = now;
			emitHistory();
		};
		try {
			if (options.signal?.aborted) throw new Error("Subagent was aborted");
			if (options.signal) {
				const onAbort = () => void abortSession();
				options.signal.addEventListener("abort", onAbort, { once: true });
				removeAbortListener = () => options.signal?.removeEventListener("abort", onAbort);
			}
			if (options.onHistory || options.onLiveUsage) {
				removeHistoryListener = session.subscribe((event) => {
					if (options.onLiveUsage) {
						const liveUsage = extractLiveAgentUsage(event);
						if (liveUsage) options.onLiveUsage(liveUsage);
					}
					maybeEmitHistory();
				});
			}

			await session.prompt(this.buildPrompt(prompt, options as AgentRunOptions<any>, Boolean(options.schema)));
			if (options.signal?.aborted) throw new Error("Subagent was aborted");

			if (options.schema) {
				return (await resolveStructuredOutput(session, capture, options.schema, options, (m) =>
					this.lastAssistantText(m),
				)) as AgentRunResult<TSchemaDef>;
			}

			const text = this.lastAssistantText(session.messages);
			if (!text.trim()) {
				throw new WorkflowError("Subagent produced no assistant output", WorkflowErrorCode.AGENT_EMPTY_OUTPUT, {
					recoverable: true,
					agentLabel: options.label,
				});
			}
			return text as AgentRunResult<TSchemaDef>;
		} finally {
			if (options.signal?.aborted) await abortSession();
			removeAbortListener?.();
			removeHistoryListener?.();
			try {
				emitHistory();
			} catch {
				// History is diagnostic only; never let it mask the real result/error.
			}
			// Read real usage before disposing — dispose tears down the session state.
			if (options.onUsage) {
				try {
					const { tokens, cost } = session.getSessionStats();
					options.onUsage({
						input: tokens.input,
						output: tokens.output,
						cacheRead: tokens.cacheRead,
						cacheWrite: tokens.cacheWrite,
						total: tokens.total,
						cost,
					});
				} catch {
					// Usage is best-effort; never let stats failure mask the real result/error.
				}
			}
			session.dispose();
		}
	}

	private buildPrompt(prompt: string, options: AgentRunOptions<any>, structured: boolean): string {
		const parts = [
			this.instructions,
			options.instructions,
			options.label ? `Task label: ${options.label}` : undefined,
			prompt,
			this.discoMode === "creator" && options.subSkill
				? this.buildSubSkillFileContract(options.subSkill)
				: undefined,
		].filter(Boolean);

		if (structured) {
			parts.push(
				[
					"Final output contract:",
					"- Your final action MUST be a structured_output tool call.",
					"- The structured_output arguments are the return value of this subagent.",
					"- Do not emit a prose final answer instead of structured_output.",
					"- If you need to inspect files or run commands first, do so, then call structured_output exactly once.",
					"- If the task asks you to create or revise files, write those files with the available file tools before structured_output. The structured_output result should summarize file paths and evidence, not contain drafts for a parent agent to write later.",
				].join("\n"),
			);
		}

		return parts.join("\n\n");
	}

	private buildSubSkillFileContract(subSkill: string): string {
		return [
			"DisCo sub-skill file contract:",
			`- Assigned sub-skill: ${subSkill}.`,
			"- If this task asks you to draft or revise the generated sub-skill, write the runtime files directly in the planned output subtree before returning.",
			"- Use the available read, edit, write, and bash tools as needed to create `SKILL.md`, bundled `references/`, and bundled `scripts/`.",
			"- If this task contributes to repo-skill verification planning, propose one or two difficult synthetic usability cases for this sub-skill that go beyond the original repo tests/examples.",
			"- Keep review/test artifacts out of the runtime skill tree. Concrete cases belong under the artifact root's `test-cases/`; reports, review notes, and evals belong under `reports/`.",
			"- Do not return full Markdown or script bodies for the parent/main agent to write later, even if earlier task text requested JSON or prose drafts.",
			"- Your final response or structured_output should be a concise handoff: files created or updated, evidence consulted, checks performed, proposed hard cases, known gaps, and review questions.",
		].join("\n");
	}

	private lastAssistantText(messages: unknown[]): string {
		for (let i = messages.length - 1; i >= 0; i--) {
			const message = messages[i] as Partial<AssistantMessage> | undefined;
			if (message?.role !== "assistant" || !Array.isArray(message.content)) continue;
			const text = message.content
				.filter((part): part is TextContent => part.type === "text")
				.map((part) => part.text)
				.join("");
			if (text.trim()) return text;
		}
		return "";
	}
}
