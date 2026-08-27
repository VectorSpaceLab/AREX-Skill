# Config, CLI, Components, and Prompters

## CLI dispatcher behavior

LazyLLM exposes the console script `lazyllm = lazyllm.cli.main:main`. The dispatcher selects command handlers by the first argument and forwards the remaining arguments.

Recognized command families:

| Command | Use |
| --- | --- |
| `lazyllm install <extra...>` | Install optional extras or explicit packages into the active environment. |
| `lazyllm deploy modelname` | Deploy a model through LazyLLM serving abstractions. Route details to model-deployment. |
| `lazyllm deploy mcp_server <command> [args ...] [options]` | MCP server deployment wrapper. Route details to agents-tools. |
| `lazyllm run graph.json` | Run a graph JSON workflow. |
| `lazyllm run chatbot` / `lazyllm run rag` | Built-in app demos; usually require model/provider/RAG dependencies. |
| `lazyllm skills init/list/info/delete/add/import/install` | Manage LazyLLM skills directories. `skills list` is a safe smoke command. |
| `lazyllm review ...` | PR review workflow; can be side-effecting. Route to writer-review. |
| `lazyllm review-local ...` | Local repository review workflow; still may inspect git state and produce files. |

The dispatcher does not provide a conventional successful `--help`; unknown commands and bare help-style invocations print usage and exit with error.

## Optional dependency strategy

Use the root [installation reference](../../../references/installation-and-extras.md) for the full matrix. Core runtime should install only what it needs:

- Base install for config, CLI routing, common helpers, prompts, and flow primitives.
- `rag` when importing `lazyllm.tools.rag`, `Document`, or BM25.
- `agent-advanced` for MCP-specific work.
- `standard` or `full` only when broad demos/backends are explicitly selected.

## Config behavior

LazyLLM tests verify that `lazyllm.config`:

- reads environment-backed values, including `LAZYLLM_GPU_TYPE` and `LAZYLLM_DISPLAY`,
- supports `refresh()` to reload config implementation state,
- supports `config.add(key, type, default, env=None, options=[...], alias={...}, post_action=...)`,
- resolves aliases case-insensitively,
- rejects values outside configured options,
- treats empty strings as default fallback,
- supports namespace contexts with `lazyllm.config.namespace("name")` and `lazyllm.namespace("name")`.

A common diagnostic pattern is to isolate environment changes, set a LazyLLM env var, verify `lazyllm.config[...]`, then restore the environment.

## Components and registry

Core component behavior is tested through `lazyllm.components.register` and `ComponentBase`:

- `comp_register.new_group("group")` creates a new group exposed under `lazyllm.<group>`.
- `@comp_register("group")` registers callables under original and normalized names.
- Component subclass names can automatically create nested groups and aliases.
- Tool function registration (`fc_register`) is covered more deeply by agents-tools, but core import diagnostics may still touch its metadata.

## Prompters

LazyLLM prompters are safe to exercise without models:

- `lazyllm.Prompter(prompt="hello <{input}>")` can format string or dict input.
- `lazyllm.Prompter.from_template("alpaca")` loads a built-in template.
- `lazyllm.AlpacaPrompter` and `lazyllm.ChatPrompter` support plain text and `format="openai"` message dictionaries.
- Chat prompters preserve conversation history as user/assistant pairs and can apply model-specific separators.

## Launcher and server notes

Launcher tests cover local launcher behavior and `ServerModule` integration. Starting servers can bind ports or spawn subprocesses, so core smoke tests should prefer import/signature checks. If a task asks to run a service, route to model-deployment or the workflow owner and require an explicit port/back-end plan.

## Maintainer guidance from repo rules

Repo-local guidance emphasizes not bypassing public package surfaces when changing code in subpackages. For skill use, this means future agents should prefer documented public APIs, selected tests, and safe wrappers rather than importing deep private internals unless troubleshooting requires it.
