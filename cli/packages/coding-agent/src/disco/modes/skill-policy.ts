import type { DiscoAgentMode } from "./types.ts";

export type DiscoSkillRole = "meta" | "operating" | "shared";

export interface DiscoSkillRoleResolution {
	role?: DiscoSkillRole;
	invalidValue?: unknown;
}

function hasOwnKey(value: object, key: PropertyKey): boolean {
	return Object.hasOwn(value, key);
}

export function resolveDiscoSkillRole(frontmatter: Record<string, unknown>): DiscoSkillRoleResolution {
	const metadata = frontmatter.metadata;
	if (typeof metadata !== "object" || metadata === null || Array.isArray(metadata)) {
		return { role: "operating" };
	}

	if (!hasOwnKey(metadata, "disco-role")) {
		return { role: "operating" };
	}

	const value = (metadata as Record<string, unknown>)["disco-role"];
	if (value === "meta" || value === "operating" || value === "shared") {
		return { role: value };
	}
	return { invalidValue: value };
}

export function isSkillEligibleForDiscoMode(role: DiscoSkillRole, mode: DiscoAgentMode): boolean {
	if (role === "shared") return true;
	return mode === "creator" ? role === "meta" : role === "operating";
}
