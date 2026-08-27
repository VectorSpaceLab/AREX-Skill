import {
	defaultProviderAuthContext,
	type AuthContext,
	type OAuthAuth,
	type Provider,
} from "@earendil-works/pi-ai";
import { anthropicOAuth } from "./anthropic.ts";
import { openaiCodexOAuth } from "./openai-codex.ts";
import { openRouterOAuth } from "./openrouter.ts";

const DISCO_OAUTH_BY_PROVIDER: Readonly<Record<string, OAuthAuth>> = {
	anthropic: anthropicOAuth,
	"openai-codex": openaiCodexOAuth,
	openrouter: openRouterOAuth,
};

/** Replace only the Pi flows that read a Pi-owned callback-host variable. */
export function withDiscoOAuth(provider: Provider): Provider {
	const oauth = DISCO_OAUTH_BY_PROVIDER[provider.id];
	if (!oauth) return provider;
	return { ...provider, auth: { ...provider.auth, oauth } };
}

/** Keep ambient provider credentials while making every PI_* value invisible. */
export function createDiscoProviderAuthContext(base: AuthContext = defaultProviderAuthContext()): AuthContext {
	return {
		env: (name) => (name.startsWith("PI_") ? Promise.resolve(undefined) : base.env(name)),
		fileExists: (path) => base.fileExists(path),
	};
}

export { getDiscoOAuthCallbackHost } from "./callback-host.ts";
export { anthropicOAuth, openaiCodexOAuth, openRouterOAuth };
