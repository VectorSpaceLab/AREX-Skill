# Agent Runtime Reference

Return to [`../SKILL.md`](../SKILL.md) for routing and safe-start guidance.

## JARVIS, Claw, Gateway, and Web Modes

The top-level CLI delegates agent workflows to `omicverse.jarvis.cli`:

| User command | Runtime behavior |
| --- | --- |
| `omicverse jarvis ...` | Direct JARVIS CLI. Starts a channel bot unless one-shot `-q/--question` or daemon flags are supplied. |
| `omicverse claw` | Starts gateway mode by default: adds `--gateway-daemon` and `--with-web`. |
| `omicverse claw -q ...` | One-shot code generation / natural-language response path, not gateway startup. |
| `omicverse claw --daemon` | Starts a persistent claw daemon process. |
| `omicverse claw --use-daemon -q ...` | Sends a one-shot request to a running daemon. |
| `omicverse claw --stop-daemon` | Stops the running claw daemon. |
| `omicverse gateway ...` | Gateway daemon with web UI enabled by default. |
| `omicverse web ...` | Optional OmicClaw/legacy web workspace; requires optional web package availability. |

Safe parser checks:

```bash
omicverse jarvis --help
omicverse claw --help
omicverse gateway --help
```

Service startup examples, only when explicitly requested:

```bash
omicverse claw -q "write OmicVerse QC code for an existing AnnData object" --max-functions 8 --no-reflection
omicverse claw --daemon --socket /tmp/ov-claw.sock
omicverse claw --use-daemon -q "find marker genes for leiden clusters" --socket /tmp/ov-claw.sock
omicverse gateway --web-host 127.0.0.1 --web-port 5050 --no-browser
omicverse jarvis --channel telegram --allowed-user USERNAME
```

Do not embed tokens or saved auth files into generated code, config examples, logs, or artifacts. Credentials must come from user-provided environment variables, OAuth setup, or explicit CLI flags in the user's own shell.

## JARVIS CLI Options

Core setup and runtime options:

| Option | Purpose |
| --- | --- |
| `--setup` | Run the interactive setup wizard. |
| `--setup-language en|zh` | Wizard language. |
| `--config-file PATH` | Jarvis config file path. |
| `--auth-file PATH` | Jarvis auth state file path. |
| `--channel telegram|discord|wechat|feishu|imessage|qq` | Channel backend. |
| `--model MODEL` | LLM model name. |
| `--auth-mode environment|openai_oauth|openai_codex|openai_api_key|saved_api_key|google_oauth|gemini_cli_oauth|no_auth` | Provider auth mode. |
| `--api-key KEY` | Direct LLM key; prefer environment or saved auth to avoid shell history exposure. |
| `--endpoint URL` | Custom base URL, including local Ollama/OpenAI-compatible endpoints. |
| `--max-prompts N` | Max prompts per kernel session before auto-restart; `0` disables auto-restart. |
| `--session-dir PATH` | Per-user workspaces. |
| `--verbose` | Verbose logging. |

Channel credential options:

| Channel | Options / environment |
| --- | --- |
| Telegram | `--token`, `--allowed-user`; `TELEGRAM_BOT_TOKEN`. |
| Discord | `--discord-token`; `DISCORD_BOT_TOKEN`. |
| WeChat | `--wechat-token`, `--wechat-base-url`, `--wechat-allow-from`; `WECHAT_BOT_TOKEN`. |
| Feishu | `--feishu-app-id`, `--feishu-app-secret`, `--feishu-host`, `--feishu-port`, `--feishu-path`, `--feishu-connection-mode`, `--feishu-verification-token`, `--feishu-encrypt-key`; matching `FEISHU_*` variables. |
| iMessage | `--imessage-cli-path`, `--imessage-db-path`, `--imessage-include-attachments`; platform-specific permissions may apply. |
| QQ | `--qq-app-id`, `--qq-client-secret`, `--qq-image-host`, `--qq-image-server-port`, `--qq-markdown`; matching `QQ_*` variables. |

Gateway/web options:

| Option | Purpose |
| --- | --- |
| `--with-web` | Start the OmicVerse web server in the background. |
| `--web-port PORT` | Web server port; `0` means auto-select from `5050`. |
| `--web-host HOST` | Web bind host; default is `127.0.0.1`. |
| `--no-browser` | Do not open a browser. |
| `--codex-login` | Force fresh OpenAI Codex OAuth login. |
| `--gemini-cli-login` | Force fresh Gemini CLI OAuth login. |

Claw one-shot/daemon options:

| Option | Purpose |
| --- | --- |
| `-q`, `--question WORD...` | One-shot natural-language request. |
| `--output FILE` | Write generated code to a file instead of stdout. |
| `--max-functions N` | Limit registry functions included in the prompt; default `8`. |
| `--no-reflection` | Skip review pass and return first generated code. |
| `--debug-registry` | Print matched registry entries to stderr. |
| `--daemon` | Start persistent daemon. |
| `--use-daemon` | Send one-shot request to daemon. |
| `--stop-daemon` | Stop daemon. |
| `--socket PATH` | Unix socket for daemon communication. |

## Smart Agent Public API

The public factory is `omicverse.utils.smart_agent.Agent(...)`, also exported with `OmicVerseAgent` and `list_supported_models`.

```python
from omicverse.utils.smart_agent import Agent, AgentConfig, LLMConfig, ExecutionConfig

agent = Agent(
    model="gemini-2.5-flash",
    auth_mode="environment",
    enable_reflection=True,
    use_notebook_execution=True,
    max_prompts_per_session=5,
    approval_mode="never",
    max_agent_turns=15,
)
```

Important constructor/factory parameters:

| Parameter | Default / role |
| --- | --- |
| `model` | Default constructor value; current grouped config default is `gemini-2.5-flash`. |
| `api_key` | Optional direct provider key; prefer environment/saved auth. |
| `endpoint` | Optional provider base URL. |
| `auth_mode` | `environment` by default; JARVIS also supports OAuth and saved-key modes. |
| `auth_provider`, `auth_file` | OAuth/provider-specific auth. |
| `enable_reflection`, `reflection_iterations`, `enable_result_review` | Code/result review controls; iterations are clamped to 1-3 in grouped config. |
| `use_notebook_execution`, `notebook_storage_dir`, `keep_execution_notebooks`, `notebook_timeout`, `strict_kernel_validation` | Notebook execution controls. |
| `max_prompts_per_session` | Auto-restart threshold for notebook sessions. |
| `enable_filesystem_context`, `context_storage_dir` | Filesystem context collection and storage. |
| `approval_mode` | Sandbox permission behavior; default `never`. |
| `agent_mode`, `max_agent_turns` | Agentic loop behavior. |
| `security_level` | Optional preset that builds sandbox policy. |
| `config` | Optional `AgentConfig`; takes priority over flat kwargs. |
| `reporter`, `verbose` | Event reporting and logs. |

`AgentConfig.from_flat_kwargs(...)` preserves backward compatibility while grouping settings into `llm`, `reflection`, `execution`, `context`, `harness`, and `security` blocks.

## AgentConfig Groups

| Group | Key fields |
| --- | --- |
| `LLMConfig` | `model`, `api_key`, `endpoint`, `auth_mode`, `auth_provider`, `auth_file`, `reasoning_effort`. |
| `ReflectionConfig` | `enabled`, `iterations`, `result_review`. |
| `ExecutionConfig` | `use_notebook`, `max_prompts_per_session`, `storage_dir`, `keep_notebooks`, `timeout`, `strict_kernel_validation`, `sandbox_fallback_policy`, `auto_install_packages`, `package_blocklist`, `max_execution_retries`, `validate_outputs`, `max_agent_turns`. |
| `ContextConfig` | `enabled`, `storage_dir`. |
| `HarnessConfig` | traces, artifact recording, server-tool mode, deferred tool loading, cleanup reports, context compaction, MCP registry enablement. |
| `SecurityConfig` | approval mode, dynamic import policy, introspection restrictions, or preset security level. |

Default subagent profiles are:

| Profile | Tools | Mutates AnnData |
| --- | --- | --- |
| `explore` | `inspect_data`, `run_snippet`, `search_functions`, `web_fetch`, `web_search`, `finish` | No |
| `plan` | Explore tools plus `search_skills` | No |
| `execute` | Plan tools plus `execute_code`, `web_download` | Yes |

Use `subagent_overrides` to adjust max turns, allowed tools, or temperature; invalid fields raise `ValueError`.

## Providers and Auth

Provider mapping recognizes environment variables for OpenAI, Anthropic, Google/Gemini, DeepSeek, DashScope/Qwen, Moonshot, MiniMax, Together, xAI/Grok, Qianfan, Xiaomi, Synthetic, Zhipu, Ollama, OpenAI-compatible endpoints, and local Python mode. Representative variables include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `DASHSCOPE_API_KEY`, `MOONSHOT_API_KEY`, `TOGETHER_API_KEY`, `XAI_API_KEY`, `ZAI_API_KEY`, and `ZHIPUAI_API_KEY`.

Use these patterns:

```bash
export OPENAI_API_KEY=...
omicverse jarvis --model gpt-5.1 --auth-mode environment

omicverse jarvis --model gemini-2.5-flash --auth-mode gemini_cli_oauth --gemini-cli-login

omicverse jarvis --model qwen2.5:7b --endpoint http://127.0.0.1:11434/v1 --auth-mode environment
```

For OpenAI Codex models, rerun `omicverse jarvis --setup` or use `--codex-login` when the saved token is missing account metadata or needs account switching. For Gemini CLI OAuth, use `--gemini-cli-login` to force a fresh account.

## Streaming and Sessions

`OmicVerseAgent.run(request, adata)` synchronously wraps async execution. When called inside an already-running event loop, it uses a background thread to avoid nested-loop failures. `stream_async(request, adata, ...)` yields structured streaming events such as tool calls, trace IDs, step IDs, session IDs, and categories when harness metadata is enabled.

Session guidance:

- `restart_session()` clears notebook executor state when notebook execution is enabled and is a no-op otherwise.
- `get_session_history()` returns notebook session history when enabled and an empty list otherwise.
- `max_prompts_per_session` controls automatic restart for long interactive sessions.
- Keep generated notebooks/artifacts only when the user wants traceability; otherwise use cleanup policies or temporary storage.

## Permission and Sandbox Policy

Agentic execution can read files, inspect data, run snippets, execute generated code, fetch web content, and download data depending on the selected tool profile and security policy. Before enabling high-side-effect workflows:

1. Confirm whether external network access, downloads, filesystem writes, or package installation are allowed.
2. Keep credentials in environment/config mechanisms and redact them from logs.
3. Prefer `approval_mode` and `security_level` settings that match the user's environment.
4. Disable or restrict `auto_install_packages` when package mutation is not acceptable.
5. Use explicit storage directories and cleanup expectations for notebooks and traces.
