/**
 * Configuration constants for DisCo dynamic workflows.
 */

/** Maximum number of agents allowed per workflow run. */
export const MAX_AGENTS_PER_RUN = 1000;

/** Default timeout for a single agent in milliseconds. null means no hard timeout. */
export const DEFAULT_AGENT_TIMEOUT_MS = null;

/** Maximum concurrent agents (matches Claude Code limit). */
export const MAX_CONCURRENCY = 16;

/** Maximum automatic retry attempts after a recoverable agent failure. */
export const MAX_AGENT_RETRIES = 3;

/** Default token budget if none specified. */
export const DEFAULT_TOKEN_BUDGET = null;

/** User-level saved workflows directory. */
export const USER_WORKFLOW_SAVED_DIR = "~/.disco/workflows/saved";

/** User-level model tiers config file, relative to the home directory. */
export const MODEL_TIERS_FILE = ".disco/workflows/model-tiers.json";

/** User-level workflow extension settings file, relative to the home directory. */
export const WORKFLOW_SETTINGS_FILE = ".disco/workflows/settings.json";

/**
 * Named workflow subagent definitions directory. Resolved both project-relative
 * (cwd/.disco/agents) and home-relative (~/.disco/agents); project entries win on name
 * collision. Each `*.md` file is an agent definition (frontmatter + body prompt).
 */
export const AGENTS_DIR = ".disco/agents";
