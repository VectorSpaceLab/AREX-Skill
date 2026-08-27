# Configuration files and precedence

This reference is for configuring an installed gptme runtime or reviewing a user's configuration safely. It is self-contained; do not rely on the original repository checkout being present.

## Config locations and purpose

| Layer | Typical file | Purpose | Secret-safety notes |
| --- | --- | --- | --- |
| Global user config | `~/.config/gptme/config.toml` | User identity, prompt defaults, global env fallbacks, default model preferences, custom provider definitions, MCP/plugin/hook configuration pointers, and user-level settings. | Keep committable preferences here; do not put provider keys here if the file is synced. |
| Global local override | `~/.config/gptme/config.local.toml` | Machine-local override merged into the global config. | Preferred config file for API keys and local-only MCP/provider secrets. |
| Project config | `gptme.toml` in the workspace root | Project prompt/context, project env fallbacks, local settings, agent metadata, and project-specific custom provider/MCP/plugin references. | Treat as project-owned and potentially committed; review before use in untrusted workspaces. |
| Project local override | `gptme.local.toml` next to `gptme.toml` | Machine-local project override. | Put project-specific secrets here and gitignore it. |
| Chat config | `config.toml` inside a chat log directory | Per-conversation model, tools, tool format, workspace, agent, sampling, streaming, and chat env/MCP settings. | This is conversation state; when resuming, saved values can override new defaults. |
| Credential store | `credentials.toml` under gptme's config directory | Provider API keys stored by `/account setup`. | Created/tightened to owner-only permissions; future agents must list providers only, not values. |

A target user may set a non-default config directory through normal platform/XDG configuration. Avoid hard-coding user-specific absolute paths in generated instructions; ask for or infer the actual target path when inspecting a user's machine.

## Global config shape

Typical global config sections:

```toml
[user]
name = "User"
about = "I am a curious human programmer."
response_preference = "Basic concepts don't need to be explained."
# avatar = "~/Pictures/avatar.jpg"

[prompt]
files = ["~/notes/llm-tips.md"]
# [prompt.project]
# myproject = "Project-specific context injected by git-root name."

[settings]
gear = 2

[env]
# Prefer [models].default for the permanent chat model.
# MODEL = "anthropic/claude-sonnet-4-6"
# TOOL_FORMAT = "markdown"
# TOOL_ALLOWLIST = "save,append,patch,ipython,shell,browser"

[models]
default = "anthropic/claude-sonnet-4-6"
favorites = ["anthropic/claude-sonnet-4-6", "openai/gpt-4o"]
```

Important details:

- `[user]` is the current identity section. Older `[prompt].about_user` and `[prompt].response_preference` are still accepted as fallbacks when the matching `[user]` values are absent.
- `[prompt].files` are always-included context files. Relative paths resolve from the config directory for global config.
- `[settings].gear` sets the default autonomy preset for new conversations; project settings can override it.
- `[models].default` is the recommended permanent default chat model. It is a formal alternative to `MODEL` and wins over `MODEL` during model selection.
- `[models].favorites` only curates picker/UI favorites; it does not select the active model.
- Unknown global top-level keys are stripped by recent gptme versions to avoid repeated warnings. Preserve known sections when cleaning contaminated configs.

## `config.local.toml` merge behavior

`config.local.toml` is loaded from the same directory as `config.toml` and merged into the main global config.

Merge rules:

- Dictionary sections merge recursively.
- Scalar values in the local file override the main file.
- `[[mcp.servers]]` entries merge by `name`; local entries can add secrets to a server declared in the main file.
- `[[providers]]` entries merge by `name`; local entries can add an `api_key` or override a base URL/default model without appending duplicate provider rows.

Safe local override example:

```toml
[env]
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

[[providers]]
name = "ollama"
base_url = "http://127.0.0.1:11434/v1"
default_model = "llama3.2:3b"
```

Prefer `config.local.toml` over the main file for secrets. If the main config contains keys ending in `_API_KEY`, warn and suggest moving them to a local override or the credential store.

## Project config shape

A workspace `gptme.toml` can provide project context and project-local env fallbacks:

```toml
[prompt]
files = ["README.md", "Makefile"]
exclude = ["*.lock"]
system = "short"       # accepted values: "full" or "short"
prompt = "This project builds a terminal coding agent."
# base_prompt = "Override the base assistant identity for this project."
# context_cmd = "scripts/context.sh"

[env]
MODEL = "openrouter/qwen/qwen3-max"

[settings]
gear = 1

[agent]
name = "ProjectBot"
avatar = "assets/avatar.png"

[subagent]
max_concurrent = 4
```

Project config supports additional sections such as `rag`, `context`, `architect`, `plugins`, `hooks`, and `mcp`. This sub-skill only covers their configuration-file placement. Route plugin/tool/hook/MCP behavior and implementation details to the tools/extensibility sub-skill.

Security notes for project config:

- `context_cmd` and shell hook commands are executed with shell interpretation from the workspace. Review them before running gptme in untrusted repositories.
- Put project-specific secrets in `gptme.local.toml`, not `gptme.toml`.
- `prompt.system` only accepts `full` or `short`; typos are rejected.

## Chat config shape

A chat log directory stores a `config.toml` with a `[chat]` table plus optional `env` and `mcp` tables:

```toml
[chat]
model = "anthropic/claude-sonnet-4-6"
tools = ["save", "patch", "shell"]
tool_format = "markdown"
stream = true
interactive = true
workspace = "~/work/project"
# max_tokens = 4096
# temperature = 0.0
# top_p = 0.1

[env]
# Chat-local env fallback, loaded below shell env and above project/user config.
```

When resuming a conversation, the saved chat model persists unless the user supplies a new `--model`/`-m`. New CLI conversations default to the current workspace; server-created conversations may explicitly use a workspace under the log directory.

## Effective environment lookup

gptme's config object resolves env-backed values with this order:

1. `GPTME_<KEY>` in the process environment.
2. `<KEY>` in the process environment.
3. `[env]` from chat config.
4. `[env]` from project config.
5. `[env]` from global user config after local merge.
6. Caller-provided default.

Examples:

- `Config.get_env("MODEL")` checks `GPTME_MODEL`, then `MODEL`, then chat/project/global `[env].MODEL`.
- `Config.get_env("OPENAI_API_KEY")` checks `GPTME_OPENAI_API_KEY`, then `OPENAI_API_KEY`, then config `[env].OPENAI_API_KEY`.
- `get_env_required("OPENAI_API_KEY")` raises if neither env nor config provides a value.

Do not print env values for keys containing `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, or `AUTH`.

## Model selection priority

For the primary chat model, gptme resolves in this priority order:

1. `--model` / `-m` CLI flag or API request model.
2. Per-chat model saved by `/model` or the chat `config.toml`.
3. `[models].default` in the global config after local merge.
4. `MODEL` from env/config through the env lookup rules above.
5. Auto-detection from configured provider credentials.
6. Interactive first-run setup, when allowed.

Consequences:

- If `[models].default` and `MODEL` both exist and differ, `[models].default` wins. Keep the conflict visible so the user does not edit the wrong setting.
- Project `[env].MODEL` can be useful for a workspace, but global `[models].default` still has priority over `MODEL` in normal initialization.
- A provider-only value such as `anthropic` can resolve to that provider's recommended model; a fully-qualified value such as `anthropic/claude-sonnet-4-6` is clearer and safer.
- Provider aliases and model aliases may be used for metadata lookup, but the requested model name is generally sent as requested.

Use the bundled [model-selection explainer](../scripts/explain_model_selection.py) to make the priority chain explicit without making model calls.

## Static config review workflow

1. Identify which files are in scope: global `config.toml`, local override, project `gptme.toml`, project local override, chat config, and credential store.
2. Parse each TOML file. Duplicate keys or invalid syntax are hard blockers; TOML does not allow the same key twice in a table.
3. Merge local overrides into the matching main config before reasoning about effective values.
4. Compute the model-selection chain and call out conflicts, especially `[models].default` versus `MODEL`.
5. Confirm provider prefix and API-key source for the selected model. Report only source names and whether a value is present, never raw secrets.
6. For `local/...`, confirm `OPENAI_BASE_URL` or legacy `OPENAI_API_BASE` is configured.
7. For custom `[[providers]]`, confirm unique names, HTTP(S) base URLs, API-key source, and a `default_model` if the user wants to invoke the provider by bare name.
8. Use [scripts/validate_gptme_config.py](../scripts/validate_gptme_config.py) for deterministic checks before advising live auth, browser OAuth, provider connectivity tests, or model calls.
