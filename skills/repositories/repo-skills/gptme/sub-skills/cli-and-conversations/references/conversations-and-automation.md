# Conversations, logs, multiprompts, automation, and agents

This reference explains how to keep terminal `gptme` work resumable, searchable, auditable, and safe for automation. For option details, read [cli-reference.md](cli-reference.md). For common failure modes, read [troubleshooting.md](troubleshooting.md). Use [../scripts/inspect_conversation_log.py](../scripts/inspect_conversation_log.py) when you need a local, redacted log summary.

## Conversation model

A `gptme` run is stored as a conversation: a named directory containing a `conversation.jsonl` transcript plus adjacent files such as config, attachments, queued prompts, branches/views, or workspace snapshots depending on the session. Each JSONL line is one message with fields such as `role`, `content`, `files`, `metadata`, and `call_id`.

Operational consequences:

- Conversation IDs are single path components; do not use `/`, `\\`, `.`, `..`, control characters, or leading/trailing whitespace.
- Without `--name`, new chats receive generated names.
- Reusing `--name NAME` opens the same named conversation if it already exists.
- `--resume` without a name chooses a previous conversation; by default it is filtered by the current workspace.
- `--workspace @log` changes the workspace to one under the log directory and makes unnamed resume choose the global latest conversation.
- Forking creates a new top-level conversation. It is not a branch inside the original conversation.

## Start, resume, list, and search

Start a new named conversation:

```bash
gptme --name my-refactor "let's refactor the auth module"
```

Resume by explicit name:

```bash
gptme --name my-refactor
```

Resume the most recently modified conversation for the current workspace:

```bash
gptme --resume
# short form
gptme -r
```

Resume a workspace-specific latest conversation:

```bash
gptme --resume --workspace <project-directory>
```

Resume the global latest conversation, independent of the current workspace:

```bash
gptme --resume --workspace @log
```

List and search:

```bash
gptme chats list
gptme chats list --metadata
gptme chats list --json
gptme chats search "auth module refactor"
gptme chats search "auth module" --limit 10 --context 2 --matches 3
gptme chats read my-refactor --system --start 5 --limit 20
```

Shortcut search:

```bash
gptme search "auth module"
```

## Rename, export, clean, and stats

```bash
# Change display name without moving conversation files.
gptme chats rename my-refactor better-name

# Export a conversation.
gptme chats export my-refactor --format markdown --output my-refactor.md
gptme chats export my-refactor --format html --output my-refactor.html

# Dry-run cleanup of empty/trivial conversations.
gptme chats clean

# Actually delete only after review.
gptme chats clean --delete

# Conversation statistics.
gptme chats stats
gptme chats stats my-refactor
gptme chats stats --since 7d --json
```

`chats export --safety-check` runs local heuristic safety analysis. Modes that request an LLM judge require provider credentials/network access and should not be treated as safe offline verification.

## Fork conversations deliberately

Fork during a running conversation:

```text
/fork my-experiment
```

Fork from the terminal at a specific turn:

```bash
gptme chats fork my-refactor --at-turn 3 --name my-refactor-v2
gptme --name my-refactor-v2
```

Turn semantics for `gptme chats fork`:

- `--at-turn 0` keeps only pre-user messages, such as system context.
- `--at-turn N` keeps messages through the Nth complete user+assistant exchange.
- If `N` is out of range, the command reports a usage error.
- The source conversation is not modified.

Use `/checkpoint`, `/snapshot`, or `/backtrack` when the user wants workspace rollback or conversation rewind. Use fork when the user wants a separate top-level conversation for an alternate path.

## Queue follow-up prompts

If a conversation is already running in another terminal, queue a later user turn instead of interrupting it:

```bash
gptme chats send my-refactor "when the tests finish, summarize the failures"
```

The running chat drains queued prompts between turns. The queue is durable JSONL in the conversation directory and is protected by a lock file. Queued prompts are not a general-purpose same-step steering channel; they are for the next user turn unless a specialized integration marks a steer prompt.

## Multiprompt syntax

Use a standalone `-` argument to split one CLI invocation into multiple user turns. Each turn lets the assistant respond and run tools before the next prompt is sent.

```bash
gptme "read the failing test" - "fix the implementation" - "run the tests"
```

Rules that prevent surprises:

- The separator must be exactly one argument: `-`.
- Markdown list items inside a quoted prompt are preserved and are not treated as separators.
- A lone `-` as the only prompt is literal content.
- File paths mentioned in later prompts are expanded when that prompt is processed, not at initial parse time.

Difficult multiprompt/minimal-context pattern:

```bash
gptme \
  --name refactor-tight-context \
  --system short \
  --tools shell,read,patch,save \
  --context files \
  "read the failing test and identify the smallest fix" \
  - "apply the fix only" \
  - "run the focused test and summarize the result"
```

For command construction without execution, use:

```bash
python ../scripts/build_gptme_command.py \
  --name refactor-tight-context \
  --system short \
  --tools shell,read,patch,save \
  --context files \
  --prompt "read the failing test and identify the smallest fix" \
  --prompt "apply the fix only" \
  --prompt "run the focused test and summarize the result"
```

## Prompt context from stdin, files, URLs, and images

Common terminal forms:

```bash
# Include a file or image path as prompt context.
gptme "summarize this" README.md
gptme "what do you see?" screenshot.png

# Include a URL as context.
gptme "summarize this issue" https://example.invalid/org/repo/issues/123

# Include piped stdin as a fenced stdin block.
git diff | gptme "review this diff"

# Non-interactive stdin use.
cat report.txt | gptme --non-interactive "extract the action items"
```

Path diagnosis matters: if the prompt argument is only an explicit local path and the path is missing, `gptme` fails early instead of sending a likely typo to the model. If the user intended prose, add words around it; if the user intended a file, fix the path or current working directory.

## Non-interactive automation

Use `--non-interactive` or `-n` for scripts. It skips confirmation prompts and exits after queued prompts are drained or the supplied prompt chain completes.

```bash
gptme --non-interactive "summarize this" README.md
gptme -n "read the failing test" - "fix the implementation" - "run the tests"
```

Capture text output:

```bash
gptme -n "summarize this codebase in 3 bullet points" README.md > summary.txt
```

Use JSONL output for machine parsing:

```bash
gptme --non-interactive --output-format json "summarize the current git diff"
```

Expected exit-code meaning:

| Code | Meaning |
| --- | --- |
| `0` | Task completed successfully. |
| `1` | Task failed during execution. |
| `2` | Invalid arguments or usage error. |

Automation guardrails:

1. Test prompts interactively before scheduling them.
2. Use named conversations for auditability.
3. Restrict tools with `--tools` instead of relying on a broad default set.
4. Keep autonomous code changes inside a reviewable worktree.
5. Review `git status` and `git diff` before staging or committing.
6. Redirect stdout/stderr to a log file for scheduled jobs.
7. Treat provider keys, network publishing, deployment, and external mutations as separate approval boundaries.

Review-gated autonomous pattern for code changes:

```bash
# 1. Work in an isolated branch/worktree chosen by the operator.
cd <project-worktree>

# 2. Let gptme work non-interactively inside the checkout.
gptme -n \
  "read the issue and identify the relevant files" \
  - "implement the requested change" \
  - "run the focused checks and fix failures" \
  - "summarize the final diff"

# 3. Deterministically review before delivery.
git status --short
git diff
```

Commit, push, and pull-request creation are maintainer or operator actions. Follow the repository's own contribution policy rather than assuming broad permission.

## Persistent `gptme-agent` workflows

Use `gptme-agent` when the user wants a persistent agent workspace with identity, memory, tasks, knowledge, lessons, project context, and scheduled autonomous runs.

Help and discovery:

```bash
gptme-agent --help
gptme-agent scan
gptme-agent scan --workspace <parent-directory> --json
gptme-agent status --all
gptme-agent list
```

Create a workspace:

```bash
gptme-agent create <agent-workspace> --name MyAgent
# Minimal workspace without the full template:
gptme-agent create <agent-workspace> --name MyAgent --no-template
```

Run interactively from the workspace:

```bash
cd <agent-workspace>
gptme "your prompt here"
```

Install scheduled autonomous operation only with explicit host-mutation approval:

```bash
cd <agent-workspace>
gptme-agent install --schedule "*:00/30"
gptme-agent status
gptme-agent logs --follow
gptme-agent run
gptme-agent stop
gptme-agent start
gptme-agent restart
gptme-agent doctor
```

Service-manager actions install or modify systemd/launchd entries on supported hosts. If the task is only to understand an agent, prefer `status`, `scan`, `logs`, and `doctor` without `--fix`.

