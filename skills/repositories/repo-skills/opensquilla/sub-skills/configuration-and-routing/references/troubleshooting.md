# Troubleshooting Configuration and Routing

Start with non-mutating checks and keep local/gateway/live boundaries clear.

## Fast triage checklist

```sh
opensquilla config get llm.provider
opensquilla config get llm.model
opensquilla config get llm.base_url
opensquilla config get squilla_router.enabled
opensquilla config get search_provider
opensquilla providers list --json
opensquilla search list --json
```

If the issue depends on a running gateway or live provider, continue with:

```sh
opensquilla providers status
opensquilla providers status --probe-models
opensquilla models list --json
opensquilla search status
opensquilla doctor
```

If these cannot connect to the gateway, route gateway startup/readiness to setup-and-gateway before debugging provider logic.

## Config precedence confusion

Symptoms:

- The active provider/model/base URL is not the TOML value the user expected.
- An environment variable appears ignored.
- `configure ...` wrote one file, but the gateway reads another.

Checks:

```sh
opensquilla config get
opensquilla config get llm.provider
opensquilla config get llm.base_url
opensquilla config get search_provider
```

Fix pattern:

1. Confirm which config file is being read: explicit `--config`, `OPENSQUILLA_GATEWAY_CONFIG_PATH`, `./opensquilla.toml`, or the user config.
2. For base URLs, remember that explicit config beats `OPENSQUILLA_LLM_BASE_URL`, provider-specific base-URL env vars, and provider defaults.
3. For keys, prefer `api_key_env` and confirm that the variable is visible to the gateway process, not just the shell that edited the config.
4. Restart the gateway after persisted config changes when the CLI says restart is required.

## Missing provider API key

Symptoms:

- `providers status` shows configured but not buildable.
- `models probe` returns `auth_invalid` or `No API key available`.
- Live calls fail with 401/403 or a provider-auth failure kind.

Checks:

```sh
opensquilla config get llm.api_key_env
opensquilla providers status openai --json
opensquilla models probe --provider openai --json
```

Fix pattern:

```sh
export OPENAI_API_KEY="sk-..."
opensquilla configure provider --provider openai --model gpt-5.4-mini --api-key-env OPENAI_API_KEY
opensquilla gateway restart
```

Do not paste raw API keys into examples or issue reports. If a raw key was stored in TOML, replace it with `api_key_env` and rotate the leaked credential when appropriate.

## Missing or wrong provider base URL

Symptoms:

- Provider marked unbuildable with a `missing_base_url`-style reason.
- Custom/OpenAI-compatible endpoint receives requests on the wrong path.
- A key that works on the official endpoint fails after changing `base_url`.

Checks:

```sh
opensquilla providers list --json
opensquilla config get llm.base_url
opensquilla providers status --json
```

Fix pattern:

- For providers with no registry default, set `--base-url` explicitly.
- Do not point coding-plan or protocol-specific providers at regular chat endpoints.
- A credential bound to one official endpoint is not automatically safe for a foreign custom endpoint. Provide a matching member/profile credential for the custom origin.

## Runtime-supported versus verified provider confusion

Symptoms:

- A provider appears in `providers list`, but behaves differently from onboarding-verified providers.
- The user assumes every catalog entry has full live coverage.

Checks:

```sh
opensquilla providers list --json
opensquilla onboard catalog providers --json
```

Interpretation:

- `runtimeSupported` means the installed package has a runtime adapter path.
- `verification` distinguishes stronger verified coverage from experimental/external coverage.
- `requiresApiKey` and `requiresBaseUrl` explain why configuration may be incomplete even when the provider id is known.

For experimental/custom providers, run deliberate live probes with user approval and keep failures scoped to that provider rather than generalizing to all routing.

## Router disabled fallback or direct-mode expectation

Symptoms:

- User expected one exact model, but a different tier/model was selected.
- Router metadata is absent or says routing was not applied.
- Provider/model evaluation is noisy because the router is enabled.

Checks:

```sh
opensquilla config get squilla_router.enabled
opensquilla config get squilla_router.tier_profile
opensquilla config get squilla_router.tiers
opensquilla diagnostics on
```

Fix pattern:

```sh
opensquilla configure router --router disabled
opensquilla configure provider --provider openai --model gpt-5.4-mini --api-key-env OPENAI_API_KEY
opensquilla gateway restart
```

Use direct/disabled mode for exact-model work, benchmarks, provider debugging, and billing audits. Use `recommended` for ordinary personal-agent usage.

## Router optional dependency or runtime fallback

Symptoms:

- Router initialization warnings mention V4 bundle, LightGBM, ONNX Runtime, or degraded/default-tier behavior.
- Router enabled but every turn appears to fall back to the default tier.

Checks:

```sh
opensquilla config get squilla_router.strategy
opensquilla config get squilla_router.require_router_runtime
opensquilla providers status
opensquilla doctor
```

Fix pattern:

- If the user only needs the agent running, disable routing and use direct mode.
- If they need router behavior, use a recommended install with the router dependencies present.
- macOS source/terminal installs can need `libomp` for LightGBM; Windows installs can need the Visual C++ Redistributable for ONNX Runtime. Route installation remediation to setup-and-gateway.

## Cross-provider router mismatch

Symptoms:

- A tier names `openai`, but execution stays on the active `openrouter` provider.
- Metadata includes a tier/provider mismatch or cross-provider route block.

Checks:

```sh
opensquilla config get squilla_router.cross_provider_tiers
opensquilla config get squilla_router.tier_provider_mismatch
opensquilla config get llm_profiles
```

Fix pattern:

- Leave `cross_provider_tiers = false` for ordinary setups.
- Enable it only when each routed provider has safe credentials through `[llm_profiles.<provider>]` or provider env keys.
- Use `tier_provider_mismatch = "veto"` only for operators who prefer rebinding to an active-provider tier over route-and-flag behavior.

## Search provider missing key or no-key fallback

Symptoms:

- `search status` reports missing key.
- `search query` works with DuckDuckGo but not with a keyed provider.
- Automatic search does not use the configured keyed provider.

Checks:

```sh
opensquilla search list --json
opensquilla config get search_provider
opensquilla config get search_api_key_env
opensquilla search status --json
opensquilla search query "test query" --provider duckduckgo --json
```

Fix pattern:

```sh
export TAVILY_API_KEY="..."
opensquilla configure search --search-provider tavily --api-key-env TAVILY_API_KEY
opensquilla gateway restart
opensquilla search status tavily --json
```

Remember that DuckDuckGo is the no-key path. `search_provider` anchors configured credentials; automatic search can still use a better-ranked available provider or DuckDuckGo fallback depending on mode, recency, capabilities, missing-key handling, and fallback policy.

## Search network or proxy issue

Symptoms:

- Key is configured, but queries time out or return network/rate-limit failures.
- CLI prints proxy-related warnings.
- `search status` shows network blocked.

Checks:

```sh
opensquilla search status --json
opensquilla search query "OpenSquilla release notes" --json
opensquilla doctor
```

Fix pattern:

- Set an explicit search proxy with `opensquilla search configure ... --proxy ...` when only search needs it.
- Use `--use-env-proxy` only when the gateway environment should honor `HTTP_PROXY` / `HTTPS_PROXY` for search calls.
- If the CLI warns that proxy env vars are ignored, use the documented trust-env setting for the process that should honor them.
- Keep fallback policy bounded: `network` permits at most one additional compatible provider after transient failure.

## Image-generation and memory-embedding boundary mistakes

Symptoms:

- User expects router `image_model` to create images.
- User expects memory-embedding setup to run memory indexing/search commands.

Clarification:

- Router `image_model` selects a vision-capable route for image inputs. Image creation uses `[image_generation]` and the `image_generate` tool.
- `configure memory-embedding` chooses embedding deployment (`auto`, `local`, `openai`, `openai-compatible`, `ollama`, or `none`). Memory operations such as `memory index`, `memory search`, and `memory flush-session` belong to cli-and-automation.
