# Package Architecture

## Purpose

Use this reference when a task needs the package/source map, public object relationships, or a quick way to choose the right sub-skill. It is distilled from the `gptme` source tree, package metadata, docs, and installed-package inspection.

## Top-level package map

| Area | Main modules | What it owns | Route |
| --- | --- | --- | --- |
| CLI and chat loop | `gptme.cli`, `gptme.chat`, `gptme.commands`, `gptme.logmanager`, `gptme.message`, `gptme.codeblock`, `gptme.prompt_queue`, `gptme.profiles`, `gptme.agent` | Terminal prompts, conversations, slash commands, logs, queued prompts, persistent agent workspaces. | `cli-and-conversations` |
| Config and providers | `gptme.config`, `gptme.credentials`, `gptme.llm`, `gptme.oauth`, `gptme.model_attestation` | Global/project/chat config, API keys, provider selection, model metadata, OAuth/device auth, model trace/attestation. | `configuration-and-providers` |
| Tools and extensions | `gptme.tools`, `gptme.hooks`, `gptme.plugins`, `gptme.mcp`, `gptme.lessons` | Tool specs/execution, PTC formats, browser/computer/shell/file tools, custom tools, plugins, hooks, MCP, lessons and skills. | `tools-and-extensibility` |
| Server and interfaces | `gptme.server`, `gptme.tui`, `gptme.acp`, `packages/gptme-acp`, `webui` | REST/SSE server, bundled Web UI, API client, auth/CORS, TUI, ACP stdio agent, frontend data-flow. | `server-webui-and-protocols` |
| Evals | `gptme.eval` | Eval suites, result files, leaderboard/trends, pass-rate gates, SWE-bench/T-bench integrations. | `evals-and-benchmarks` |
| Maintainer surfaces | `tests`, `Makefile`, `.github`, `scripts`, `webui`, docs | Focused tests, lint/typecheck/docs, release packaging, Web UI development, CI policy. | `repo-development` |

## Verified public signatures

Installed-package inspection verified these representative signatures:

```text
gptme.chat.chat(prompt_msgs, initial_msgs, logdir, workspace, model, stream=True, no_confirm=False, interactive=True, show_hidden=False, tool_allowlist=None, tool_format=None, output_schema=None, output_format='text') -> None

gptme.chat.step(log, stream, tool_format='markdown', workspace=None, model=None, output_schema=None, on_token=None, on_thinking=None, logdir=None) -> Generator[Message, None, None]

Message(role, content, timestamp=<factory>, files=<factory>, file_hashes=<factory>, call_id=None, pinned=False, hide=False, quiet=False, ephemeral_ttl=None, metadata=None)

LogManager(log=None, logdir=None, branch=None, lock=True, view=None)

Config(user=<factory>, project=None, chat=None)
ChatConfig(name=None, model=None, tools=None, tool_format=None, gear=None, stream=True, interactive=True, no_confirm=None, workspace=<factory>, agent=None, system_prompt=None, env=<factory>, mcp=None)

ToolSpec(name, desc, instructions='', instructions_format=None, examples='', functions=None, init=None, execute=None, block_types=None, available=True, available_hint=None, parameters=None, load_priority=0, disabled_by_default=False, is_mcp=False, hints=None, hooks=None, commands=None)
Parameter(name, type, description=None, enum=None, required=False)
init_tools(allowlist=None) -> list[ToolSpec]
get_available_tools(include_mcp=True) -> list[ToolSpec]

create_app(cors_origin=None, host='127.0.0.1', webui_dir=None, default_profile=None, allowed_hosts=None) -> Flask
GptmeApiClient(base_url='http://localhost:5000', auth_token=None)
GptmeAgent() -> None
create_workspace_from_template(path, agent_name, template_repo='https://github.com/gptme/gptme-agent-template', template_branch='master', fork_command=None, project_config=None, timeout=300) -> Path
resolve_eval_names(eval_names) -> list[EvalSpec]
run_evals(evals, model_configs, timeout, parallel, use_docker=False, include_user_context=False, adversarial=False, no_lessons=False) -> dict[ModelConfig, list[EvalResult]]
```

Treat these as stable enough for guidance at the captured commit, but re-run the root environment checker after a refresh or package upgrade.

## Important object relationships

- A **conversation** is persisted through `LogManager` as message history plus chat config; `gptme` CLI commands such as resume, fork, list, search, and stats operate on these logs.
- `Message` is the common unit across CLI, tools, server events, ACP conversion, and Web UI rendering. Metadata consistency matters for server/Web UI tasks.
- The chat loop calls one or more `step()` passes. A step generates an assistant response, parses tool uses, executes tools, and appends system/tool-result messages.
- `ToolSpec` is the extension contract for built-in tools and custom tool modules. Tools may own commands and hooks, not only executable blocks.
- `Config` combines user, project, and chat config. Model selection and tool configuration are resolved from CLI flags, chat config, config files, and environment.
- `create_app()` registers the Flask server/Web UI/API surface. Server sessions wrap `LogManager` and stream events over SSE for the Web UI.
- ACP adapts between ACP protocol content and `gptme` messages, then delegates turns to the normal chat infrastructure.
- Evals run normal gptme conversations inside controlled execution environments, then summarize `EvalResult` records into CSV/leaderboard/trend outputs.

## Routing by natural task

- "Run gptme with these prompts/files/tools", "resume a chat", "inspect a conversation log", "use gptme-agent" → `cli-and-conversations`.
- "Set default model", "configure OpenRouter/Ollama", "where do API keys go", "write a provider plugin" → `configuration-and-providers`.
- "Add a custom tool", "debug browser/MCP/plugin/hook/lesson", "choose skill vs plugin" → `tools-and-extensibility`.
- "Start the server", "host the Web UI", "call the API", "ACP from editor", "TUI", "CORS/auth/token" → `server-webui-and-protocols`.
- "Run evals", "summarize benchmark CSVs", "SWE-bench/T-bench", "leaderboard" → `evals-and-benchmarks`.
- "Modify the gptme repo", "which tests", "release/package/webui build", "PR policy" → `repo-development`.

## Refresh triggers

Run `refresh-repo-skill` if any of these change in a target checkout:

- `pyproject.toml` entry points or extras;
- major docs for CLI/config/tools/server/evals;
- server API route structure or Web UI data-flow contract;
- tool/plugin/hook/lesson APIs;
- eval result schemas or suite selection;
- maintainer policy in `AGENTS.md`, `Makefile`, or Web UI agent guidance.
