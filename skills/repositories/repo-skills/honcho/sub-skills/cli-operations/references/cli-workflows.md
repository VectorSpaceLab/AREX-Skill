# CLI workflows

## Onboarding

1. Run `honcho init`.
2. Confirm the API key and base URL.
3. Confirm the config file location and the active scope variables.
4. Run `honcho doctor`.

## Workspace inspection

- `honcho workspace inspect` shows the workspace-level inventory.
- `honcho workspace search` searches across messages in the workspace.
- `honcho workspace queue-status` reports background processing state.

## Peer debugging

- `honcho peer inspect` is the first memory inspection command.
- `honcho peer card` shows the raw card content.
- `honcho peer chat` asks the dialectic a question about a peer.
- `honcho peer representation` produces the formatted representation.
- `honcho peer search` searches that peer's messages.

## Session debugging

- `honcho session inspect` checks the current session.
- `honcho session view` shows the transcript table.
- `honcho session context` shows what an agent would receive.
- `honcho session summaries` shows the summary state.
- `honcho session peers`, `add-peers`, and `remove-peers` adjust membership.

## Message and conclusion inspection

- `honcho message list` and `honcho message get` inspect raw turns.
- `honcho conclusion list` and `honcho conclusion search` inspect derived memory.

## Output rules

- Use `--json` when the output will be parsed.
- Treat TTY output as a human format, not a stable machine format.
- Do not assume scope flags persist between commands.

## Good CLI debugging loop

1. Inspect the workspace.
2. Inspect the peer.
3. Inspect the session.
4. Inspect the message or conclusion evidence.
5. Only then decide whether the problem is data, scope, or auth.
