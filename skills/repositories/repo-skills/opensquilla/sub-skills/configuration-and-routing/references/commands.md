# Command Reference: Providers, Models, Router, Search, Config

Use these commands from an environment where the `opensquilla` executable is installed. Do not rely on a source checkout.

## Safety classes

| Class | Commands | Notes |
| --- | --- | --- |
| Local, non-mutating | `providers list`, `search list`, `onboard catalog ...`, `config get`, `router calibration-show` | Safe first checks. They inspect installed catalogs or local config. |
| Mutating config | `configure provider`, `configure router`, `configure search`, `config set --config ...` | Writes a config file; restart the gateway when the CLI says restart is required. |
| Gateway-backed | `providers status`, `models list`, ordinary `search status`, ordinary `search query` | Requires a running gateway that can read the intended config and environment. |
| Live/provider-dependent | `models probe`, `providers status --probe-models`, credentialed search queries | May contact provider APIs or the network; use only with explicit user intent and valid keys. |

## Provider setup and inspection

List local provider metadata without a gateway:

```sh
opensquilla providers list
opensquilla providers list --json
opensquilla onboard catalog providers
opensquilla onboard catalog providers --json
```

Inspect runtime status through the running gateway:

```sh
opensquilla providers status
opensquilla providers status openrouter --json
opensquilla providers status --probe-models
```

Configure a provider with an environment-variable key reference:

```sh
export OPENROUTER_API_KEY="sk-..."
opensquilla configure provider \
  --provider openrouter \
  --model deepseek/deepseek-v4-flash \
  --api-key-env OPENROUTER_API_KEY
```

Common direct-provider examples:

```sh
opensquilla configure provider --provider openai --model gpt-5.4-mini --api-key-env OPENAI_API_KEY
opensquilla configure provider --provider anthropic --model claude-sonnet-4-5 --api-key-env ANTHROPIC_API_KEY
opensquilla configure provider --provider gemini --model gemini-2.5-flash --api-key-env GEMINI_API_KEY
opensquilla configure provider --provider ollama --model llama3.1
```

For a custom compatible endpoint, include the base URL and a model id:

```sh
opensquilla configure provider \
  --provider custom \
  --model vendor-model \
  --base-url https://llm.example.com/v1 \
  --api-key-env CUSTOM_LLM_API_KEY
```

`opensquilla providers configure PROVIDER ...` also exists for direct provider edits, but the higher-level `opensquilla configure provider ... --api-key-env ...` path is the safer routine recommendation because it supports secret-by-env setup and applies onboarding mutations consistently.

## Model catalog and provider probes

List available models through the running gateway:

```sh
opensquilla models list
opensquilla models list --provider openrouter --json
opensquilla models list --capability vision
```

Probe configured providers directly from config. This is live/provider-dependent and may perform a small chat probe or a model-list probe:

```sh
opensquilla models probe
opensquilla models probe --provider openai --model gpt-5.4-mini --timeout 30 --json
opensquilla models probe --config ./opensquilla.toml
```

Probe output redacts credential material. Exit code `1` means at least one probe failed; exit code `2` means invalid selection or missing configured providers.

## Router setup and inspection

Use onboarding/router catalog for available modes and provider profiles:

```sh
opensquilla onboard catalog router
opensquilla onboard catalog router --json
```

Recommended first-run router setup:

```sh
opensquilla onboard --router recommended
```

Reconfigure an existing install:

```sh
opensquilla configure router --router recommended
opensquilla configure router --router openrouter-mix
opensquilla configure router --router disabled
opensquilla configure router --router recommended --default-tier c1
```

Inspect relevant config values:

```sh
opensquilla config get squilla_router.enabled
opensquilla config get squilla_router.tier_profile
opensquilla config get squilla_router.default_tier
opensquilla config get llm.provider
opensquilla config get llm.model
```

Offline calibration commands read local router decision records and do not contact providers:

```sh
opensquilla router calibration-show
opensquilla router calibrate --dry-run
opensquilla router calibrate --json
```

Use calibration only when the user is asking about router calibration or local decision records. Do not confuse calibration with basic router enable/disable setup.

## Search setup and testing

List search provider metadata without a gateway:

```sh
opensquilla search list
opensquilla search list --json
opensquilla onboard catalog search
opensquilla onboard catalog search --json
```

Configure DuckDuckGo as the no-key path:

```sh
opensquilla configure search --search-provider duckduckgo
# equivalent search subcommand:
opensquilla search configure duckduckgo
```

Configure a keyed provider with an environment-variable key reference:

```sh
export TAVILY_API_KEY="..."
opensquilla configure search --search-provider tavily --api-key-env TAVILY_API_KEY
```

Equivalent search subcommand with advanced fields:

```sh
opensquilla search configure tavily \
  --api-key-env TAVILY_API_KEY \
  --max-results 8 \
  --fallback-policy network \
  --diagnostics
```

Inspect and test through the running gateway:

```sh
opensquilla search status
opensquilla search status tavily --json
opensquilla search query "OpenSquilla release notes"
opensquilla search query "OpenSquilla release notes" --limit 5 --json
```

Research-mode query options can run the normalized local research path:

```sh
opensquilla search query "sqlite json functions" --mode technical --max-results 8 --fetch-top-k 3 --json
opensquilla search query "browser automation release notes" --mode news --recency month --include-domain github.com
```

The built-in synthetic search benchmark is offline unless `--live` is requested, and the CLI rejects the live benchmark in favor of live gate tests:

```sh
opensquilla search benchmark --profile smoke
opensquilla search benchmark --profile smoke --json
```

## Config commands

Inspect the active public config:

```sh
opensquilla config get
opensquilla config get llm.provider
opensquilla config get search_provider
```

Persist a specific advanced setting to a chosen config file:

```sh
opensquilla config set squilla_router.confidence_threshold 0.55 --config ./opensquilla.toml
opensquilla config set search_fallback_policy '"network"' --config ./opensquilla.toml
```

Without `--config`, `config set` prints an environment export suggestion instead of editing a file. When a persisted change says restart is required, apply it with the gateway lifecycle commands in the setup-and-gateway sub-skill.

## Adjacent configuration surfaces

These commands share provider/key/base-URL patterns, but detailed image generation and memory workflows are outside this sub-skill:

```sh
opensquilla configure image-generation --image-provider tokenrhythm --primary tokenrhythm/wan2.7-image --api-key-env TOKENRHYTHM_API_KEY
opensquilla configure image-generation --no-image-enabled
opensquilla configure memory-embedding --memory-provider local
opensquilla configure memory-embedding --memory-provider openai --model text-embedding-3-small --api-key-env OPENAI_API_KEY
```
