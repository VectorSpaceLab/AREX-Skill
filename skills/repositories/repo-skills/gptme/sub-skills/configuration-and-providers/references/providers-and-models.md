# Providers, models, auth, local backends, and dependencies

Use this reference to choose a gptme model/provider, place credentials safely, configure local or custom OpenAI-compatible endpoints, and decide which optional dependencies are needed. Do not make live API calls unless the user explicitly asks for connectivity or model validation.

## Provider/model syntax

The clearest model form is:

```text
<provider>/<model-name>
```

Common examples:

```sh
gptme "hello" -m openai/gpt-5
gptme "hello" -m anthropic/claude-sonnet-4-6
gptme "hello" -m openrouter/anthropic/claude-sonnet-4-6
gptme "hello" -m deepseek/deepseek-reasoner
gptme "hello" -m gemini/gemini-2.5-flash
gptme "hello" -m groq/llama-3.3-70b-versatile
gptme "hello" -m xai/grok-4
gptme "hello" -m local/llama3.2:3b
gptme "hello" -m gptme/claude-sonnet-4-6
```

Provider-only values such as `anthropic` use that provider's recommended model when a recommendation exists. Fully-qualified model IDs are easier to audit and should be preferred in persistent config.

## Built-in provider prefixes and key sources

| Provider prefix | Primary credential/config source | Notes |
| --- | --- | --- |
| `openai` | `OPENAI_API_KEY` | GPT-5-class and o-series models use the OpenAI Responses API by default. Set `GPTME_OPENAI_RESPONSES_API=0` only for direct-OpenAI debugging. |
| `anthropic` | `ANTHROPIC_API_KEY` | Native Anthropic path. `GPTME_ANTHROPIC_FAST_MODE=true` enables provider fast mode for models/accounts that support it. |
| `openrouter` | `OPENROUTER_API_KEY` or `/account setup openrouter` | One key for many providers. gptme applies privacy/routing defaults described below. |
| `requesty` | `REQUESTY_API_KEY` | OpenAI-compatible gateway using `requesty/<provider>/<model>` style IDs. |
| `gemini` | `GEMINI_API_KEY` | Routed through the OpenAI-compatible client base URL for Gemini. |
| `groq` | `GROQ_API_KEY` | Do not use `OPENAI_BASE_URL=https://api.groq.com/openai/v1`; the `groq/...` prefix handles Groq's own key. |
| `xai` | `XAI_API_KEY` | Direct xAI API. |
| `deepseek` | `DEEPSEEK_API_KEY` | Direct DeepSeek API. |
| `moonshot` | `MOONSHOT_API_KEY` | Direct Moonshot/Kimi API. |
| `azure` | `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` | Tenant/deployment-specific; no universal recommended model, so use a full deployment/model name. |
| `nvidia` | `NVIDIA_API_KEY` | OpenAI-compatible NVIDIA endpoint. |
| `local` | `OPENAI_BASE_URL` or legacy `OPENAI_API_BASE`; optional `OPENAI_API_KEY` | For Ollama, LM Studio, vLLM, llama-cpp-python, or other local OpenAI-compatible servers. The base URL only applies to `local/...`. |
| `gptme` | `gptme-auth login`, `GPTME_CLOUD_API_KEY`, or stored cloud token | Managed service/gateway provider. `GPTME_CLOUD_BASE_URL` can point to a custom service. |
| `openai-subscription` | `gptme-auth openai-subscription` | Uses local OAuth tokens for personal ChatGPT subscription development use. |
| `grok-subscription` | `gptme-auth grok-subscription` or existing grok CLI auth | Uses local OAuth tokens for SuperGrok subscription access. |
| `mock` | none | Explicit testing/provider simulation only; it is not auto-selected from credential discovery. |

Credential discovery for auto-detection first considers configured built-in API keys, then provider keys stored by `/account`, then OAuth token files, then provider plugin key variables. If more than one provider is configured and no model/default is set, the first discovered provider wins; avoid surprise by setting `[models].default` or passing `--model`.

## Credential storage and auth helpers

### `/account` inside gptme

Use `/account` when already in a gptme session:

```text
/account
/account list
/account setup
/account setup openrouter
/account setup anthropic
```

Behavior:

- `/account list` shows configured provider accounts and a masked preview only.
- `/account setup openrouter` launches OpenRouter OAuth / PKCE, stores the resulting key in the credential store, refreshes the in-memory provider when possible, and sets an `env.MODEL` default for OpenRouter's recommended model.
- `/account setup anthropic|openai|deepseek|gemini|groq|xai` prompts for the key without putting it on the command line, validates it, stores it in the credential store, and sets an `env.MODEL` default for that provider when gptme has one.
- Passing API keys as slash-command arguments is intentionally rejected.

The credential store records keys under provider names and is created/tightened to owner-only file permissions. Future agents should report only that a provider is configured, not the key value.

### `gptme-auth` CLI

Use `gptme-auth --help` for the current command surface. Common safe help-only checks:

```sh
gptme-auth --help
gptme-auth login --help
gptme-auth status --help
gptme-auth openrouter --help
gptme-auth openai-subscription --help
gptme-auth grok-subscription --help
```

Useful flows:

- `gptme-auth login` starts gptme managed-service device-flow login and stores a refreshable token.
- `gptme-auth login --no-browser` prints the URL/code instead of attempting to open a browser.
- `gptme-auth status` reports cloud login status without printing tokens.
- `gptme-auth logout` removes stored gptme managed-service credentials for the selected service URL.
- `gptme-auth openrouter` runs browser PKCE and writes `OPENROUTER_API_KEY` to local config.
- `gptme-auth openai-subscription` and `gptme-auth grok-subscription` store local OAuth tokens for subscription-backed providers.

Live auth flows open browsers, run callback/device-flow servers, or contact external services; do not run them during static diagnosis unless explicitly requested.

## OpenRouter routing and privacy

For `openrouter/...` models, gptme adds provider-routing preferences to avoid silent incompatibilities:

- Non-reasoning requests set `require_parameters = true`, so OpenRouter only routes to backends that support all request parameters such as tools or response formats.
- Non-reasoning requests default `data_collection = "deny"` to prevent provider training/data retention when possible.
- Reasoning requests do not set those defaults unless the user overrides them, because combining reasoning, `require_parameters`, and `data_collection="deny"` can eliminate all providers and cause OpenRouter 400 errors.
- Add a provider suffix to pin a backend: `openrouter/anthropic/claude-sonnet-4-6@anthropic`. gptme sets provider order and disables fallback for the pinned suffix.
- Set `OPENROUTER_DATA_COLLECTION=allow` only if the user knowingly accepts a provider requiring it.
- Set `OPENROUTER_QUANTIZATION=fp16,bf16` or similar to restrict provider precision. Valid examples include `fp16`, `bf16`, `fp8`, `int8`, `int4`, and `unknown`; unknown values produce warnings.

OpenRouter requests may also use `GPTME_MAX_TOKENS` to avoid large credit reservations. For OpenRouter and `gptme` cloud, gptme applies safer `max_tokens` defaults when none are supplied.

## Local OpenAI-compatible providers

### Ollama quick config

Ollama exposes an OpenAI-compatible server at port 11434. A safe persistent config is:

```toml
[env]
MODEL = "local/llama3.2:3b"
OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
```

Runtime commands a user may run on their own machine:

```sh
ollama pull llama3.2:3b
ollama serve
gptme "hello" -m local/llama3.2:3b
```

Checklist:

- The model tag after `local/` must match `ollama list` exactly, including the `:tag` suffix.
- `OPENAI_BASE_URL` is used only by the `local` provider. It does not redirect `openai/...`, `anthropic/...`, `groq/...`, or other built-ins.
- `OPENAI_API_KEY` is optional for many local servers; gptme uses a harmless fallback for local if no key is present.
- Small local models often fail tool protocols. For agent work, prefer at least a capable 7B+ instruction model and try `--tool-format xml` when Markdown tool calls loop.
- If local generation is slow, set `LLM_API_TIMEOUT` to a numeric number of seconds instead of assuming the provider is broken.

### Summary-model behavior with local models

For built-in providers, gptme may choose a cheaper summary model. For `local`, no separate summary model is defined; gptme uses the same default local model for summary tasks. If summary generation fails with a local setup, troubleshoot the same endpoint/model/tool-format stack instead of searching for a hidden summary-provider setting.

Static diagnosis without live calls:

1. Confirm the selected model begins with `local/`.
2. Confirm `OPENAI_BASE_URL` or `OPENAI_API_BASE` is configured and points to an OpenAI-compatible `/v1` endpoint.
3. Confirm the local model tag exists in the user's local model list if they provide it.
4. Suggest a larger model or different `--tool-format` for tool-call failures.
5. Use the bundled config validator; do not call the model unless the user requests a live smoke test.

## Named custom providers in config

For a personal/team OpenAI-compatible endpoint, add `[[providers]]` to global config or local override:

```toml
[[providers]]
name = "vllm-local"
base_url = "http://localhost:8000/v1"
api_key_env = "VLLM_LOCAL_API_KEY"
default_model = "meta-llama/Llama-3.1-8B-Instruct"
```

Then use:

```sh
gptme "hello" -m vllm-local/meta-llama/Llama-3.1-8B-Instruct
gptme "hello" -m vllm-local
```

Config fields:

| Field | Required | Notes |
| --- | --- | --- |
| `name` | yes | Provider prefix. Must be unique across configured providers and should not collide with built-in provider names unless intentionally overriding local behavior. |
| `base_url` | yes | OpenAI-compatible API base URL. Usually ends with `/v1`. |
| `api_key` | no | Direct key in config. Avoid in shared files; only consider in local overrides. |
| `api_key_env` | no | Env var holding the key. Preferred for private/team endpoints. |
| `default_model` | no | Needed when invoking the provider by bare name. |

API key resolution for a configured provider:

1. Inline `api_key` if present.
2. `api_key_env` if present.
3. `<PROVIDER_NAME>_API_KEY`, where dashes become underscores and the name is uppercased.
4. A default placeholder key for endpoints that do not require auth.

`gptme-util providers list` is safe and prints sources without raw keys. `gptme-util providers test <name>` performs a live `/models` call; only run it with user approval.

## Provider plugin packages

Use a provider plugin package when the provider is shareable and OpenAI-compatible. Two entry-point paths are supported:

- Legacy provider-only package: `gptme.providers` entry point exporting a `ProviderPlugin` instance.
- Unified plugin package: `gptme.plugins` entry point exporting a plugin object that may include a provider plus tools/hooks/commands.

Minimal provider-only shape:

```python
from gptme.llm.models import ModelMeta, ProviderPlugin

provider = ProviderPlugin(
    name="acme",
    api_key_env="ACME_API_KEY",
    base_url="https://api.acme.example/v1",
    models=[
        ModelMeta(
            provider="unknown",
            model="acme/turbo-v1",
            context=128_000,
            max_output=4096,
            supports_vision=True,
            supports_reasoning=True,
        ),
    ],
)
```

Package metadata:

```toml
[project.entry-points."gptme.providers"]
acme = "gptme_provider_acme:provider"
```

Rules:

- `ProviderPlugin.name` is the model prefix.
- `api_key_env` names the required env var.
- `base_url` must be OpenAI-compatible.
- `ModelMeta.model` should be fully qualified, such as `acme/turbo-v1`, with `provider="unknown"`.
- If a custom `init(config)` is provided, it must register an OpenAI-compatible client before returning. Otherwise gptme raises a runtime error.
- Plugin traffic routes through the OpenAI client path. Metadata flags such as `supports_streaming` are UI/capability hints; they may not change transport behavior by themselves.

Route plugin tools, hooks, commands, and packaging mechanics to the tools/extensibility sub-skill; this sub-skill owns only provider/model/auth behavior.

## Optional Python extras and system dependencies

Install only what the target workflow needs. Broad `[all]` installs increase startup, disk, and host-dependency risk.

| Extra or system dependency | Use when | Route/notes |
| --- | --- | --- |
| `server` | Running `gptme-server`, REST API, or Web UI backend. | Server security and deployment details belong to server/protocols. |
| `browser` plus Playwright browser install | Browser automation tool. | Tool/browser behavior belongs to tools/extensibility. |
| `tui` | Running `gptme-tui`. | TUI operation belongs to server/protocols. |
| `acp` | Agent Client Protocol adapter. | ACP operation belongs to server/protocols. |
| `datascience` | matplotlib/pandas/numpy workflows. | Usually tool/workflow-specific. |
| `telemetry` | OpenTelemetry instrumentation. | Treat collector/exporter endpoints as external service config. |
| `sandbox` | Wasmtime sandbox support. | Tool execution/safety behavior belongs to tools/extensibility. |
| `sounds` | Tool sound notifications. | Optional local audio dependency. |
| `dspy`, `swebench`, `eval` | Prompt optimization and large benchmark/eval workflows. | Eval execution belongs to evals/benchmarks. |
| `docs`, `pyinstaller` | Maintainer-only docs/build/release work in a gptme checkout. | Maintainer workflow belongs to repo-development. |
| `shellcheck`, `tmux`, `gh` | Helpful CLI/development integrations. | Install only if the user needs shell linting, terminal multiplexing, or GitHub CLI. |
| `lynx`, `wl-clipboard`, `pdftotext` | Optional browser/clipboard/PDF capabilities. | Document missing-package errors; do not install host packages without approval. |

When the task is maintainer-only for a gptme checkout, say so explicitly before recommending `make test`, `make lint`, `make typecheck`, docs builds, release checks, or frontend dependency installs.
