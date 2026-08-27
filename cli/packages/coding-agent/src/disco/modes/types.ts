export type DiscoAgentMode = "creator" | "researcher";

export const DEFAULT_DISCO_AGENT_MODE: DiscoAgentMode = "researcher";

export interface DiscoAgentModeResolution {
	mode: DiscoAgentMode;
	invalidValue?: unknown;
}

export interface DiscoAgentModeCommand {
	mode: DiscoAgentMode;
	hasArguments: boolean;
}

export function isDiscoAgentMode(value: unknown): value is DiscoAgentMode {
	return value === "creator" || value === "researcher";
}

export function resolveDiscoAgentMode(value: unknown): DiscoAgentModeResolution {
	if (value === undefined) {
		return { mode: DEFAULT_DISCO_AGENT_MODE };
	}
	if (isDiscoAgentMode(value)) {
		return { mode: value };
	}
	return { mode: DEFAULT_DISCO_AGENT_MODE, invalidValue: value };
}

export function formatDiscoAgentMode(mode: DiscoAgentMode): string {
	return mode === "creator" ? "Creator" : "Researcher";
}

export function parseDiscoAgentModeCommand(value: string): DiscoAgentModeCommand | undefined {
	const match = /^\/(creator|researcher)(?:\s+([\s\S]+))?$/.exec(value);
	if (!match || !isDiscoAgentMode(match[1])) {
		return undefined;
	}
	return { mode: match[1], hasArguments: match[2] !== undefined };
}
