# Config Precedence and Value Sources

Use this reference when a provider, model, router, search, image-generation, or memory-embedding value appears to come from the wrong place.

## Config file selection

OpenSquilla reads configuration in this order:

1. `OPENSQUILLA_GATEWAY_CONFIG_PATH`
2. `./opensquilla.toml`
3. `~/.opensquilla/config.toml`
4. built-in defaults

Use `--config ./opensquilla.toml` when the user wants project-local inspection or edits:

```sh
opensquilla config get --config ./opensquilla.toml
opensquilla configure provider --provider openrouter --model deepseek/deepseek-v4-flash --api-key-env OPENROUTER_API_KEY --config ./opensquilla.toml
```

Routine edits should go through `opensquilla configure ...`. Use raw TOML or `config set --config` for advanced fields only.

## Provider identity and endpoint precedence

For the active `[llm]` provider, `llm.base_url` resolves as:

1. Explicit config: a TOML value, Web UI advanced value, or `config set` value.
2. `OPENSQUILLA_LLM_BASE_URL` when TOML did not set `llm.base_url`; it is treated as an explicit settings-layer value.
3. Provider-derived environment variables such as `OPENAI_BASE_URL`, `OPENROUTER_BASE_URL`, or `<PROVIDER>_BASE_URL`, when the config never chose an endpoint or still holds the provider default.
4. The provider registry default base URL.

API keys use the same explicit-config-first posture:

1. `api_key` stored in config, if present. Avoid this for normal use because it stores a secret.
2. The configured `api_key_env` environment variable, if present and visible to the gateway process.
3. The provider registry environment key, such as `OPENAI_API_KEY` or `OPENROUTER_API_KEY`, when endpoint identity allows that key to be reused safely.
4. Keyless behavior for providers that do not require a key.

For non-primary deployments such as router tiers or ensemble members, resolution is stricter: explicit member overrides win, then matching provider profiles in `[llm_profiles.<provider>]`, then profile env or credential pools, then the registry env key. A registry key is not reused across a foreign custom endpoint merely because the provider id matches; an endpoint override that changes origin needs its own explicit member/profile credential.

## Provider profile example for cross-provider tiers

```toml
[llm]
provider = "openrouter"
model = "deepseek/deepseek-v4-pro"
api_key_env = "OPENROUTER_API_KEY"

[llm_profiles.openai]
api_key_env = "OPENAI_API_KEY"
base_url = "https://api.openai.com/v1"

[squilla_router]
enabled = true
cross_provider_tiers = true
```

Only use cross-provider tiers when the user intentionally wants router tiers to execute on providers other than the primary provider. Otherwise leave `cross_provider_tiers = false`.

## Router config fields

Routine modes:

```sh
opensquilla configure router --router recommended
opensquilla configure router --router openrouter-mix
opensquilla configure router --router disabled
```

Key public fields:

```sh
opensquilla config get squilla_router.enabled
opensquilla config get squilla_router.tier_profile
opensquilla config get squilla_router.default_tier
opensquilla config get squilla_router.tiers
opensquilla config get squilla_router.cross_provider_tiers
opensquilla config get squilla_router.tier_provider_mismatch
```

Router tier profiles are presets unless the operator owns a custom tier table. If a provider switch unexpectedly changes tiers, check `squilla_router.preset_binding`, `squilla_router.tier_profile`, and whether custom tiers were authored.

## Model context and pricing sources

Context-window resolution uses these layers, first match wins:

1. Per-model override: `[models.<provider_id>."<model_id>"] context_window = ...`.
2. Global override: `llm.context_window_tokens` when positive.
3. Model catalog: live/provider catalog data, vendored catalog data, and packaged corrections.
4. Default: conservative local-runtime default for local providers, otherwise a cloud default.

Pricing and cost estimates similarly prefer user overrides before catalog/static/default prices. Quote model ids that contain dots or slashes in TOML:

```toml
[models.openrouter."z-ai/glm-5.2"]
context_window = 200000
input_cost_per_mtok = 0.5
output_cost_per_mtok = 2.0
cache_read_cost_per_mtok = 0.05
cache_write_cost_per_mtok = 0.6
```

After raw config edits, restart or reload the gateway as appropriate and re-check with `config get`, `providers status`, or `models list`.

## Search provider and key precedence

Search settings are top-level config fields:

```toml
search_provider = "duckduckgo"
search_max_results = 10
search_fallback_policy = "off"
search_diagnostics = false
```

For search credentials, OpenSquilla resolves:

1. `search_api_key`, but avoid storing raw secrets in config.
2. `search_api_key_env`, if it names an environment variable visible to the gateway process.
3. The provider's default env key, such as `BOCHA_SEARCH_API_KEY`, `BRAVE_SEARCH_API_KEY`, `IQS_SEARCH_API_KEY`, `TAVILY_API_KEY`, or `EXA_API_KEY`.
4. No key. DuckDuckGo remains the no-key web-search path.

`search_provider` identifies the provider tied to `search_api_key` and `search_api_key_env`. It is not a hard promise that every automatic search will use only that provider: automatic search can rank available providers by mode, recency, and capabilities, and can use DuckDuckGo as the no-key path.

## Image-generation and memory-embedding boundaries

Image-generation config is separate from the router's `image_model` tier. The router image tier chooses a vision-capable model for image inputs; `[image_generation]` config controls the `image_generate` tool that creates new images.

Memory-embedding config controls memory retrieval embeddings, not chat/session memory commands. The memory-embedding catalog includes `auto`, `local`, `openai`, `openai-compatible`, `ollama`, and `none`; use the cli-and-automation sub-skill for memory operations such as indexing, search, repair, or flush.
