/**
 * Filesystem layout for DisCo dynamic workflow state.
 *
 * Workflow state lives under the DisCo workflow home. Project-scoped state is
 * isolated by a stable cwd-derived namespace.
 */

import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { basename, join, resolve } from "node:path";

export const WORKFLOW_HOME_RELATIVE_DIR = ".disco/workflows";
export const WORKFLOW_PROJECTS_SUBDIR = "projects";

export interface WorkflowProjectPaths {
	key: string;
	rootDir: string;
	runsDir: string;
	savedDir: string;
	settingsPath: string;
}

export function workflowHomeDir(): string {
	return join(homedir(), WORKFLOW_HOME_RELATIVE_DIR);
}

export function workflowUserSavedDir(): string {
	return join(workflowHomeDir(), "saved");
}

export function workflowProjectKey(cwd: string): string {
	const projectPath = resolve(cwd);
	const slug = sanitizePathSegment(basename(projectPath) || "project");
	const hash = createHash("sha256").update(projectPath).digest("hex").slice(0, 12);
	return `${slug}-${hash}`;
}

export function workflowProjectPaths(cwd: string): WorkflowProjectPaths {
	const key = workflowProjectKey(cwd);
	const rootDir = join(workflowHomeDir(), WORKFLOW_PROJECTS_SUBDIR, key);
	return {
		key,
		rootDir,
		runsDir: join(rootDir, "runs"),
		savedDir: join(rootDir, "saved"),
		settingsPath: join(rootDir, "settings.json"),
	};
}

function sanitizePathSegment(value: string): string {
	const sanitized = value
		.toLowerCase()
		.replace(/[^a-z0-9._-]+/g, "-")
		.replace(/^-+|-+$/g, "")
		.slice(0, 48);
	return sanitized || "project";
}
