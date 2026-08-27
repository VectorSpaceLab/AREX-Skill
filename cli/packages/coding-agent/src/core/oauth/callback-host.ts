const DEFAULT_OAUTH_CALLBACK_HOST = "127.0.0.1";

/** Resolve DisCo's loopback OAuth listener without consulting Pi-owned state. */
export function getDiscoOAuthCallbackHost(env: NodeJS.ProcessEnv = process.env): string {
	return env.DISCO_OAUTH_CALLBACK_HOST?.trim() || DEFAULT_OAUTH_CALLBACK_HOST;
}
