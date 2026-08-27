# CLI reference

`honcho` is the operator-facing terminal for inspecting and debugging a Honcho
deployment.

## Global behavior

- Interactive output is human-friendly.
- Piped output or `--json` produces machine-friendly JSON.
- Errors are structured so automation can inspect the code and message.
- Workspace, peer, and session scope are per-command; they are not persisted as
  hidden CLI defaults.

## Top-level commands

- `honcho init` — confirm or set the API key and server URL in the shared CLI
  config file.
- `honcho doctor` — verify connectivity, workspace health, peer health, and
  queue health.
- `honcho config` — inspect the current CLI configuration.
- `honcho workspace` — inspect, search, create, or delete workspaces.
- `honcho peer` — inspect, chat with, search, or edit peers.
- `honcho session` — inspect, view, search, and manage sessions.
- `honcho message` — list or inspect messages.
- `honcho conclusion` — list, search, create, or delete conclusions.

## Key command families

### Onboarding

- `honcho init`
  - Reads and writes `~/.honcho/config.json`.
  - Uses `HONCHO_API_KEY` and `HONCHO_BASE_URL` as non-persistent inputs.
- `honcho doctor`
  - Fastest operator health check.
  - Accepts `--json` for automation.

### Memory inspection

- `honcho workspace inspect`
- `honcho peer inspect`
- `honcho peer card`
- `honcho peer chat`
- `honcho session inspect`
- `honcho session context`
- `honcho session summaries`
- `honcho session view`
- `honcho conclusion list`
- `honcho conclusion search`

### Search and filtering

Most commands that return collections support JSON output and scope flags such
as `-w`, `-p`, `-s`, `--workspace`, `--peer`, and `--session`.

## Good CLI habits

- Pass `--json` whenever a command is being parsed by another tool.
- Check `honcho doctor` before chasing a deeper SDK or API bug.
- Use `honcho session context` to see exactly what an agent receives.
- Use `honcho peer inspect` before `honcho peer chat` so you know what the
  dialectic is likely to see.
- Inspect before delete: check the workspace or session first.

## Configuration file

The CLI shares `~/.honcho/config.json` with related Honcho tooling.
The top-level keys it owns are:

- `apiKey`
- `environmentUrl`

Everything else at the top level is left alone.

## Common error classes

- Not found or invalid scope
- Auth failure
- Server connectivity failure
- Bad CLI arguments
- Misconfigured output or JSON parsing expectations

## When to read this file

Read this file when the user is asking for a command, a flag, an output shape,
or a debugging step that should happen in the terminal rather than through the
SDK.
