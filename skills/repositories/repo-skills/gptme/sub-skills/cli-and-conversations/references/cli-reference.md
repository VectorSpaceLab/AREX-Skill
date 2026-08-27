# gptme CLI reference for terminal operation

This reference is a self-contained operating summary for the terminal-facing parts of `gptme` as captured from the repository evidence and installed-package facts used to build this skill. It focuses on command construction and conversation control. Provider credentials/model routing, custom tool internals, server/Web UI/ACP/TUI, eval execution, and maintainer test/release work are routed to other sub-skills.

Related local references:

- [conversations-and-automation.md](conversations-and-automation.md) for chat history, multiprompt, queued prompt, and automation recipes.
- [troubleshooting.md](troubleshooting.md) for common CLI failure modes.
- [../scripts/build_gptme_command.py](../scripts/build_gptme_command.py) to assemble safe commands without executing them.

## Installation and start patterns

Use an isolated application installer when possible:

```bash
pipx install gptme
# or
uv tool install gptme
```

A source checkout can also install `gptme` in editable mode for maintainer work, but contributor environment management belongs to the repo-development sub-skill. Optional extras affect browser/server/TUI/eval capability; this sub-skill only requires the base terminal entry points.

Start an interactive chat:

```bash
gptme
```

Start with a prompt and optional context arguments:

```bash
gptme "summarize this" README.md
gptme "what do you see?" image.png
gptme "implement this issue" <issue-url>
```

The CLI includes these terminal entry points in the verified package metadata: `gptme`, `gptme-util`, and `gptme-agent`. Other console scripts exist, but server/protocol/eval/config-specific entry points are covered by other sub-skills.

## Main command shape

```bash
gptme [OPTIONS] [PROMPTS]...
```

If prompt arguments are provided, `gptme` starts or resumes a conversation and sends them as user input. Without prompt arguments, interactive mode lets the user choose a previous chat or start a new one.

Important prompt parsing rules:

- Multiple prompt arguments without a standalone separator are joined into one user message with blank lines.
- A standalone `-` argument between prompts separates chained turns: `gptme "first" - "second"`.
- A lone `-` by itself remains a literal prompt; it is not a read-stdin marker.
- Piped stdin is appended to the first prompt as a fenced `stdin` block, or becomes the prompt if no prompt argument was given.
- Mentioned local text files, URLs, and image files can be included as prompt context by the main chat path.
- An argument that looks like an explicit local path (`./file`, `../file`, a rooted absolute path, `~/file`, or a drive-style path) fails early if the path does not exist.
- Slash commands such as `/log` are user messages handled by the conversation command system when the first word is a single-slash command. A multi-component filesystem path is not treated as a slash command.

## High-value options

| Option | Operating use |
| --- | --- |
| `--name NAME` | Use a stable conversation ID/name. Also resumes that same named conversation if it already exists. Unsafe names with path traversal, separators, control characters, or leading/trailing whitespace are rejected. |
| `-r`, `--resume` | Resume a previous conversation. With no explicit `--name`, the selected conversation is filtered by the current workspace unless `--workspace @log` is used. |
| `-w`, `--workspace PATH` | Set the workspace directory. The special value `@log` uses a workspace inside the conversation log directory and makes `--resume` choose the global latest conversation instead of filtering by current workspace. |
| `--agent-path PATH` | Attach a persistent agent workspace to the conversation context. Use the `gptme-agent` map below for workspace creation and service management. |
| `-m`, `--model MODEL` | Select a model for this run. Empty model names and empty provider/model path components are rejected. Provider credentials and model defaults are routed to the configuration/providers sub-skill. |
| `--system VALUE` | Choose `full`, `full-noexamples`, `short`, or a custom system prompt value. `short` is useful with minimal context. |
| `--context all|files|cmd` | Include only selected workspace context sections. Can be repeated or comma-separated. |
| `--no-workspace` | Skip all project-specific prompt files and dynamic context commands. Tools and core prompt content still load. Mutually exclusive with `--context`. |
| `-t`, `--tools SPEC` | Control CLI tool availability. Syntax is summarized below; tool internals route to tools/extensibility. |
| `--agent-profile NAME` | Apply an agent profile. Use `gptme-util profile list` to inspect available profiles. |
| `--tool-format markdown|xml|tool` | Select tool-call format for the session. |
| `-y`, `--no-confirm` | Skip confirmation prompts while staying interactive. Use with care. |
| `-n`, `--non-interactive` | Run all supplied prompts and exit. Implies no confirmation prompts. Required for reliable scripts/CI. |
| `--output-format text|json` | Output text or JSONL. JSON output is only valid with non-interactive mode. |
| `--show-prompt-stats` | Print startup prompt token sections and exit before chat execution. Useful for diagnosing context cost. |
| `--show-hidden` | Show hidden system messages when printing conversation content. |
| `--version`, `--version-json` | Print version info and exit. |

## Tool-selection syntax from the CLI

`--tools` replaces or modifies the default tool set before the chat starts:

```bash
# No tools; pure chat.
gptme --tools none "what is 2+2"

# Replace defaults with exactly these tools.
gptme --tools shell,read,patch,save "fix the failing test"

# Add one tool on top of defaults.
gptme --tools +subagent "plan a refactor"

# Exclude one tool from defaults. Use the equals form if the value begins with '-'.
gptme --tools=-browser "summarize the code"
```

Validation rules that matter operationally:

- `none` cannot be combined with other tool names.
- Additive `+tool` syntax and exclusion `-tool` syntax cannot be mixed in one invocation.
- Bare tool names cannot be mixed with exclusion syntax.
- Custom tool paths are accepted syntactically only when they are `.py` files and the file exists; custom tool authoring itself is handled by tools/extensibility.

## Minimal-context command patterns

Use this when the user wants to reduce startup context or isolate a task:

```bash
gptme --system short --tools shell,read,patch,save --context files "fix the failing test"
```

Use this when the user wants no project prompt files or dynamic workspace context:

```bash
gptme --no-workspace --system short --tools shell,read,patch,save "apply this patch"
```

Measure the startup prompt without entering a chat:

```bash
gptme --show-prompt-stats
gptme --system short --tools shell,read --context files --show-prompt-stats
```

## Slash commands inside a conversation

Common built-in slash commands:

| Command | Use |
| --- | --- |
| `/help` | Show available commands and keyboard shortcuts. |
| `/log` or `/log --hidden` | Print visible messages, or include hidden system messages. |
| `/edit` | Edit the conversation in the configured editor and reload it. |
| `/undo [N]` | Undo recent messages/actions. |
| `/rename NAME`, `/rename auto` | Rename the conversation display name. Auto-rename may require model access. |
| `/fork NAME` | Create a new top-level conversation from the current point. |
| `/delete [ID]`, `/delete --force ID` | Delete a conversation. |
| `/summarize` | Generate a conversation summary. Requires model access. |
| `/replay [last|all|TOOL]` | Replay tool operations from assistant messages. |
| `/export [FILE]` | Export the conversation as HTML. |
| `/model [MODEL]`, `/models` | Inspect or switch models; detailed provider setup routes elsewhere. |
| `/tokens`, `/context` | Inspect token usage/cost or context breakdown. |
| `/tools`, `/tools --all`, `/tools load NAME` | Inspect or load tools in the current session; tool details route elsewhere. |
| `/doctor` | Run local diagnostics. Provider/system diagnosis routes to configuration/providers. |
| `/account` | Inspect or set up providers. Route provider details elsewhere. |
| `/exit`, `/restart`, `/clear` | Exit, restart, or clear the terminal screen. |
| `/impersonate TEXT` | Add a message as if it came from the assistant, useful for controlled testing. |
| `/setup` | Run setup wizard. |
| `/plugin` | Manage plugins; plugin details route to tools/extensibility. |
| `/checkpoint`, `/snapshot`, `/backtrack` | Workspace/conversation recovery controls. Use these for rollback rather than confusing them with conversation fork. |

Tool-provided commands such as `/commit`, `/compact`, `/lesson`, `/pre-commit`, `/mcp`, and direct tool shortcuts like `/sh`, `/shell`, `/python`, and `/ipython` appear only when their tools are enabled.

## `gptme-util` and shortcut subcommands

The main CLI mirrors utility subcommands, so these forms are equivalent when the utility entry point is installed:

```bash
gptme chats list
gptme-util chats list

gptme chats search "auth module"
gptme-util chats search "auth module"
```

High-value utility families for this sub-skill:

| Command | Use |
| --- | --- |
| `gptme chats list [--metadata] [--json]` | List recent conversations. |
| `gptme chats search QUERY [-n LIMIT] [-c CONTEXT] [-m MATCHES] [--json]` | Search native conversation logs. |
| `gptme chats read ID [--system] [--start N] [-n LIMIT]` | Read messages from one conversation. |
| `gptme chats rename ID NAME` | Rename a conversation display name without moving files. |
| `gptme chats send ID MESSAGE...` | Queue a follow-up prompt for a running conversation. |
| `gptme chats fork ID --at-turn N [--name NAME]` | Fork a conversation at an explicit user turn. |
| `gptme chats export ID [-f markdown|html] [-o FILE]` | Export one conversation. Local safety-check modes exist; judge mode requires network/model credentials and is not a safe default. |
| `gptme chats clean [--delete]` | Find empty/trivial conversations; dry-run unless `--delete` is passed. |
| `gptme chats stats [ID] [--since DATE|Nd] [--json]` | Show conversation activity and token/cost stats. |
| `gptme search QUERY` | Shortcut for conversation search with discoverable defaults. |
| `gptme profile list` | List agent profiles usable with `--agent-profile`. |

## `gptme-agent` command map

`gptme-agent` manages persistent autonomous agent workspaces. A workspace is a git-backed directory with identity, memory, tasks, knowledge, lessons, project context, and an autonomous run script. Creation and service installation intentionally write files or install scheduler/service entries; do them only when the user requested persistent agent setup.

| Command | Safe interpretation |
| --- | --- |
| `gptme-agent --help` | Help-only command; safe first check. |
| `gptme-agent create <agent-workspace> --name NAME` | Create a template-based agent workspace. Mutates the target directory and may clone a template. |
| `gptme-agent create <agent-workspace> --name NAME --no-template` | Create a minimal local workspace without the full template. Mutates the target directory. |
| `gptme-agent status [NAME] [--all]` | Show installed/detected agent status. |
| `gptme-agent list` | List installed agents for the current service manager. |
| `gptme-agent scan [--workspace PATH] [--all] [--json]` | List live local agent processes across supported runtimes. |
| `gptme-agent install [--workspace PATH] [--name NAME] [--schedule SPEC]` | Install systemd/launchd scheduling for an agent. Host-mutating; use only with explicit approval. |
| `gptme-agent start|stop|restart [NAME]` | Enable/disable/restart scheduled runs. Host-mutating. |
| `gptme-agent run [NAME]` | Trigger one immediate autonomous run through the service manager. |
| `gptme-agent logs [NAME] [--lines N] [--follow]` | Inspect recent service logs; follow mode is long-running. |
| `gptme-agent doctor [PATH] [--fix]` | Check workspace health. `--fix` may mutate simple workspace issues. |
| `gptme-agent uninstall NAME [--yes]` | Remove service entries, not the workspace directory. Host-mutating. |

