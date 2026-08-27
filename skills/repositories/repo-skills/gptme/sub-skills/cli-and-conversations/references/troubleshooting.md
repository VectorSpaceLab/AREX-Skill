# Troubleshooting terminal CLI and conversations

Use this guide when `gptme` terminal behavior does not match the user's expectation. For command syntax, read [cli-reference.md](cli-reference.md). For conversation workflows, read [conversations-and-automation.md](conversations-and-automation.md). For safe log inspection, use [../scripts/inspect_conversation_log.py](../scripts/inspect_conversation_log.py).

## Fast triage

1. Run help-only checks first: `gptme --help`, `gptme-util chats --help`, and `gptme-agent --help`.
2. Identify whether the problem is command construction, conversation selection, prompt context, tool selection, provider/model setup, or an external service.
3. If model credentials or provider defaults are involved, route to configuration/providers.
4. If a custom tool, MCP server, plugin, browser, or computer-use backend is involved, route to tools/extensibility.
5. If a server, Web UI, ACP, or TUI process is involved, route to server/protocols.
6. If inspecting a transcript, pass an explicit file or directory to the bundled log inspector rather than guessing what `--resume` selected.

## `gptme` command not found

Symptoms:

- `gptme: command not found`
- `gptme-util: command not found`
- `gptme-agent: command not found`

Actions:

1. Confirm `gptme` is installed in the user's intended application environment.
2. Prefer isolated installer patterns: `pipx install gptme` or `uv tool install gptme`.
3. Confirm the installer's bin directory is on `PATH` in the current shell.
4. In a source checkout, console scripts may not be available until the package is installed. Maintainer environment repair belongs to repo-development.

## Missing explicit local path

Symptom:

```text
Prompt looks like an explicit local path, but it does not exist: <path>
```

Why it happens:

- The prompt argument was exactly an explicit local path form, such as `./file`, `../file`, a rooted absolute path, `~/file`, or a drive-style path.
- `gptme` treats that as an intended file reference and fails early if it is missing.

Fixes:

- Check the current directory and path spelling.
- Use an existing path: `gptme "summarize this" ./existing-file.md`.
- If the text was meant as prose rather than a file, add words around it: `gptme "explain why ./missing-file.md is referenced in the docs"`.
- If the target is remote, use a URL, not a local-looking path.
- If a slash command was intended, use a single slash command as the first word, for example `/log`; a multi-component filesystem path is treated as a path, not as a command.

## Resume selected the wrong conversation

Key semantics:

- `gptme --name NAME` opens that named conversation. If it exists, it is resumed; if not, a new one is created.
- `gptme --resume --name NAME` requires that named conversation to exist. It does not silently fall back to the latest conversation.
- `gptme --resume` with no name chooses the latest conversation associated with the current workspace.
- `gptme --resume --workspace <project-directory>` chooses the latest conversation associated with that workspace.
- `gptme --resume --workspace @log` chooses the global latest conversation and uses a workspace under the conversation log directory.

Diagnosis commands:

```bash
gptme chats list --metadata
gptme chats search "distinctive phrase from the session"
gptme chats read <conversation-id> --limit 20
```

If there is still ambiguity, inspect candidate log directories with:

```bash
python ../scripts/inspect_conversation_log.py <conversation-log-or-directory>
```

## Fork, branch, checkpoint, snapshot, and backtrack confusion

Use the right recovery primitive:

| User intent | Correct primitive |
| --- | --- |
| Explore a new path while preserving the original transcript | `/fork NAME` or `gptme chats fork ID --at-turn N --name NAME` |
| Rewind conversation content to a previous marker or message | `/backtrack` |
| Record or restore committed workspace state | `/checkpoint` |
| Record or restore fine-grained workspace state | `/snapshot` |
| Continue the same named chat later | `gptme --name NAME` |

Important distinction: conversation fork creates a new top-level conversation. It is not a branch inside the current conversation and it does not roll back the workspace by itself.

## Conversation name rejected

Symptoms include messages about path components, whitespace, or control characters.

Rules:

- A conversation ID/name must be a single path component.
- Do not use `.`, `..`, `/`, or `\\`.
- Do not start or end with whitespace.
- Do not include control characters.
- Empty or whitespace-only `--name` normalizes to a generated random name instead of becoming a stable conversation.

Use safe names such as:

```bash
gptme --name auth-refactor-2026-01 "start refactor"
gptme --name experiment_v2 "try an alternate approach"
```

## Non-interactive mode exits before running

Symptoms:

- Non-zero exit with a message that non-interactive mode requires a prompt.
- Empty or whitespace-only prompt rejected.
- JSON output requested in interactive mode.

Fixes:

```bash
# Provide an explicit prompt.
gptme --non-interactive "hello world"

# Resume an existing conversation.
gptme --non-interactive --resume

# Pipe stdin.
echo "hello" | gptme --non-interactive

# JSONL output requires non-interactive mode.
gptme --non-interactive --output-format json "summarize this"
```

Do not use `--output-format json` for an interactive chat. Keep stdout clean if another program will parse JSONL.

## Stdin and `-` separator surprises

Rules:

- Piped stdin is appended to the first prompt as a fenced `stdin` block.
- If prompt arguments are provided and stdin is a non-TTY with no data, `gptme` can switch to non-interactive mode to avoid terminal errors.
- The standalone `-` argument separates chained prompts only when it appears between prompt groups.
- A single prompt equal to `-` remains literal content.

Examples:

```bash
# stdin included in first prompt.
git diff | gptme "review this diff"

# three chained turns.
gptme "read the test" - "fix the code" - "run the test"

# literal dash prompt.
gptme --non-interactive -
```

## Tool allowlist usage errors

Common causes:

- `--tools none,shell` combines `none` with another tool.
- `--tools +browser,-shell` mixes additive and exclusion syntax.
- `--tools shell,-browser` mixes bare tool names with exclusion syntax.
- `--tools ./tool.bash` points to a non-`.py` custom tool.
- `--tools ./missing-tool.py` points to a missing custom tool file.
- `--tools=-browser` was needed because a bare `--tools -browser` can be parsed as an option.

Safer forms:

```bash
gptme --tools none "pure chat"
gptme --tools shell,read,patch,save "fix a bug"
gptme --tools +subagent "plan a refactor"
gptme --tools=-browser "summarize local files only"
```

If the problem is tool behavior after selection, route to tools/extensibility.

## Context minimization did not do what the user expected

Facts:

- `--context files` includes project files but skips dynamic context commands.
- `--context cmd` includes dynamic context command output but not project prompt files.
- `--context all` includes both.
- `--no-workspace` skips all workspace prompt files and dynamic context commands.
- Tools and core prompt text still load with `--no-workspace`.
- `--no-workspace` and `--context` are mutually exclusive.

Diagnosis:

```bash
gptme --show-prompt-stats
gptme --system short --tools shell,read --context files --show-prompt-stats
gptme --no-workspace --system short --tools shell,read --show-prompt-stats
```

## Slash command not recognized

Checks:

1. In a running chat, use `/help` to list registered commands.
2. Confirm the first word starts with exactly one slash. `/shell` is a command; a multi-component filesystem path is not.
3. Tool-provided commands appear only when the corresponding tool is enabled.
4. Provider/account commands may require provider setup; route those details to configuration/providers.
5. Plugin/MCP/lesson/custom command behavior routes to tools/extensibility.

## `gptme chats send` did not appear immediately

`gptme chats send ID MESSAGE` queues a regular follow-up prompt for a running conversation. It is drained between turns. If the active assistant step is long-running, the queued prompt may not appear until that step completes. If the conversation already exited, the prompt may remain queued until the conversation is resumed.

Diagnosis:

```bash
gptme chats list --metadata
gptme chats read <conversation-id> --limit 10
python ../scripts/inspect_conversation_log.py <conversation-directory>
```

## Agent service issues

Symptoms:

- `No supported service manager found`
- missing `autonomous-run.sh`
- `gptme-agent install` fails
- logs do not update

Actions:

1. Use help/status checks first: `gptme-agent --help`, `gptme-agent status --all`, `gptme-agent scan`.
2. Confirm the command is being run from the intended agent workspace, or pass `--workspace <agent-workspace>` where supported.
3. If the workspace has not been created, use `gptme-agent create <agent-workspace> --name NAME` or the minimal `--no-template` form.
4. Run `gptme-agent doctor <agent-workspace>` before using `--fix`.
5. Treat `install`, `start`, `stop`, `restart`, `run`, and `uninstall` as host/service mutations requiring explicit approval.
6. Use `gptme-agent logs NAME --lines 100` before `--follow` if the user only needs a snapshot.

