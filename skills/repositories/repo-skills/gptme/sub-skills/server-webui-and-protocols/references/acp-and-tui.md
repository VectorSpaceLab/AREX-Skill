# ACP and TUI operations

This reference covers the Agent Client Protocol (ACP) launch paths and the optional Textual-based terminal UI.

## ACP launch matrix

ACP is for editor/client protocol integration, not for normal interactive terminal chat.

Common launch shapes:

```bash
uvx gptme-acp
pipx install gptme-acp
gptme-acp
pipx install 'gptme[acp]'
gptme-acp
python -m gptme.acp
```

Practical differences:

| Launch shape | Use when | Notes |
| --- | --- | --- |
| `uvx gptme-acp` | ACP-compatible editor wants zero persistent install | The shim package depends on `gptme[acp]` and exposes the ACP server as its default executable. |
| `pipx install gptme-acp` then `gptme-acp` | User wants a persistent shim executable | Registry-friendly because the package name is plain `gptme-acp`. |
| `pipx install 'gptme[acp]'` then `gptme-acp` | User already installs gptme directly | Installs the same ACP dependency extra in the main package. |
| `python -m gptme.acp` | Direct module launch in an environment that already has gptme installed | Useful for editor configuration that accepts module commands. |

Why the shim package exists: ACP registries can launch a plain package default executable, but cannot reliably express extras-qualified specs such as `gptme[acp]` or `uvx --from ...` shapes.

## Safe ACP checks

Prefer import/smoke checks over `--help` for ACP. The ACP entry point immediately captures stdio and waits for JSON-RPC, so conventional help output is not its primary contract.

Read-only checks:

```bash
python -c "import gptme.acp.agent as a; print(a.GptmeAgent.__name__)"
python -c "import gptme.acp.__main__ as m; print(callable(m.main))"
```

If checking the shim package, use package-manager metadata or an editor dry-run. Do not start `gptme-acp` manually and wait for a chat prompt; it is waiting for an ACP client on stdio.

## ACP protocol lifecycle

`GptmeAgent` implements the ACP agent behavior. High-level lifecycle:

1. `initialize` imports ACP dependencies lazily, initializes gptme, advertises implementation info, and reports API-key auth methods when supported by the ACP schema.
2. `new_session` creates or resumes a gptme conversation for the requested workspace. With a `cwd`, it derives a stable `acp-<hash>` session id so editor restarts can resume.
3. `prompt` converts ACP content blocks into gptme messages, runs gptme chat steps, streams assistant text through `session/update`, forwards tool results, and returns an ACP stop reason.

Additional behavior:

- Per-project model overrides can be read from the session workspace config.
- ACP sessions expose two modes when the client supports them: `default` for interactive tool confirmation and `auto` for autonomous/no-confirm tool execution.
- Slash commands are handled locally where possible; unsafe process-control commands such as `/exit` and `/restart` are blocked in ACP mode.
- Tool calls can be reported to the editor and may request permission through the ACP client UI.
- Streaming uses batched `session/update` calls; tool results are forwarded separately from assistant text.

## Server-side ACP step mode

The HTTP server can opt a conversation session into ACP-backed execution with the `use_acp` boolean in a `/step` request. A server-wide default can also be enabled with `GPTME_USE_ACP_DEFAULT` (or `USE_ACP_DEFAULT`) set to a truthy value.

Limitations of this server-side ACP path compared with the in-process step path:

- It runs a per-session ACP subprocess.
- Tool execution happens autonomously inside that subprocess.
- It does not provide the same per-token behavior as the normal in-process path in all cases; the bridge forwards best-effort text chunks.
- A background health monitor cleans up stale sessions and dead ACP subprocesses.

Use it only when the integration specifically needs ACP-backed server execution; otherwise the normal `/step` path is simpler.

## ACP stdio failure modes

ACP uses JSON-RPC over stdio. This creates non-obvious failure modes:

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Editor reports garbled JSON or protocol parse errors | A wrapper, shell banner, logger, or import printed to stdout | Ensure only the ACP transport writes to stdout. Put logs on stderr. |
| Process appears idle when run manually | It is waiting for an ACP client to send `initialize` | Test through an ACP-compatible editor/client or use import smoke checks. |
| Missing dependency error | `agent-client-protocol` is not installed | Install `gptme-acp` or `gptme[acp]`. |
| Editor hangs with no visible config error | gptme initialization failed and the editor did not surface stderr | Check stderr logs; verify provider/model configuration before launch. |
| Tool permission never resolves | Client did not answer the permission request, or ACP schema/client support differs | Enable protocol logs and verify the editor's permission UI. |

Diagnostics:

- Set `GPTME_ACP_LOG_PROTOCOL=1` to log protocol messages to stderr.
- Set `GPTME_LOG_LEVEL=DEBUG` for broader debug logging.
- Keep wrapper scripts silent on stdout.

## TUI install and help checks

The TUI requires the optional `tui` extra:

```bash
pipx install 'gptme[tui]'
```

Safe check:

```bash
gptme-tui --help
```

Expected options include `--resume`, `--name`, `--model`, `--workspace`, `--tools`, `--tool-format`, `--no-confirm`, `--inline`, `--experimental-jelly-errors`, and `--verbose`.

## TUI usage

Common patterns:

```bash
gptme-tui                         # new random conversation in current directory
gptme-tui --resume                # resume most recent conversation
gptme-tui -n my-conversation      # create/open named conversation
gptme-tui --inline                # render into terminal scrollback
```

Important options:

| Option | Meaning |
| --- | --- |
| `-n`, `--name` | Conversation name to open or create. `random` generates a name. |
| `-r`, `--resume` | Resume the most recently modified conversation. |
| `-m`, `--model` | Model for the session. |
| `-w`, `--workspace` | Workspace directory. Defaults to current directory. |
| `-t`, `--tools` | Comma-separated tool allowlist. |
| `--tool-format` | `markdown`, `xml`, or `tool`. |
| `--no-confirm` | Skip tool confirmation prompts. |
| `--inline` | Use terminal scrollback instead of the alternate screen. |
| `--experimental-jelly-errors` | Animated error messages and recovery hints. |
| `-v`, `--verbose` | Verbose logging. |

The TUI and CLI use the same conversation storage format. A user can start in TUI and resume in CLI, or start in CLI and resume in TUI.

## TUI capabilities and limitations

Capabilities:

- Prompt queueing while the agent is busy.
- Compact/collapsible tool output.
- Status bar with model, token usage, and agent state.
- Confirmation dialog before tool execution.
- Slash-command completion through the shared command registry.

Limitations:

- Non-interactive and scripted workflows should use the plain `gptme` CLI.
- Commands that require external terminal programs, such as editor-spawning flows, may not work in TUI; resume in CLI for those.
- Inline mode trades away in-place expansion of past tool output for native terminal scrollback. Use the normal alternate-screen TUI when in-place tool expansion matters.

Route general CLI prompt/log/slash-command questions to `cli-and-conversations`; this reference only covers TUI-specific operation and ACP protocol integration.
