/** Pi-owned variables that must not configure or leak through the DisCo CLI process. */
export const PI_ENVIRONMENT_KEYS = [
	"PI_CODING_AGENT",
	"PI_CODING_AGENT_DIR",
	"PI_CODING_AGENT_SESSION_DIR",
	"PI_PACKAGE_DIR",
	"PI_OFFLINE",
	"PI_SKIP_VERSION_CHECK",
	"PI_TELEMETRY",
	"PI_CACHE_RETENTION",
	"PI_SHARE_VIEWER_URL",
	"PI_HARDWARE_CURSOR",
	"PI_CLEAR_ON_SHRINK",
	"PI_DEBUG_REDRAW",
	"PI_TUI_DEBUG",
	"PI_TUI_WRITE_LOG",
	"PI_OAUTH_CALLBACK_HOST",
	"PI_EXPERIMENTAL",
	"PI_SESSION_ID",
	"PI_SESSION_FILE",
	"PI_PROVIDER",
	"PI_MODEL",
	"PI_REASONING_LEVEL",
] as const;

/**
 * Isolate the DisCo executable before importing Pi-derived dependencies.
 * This only mutates the current DisCo process; a parent shell or separate Pi
 * process keeps its original environment.
 */
export function isolateDisCoProcessFromPiEnvironment(env: NodeJS.ProcessEnv = process.env): void {
	for (const key of PI_ENVIRONMENT_KEYS) {
		delete env[key];
	}
}
