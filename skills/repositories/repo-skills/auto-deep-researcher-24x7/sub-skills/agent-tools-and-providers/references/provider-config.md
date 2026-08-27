# Provider configuration reference

This reference is a self-contained description of the dispatcher configuration
and its observable provider behavior. Use environment-variable *names* in
configuration; keep key and bearer-token values outside files and prompts.

## `AgentDispatcher` constructor

The public constructor is:

```python
AgentDispatcher(
    model="claude-sonnet-4-6",
    provider="anthropic",
    max_steps=3,
    base_url=None,
    api_key=None,
    api_key_env="",
    auth_token=None,
    auth_token_env="",
)
```

Stored fields are `model`, normalized `provider`, `max_steps`, `base_url`,
`api_key`, `auth_token`, and `provider_label`. The dispatcher starts with an
empty `_leader_history`. `max_steps` is retained as dispatcher configuration;
the worker tool-loop ceiling is the worker-specific `max_turns` table below,
while the number of worker dispatches per research cycle belongs to the loop
configuration.

Provider validation occurs after domestic preset expansion. An unknown value
raises:

```text
ValueError: Unknown provider '<value>'. Supported: ('anthropic', 'openai', 'claude_cli', 'codex_cli') or a domestic preset (...)
```

The exact supported provider values are `anthropic`, `openai`, `claude_cli`,
and `codex_cli`.

## Domestic OpenAI-compatible presets

A preset is a label over the existing OpenAI SDK path. It does not add a new
SDK or change the model string.

| `provider` label | OpenAI-compatible `base_url` | default `api_key_env` |
|---|---|---|
| `deepseek` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |
| `dashscope` / `qwen` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` |
| `moonshot` / `kimi` | `https://api.moonshot.cn/v1` | `MOONSHOT_API_KEY` |
| `zhipu` / `glm` | `https://open.bigmodel.cn/api/paas/v4` | `ZHIPUAI_API_KEY` |

For a preset, `provider_label` keeps the original label for diagnostics,
`provider` becomes `openai`, and `model` is passed through verbatim. The
transformation is equivalent to:

```text
base_url = stripped explicit base_url, otherwise preset base_url
api_key_env = stripped explicit api_key_env, otherwise preset key env
provider = "openai"
```

Thus an explicit proxy or self-hosted URL and custom key environment name win
over preset defaults. The `auth_token` and `auth_token_env` fields are not
filled by a preset.

## Secret precedence and endpoint behavior

For SDK providers, direct constructor values win over environment lookup:

1. A non-empty `api_key` is stored as supplied.
2. Otherwise, a non-empty `api_key_env` is stripped and read from that named
   environment variable.
3. If no name is supplied, no key is inserted into SDK constructor kwargs;
   the official client may use its own conventional environment lookup (for
   example, `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`).

`auth_token` follows the same direct-value-then-`auth_token_env` precedence.
Only the Anthropic-compatible client receives `auth_token`; the OpenAI client
receives `api_key` and `base_url`, not `auth_token`. An unset variable resolves
to `None`, and absent values are omitted from the client constructor kwargs.
Never print resolved values.

`base_url` is stripped; an empty string becomes `None`. For `anthropic`, it is
passed to `anthropic.Anthropic` when present. For `openai` and domestic presets,
it is passed to `openai.OpenAI` when present. `api_key_env` and
`auth_token_env` are configuration-time names, not SDK parameters.

The research loop forwards `model`, `provider`, `max_steps_per_cycle` as
`max_steps`, `base_url`, `api_key_env`, and `auth_token_env`. A loop config
therefore normally supplies secret names rather than secret values.

## Model mapping

`MODEL_MAP` contains these cross-provider aliases:

| input model | mapped model |
|---|---|
| `claude-sonnet-4-6` | `codex-5.3` |
| `claude-opus-4-6` | `gpt-5.4` |
| `codex-5.3` | `claude-sonnet-4-6` |
| `gpt-5.4` | `claude-opus-4-6` |

The mapping is applied only inside `_call_openai` when `self.provider !=
"openai"` (for example, an Anthropic provider falling back to OpenAI). A
normal `openai` provider and all domestic presets preserve the supplied model
ID, so vendor IDs such as `qwen-plus` and `deepseek-reasoner` are not rewritten.
The Anthropic API receives the supplied model directly. CLI providers use the
CLI's configured model and do not use this table.

## Provider call paths

- **`anthropic`** calls `anthropic.Anthropic(...).messages.create` with the
  model, `max_tokens=4096`, a cache-enabled text system block, and role/content
  messages. If the `anthropic` package is absent, it logs a warning and falls
  back to `_call_openai`.
- **`openai`** calls `openai.OpenAI(...).chat.completions.create` with the
  model, `max_tokens=4096`, a system message, and role/content messages. If the
  package is absent, it logs a warning and returns the mock JSON response
  `{"action": "wait", "reason": "LLM not available"}`.
- **`claude_cli`** serializes system and chat history into section-marked text,
  sends it to `claude -p --output-format text --tools ""` over stdin, and
  therefore disables built-in CLI tools. Missing CLI, timeout, and nonzero
  exit return a wait JSON response and log the failure.
- **`codex_cli`** invokes `codex exec --skip-git-repo-check -o <temporary output>
  <prompt>` and returns only the output-file message when available. Missing
  CLI, timeout, or nonzero exit return a wait JSON response. Codex's internal
  tools cannot be disabled, so a worker may act outside the registry.

CLI providers use subscription login state rather than `api_key_env`; do not
assume SDK endpoint overrides affect them. A CLI timeout is 600 seconds.

## Leader and worker dispatch

`dispatch_leader(task: str, context: dict) -> dict` loads the leader prompt,
uses prior leader messages from the current cycle, appends a formatted user
message, calls the provider, stores the assistant response, and parses the
first JSON object. If JSON parsing fails, text containing `wait` or `no
experiment` becomes `{"action": "wait", "reason": ...}`; other text becomes
an experiment for the code agent. Call `reset_leader_history()` between
cycles.

`dispatch_worker(agent_type: str, task: str, tool_registry) -> dict` validates
`agent_type` before touching the registry and rejects `None` with a clear
`TypeError`. It creates a fresh conversation, appends the tool schemas, and
runs a bounded text-protocol loop. `max_turns` is 12 for `idea`, 40 for `code`,
and 30 for `writing`. The loop ends on a response with no parsed calls or
returns the last response after the ceiling, logging a warning if calls remain.

If `provider == "codex_cli"` and the selected worker has tools, a warning says
that Codex may bypass `ToolRegistry` and the PID/log result cannot be
recovered. Prefer `claude_cli`, `anthropic`, or `openai` for workers.
