/**
 * Usage records shared by the subagent runner, workflow runtime, and persisted
 * run state.  `total` is the provider's reported total when `source` is
 * terminal; estimated records are deliberately marked so they cannot be
 * mistaken for provider accounting.
 */

export type UsageSource = "terminal" | "live" | "estimated";

export interface AgentUsage {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	total: number;
	cost: number;
}

export interface AgentUsageRecord extends AgentUsage {
	source: UsageSource;
	/** The logical attempt number within one agent call. */
	attempt?: number;
}

export interface TokenUsageTotals extends AgentUsage {
	/** True when at least one included amount came from a fallback estimate. */
	estimated?: boolean;
}

export function emptyTokenUsage(): TokenUsageTotals {
	return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0, cost: 0 };
}

export function cloneTokenUsage(usage: TokenUsageTotals): TokenUsageTotals {
	return { ...usage };
}

export function addAgentUsage(target: TokenUsageTotals, usage: AgentUsage): void {
	target.input += usage.input;
	target.output += usage.output;
	target.cacheRead += usage.cacheRead;
	target.cacheWrite += usage.cacheWrite;
	target.total += usage.total;
	target.cost += usage.cost;
}

export function hasReportedUsage(usage: AgentUsage | undefined): usage is AgentUsage {
	return Boolean(usage && Number.isFinite(usage.total) && usage.total > 0);
}
