---
name: cli-operations
description: "Inspect and debug Honcho through the `honcho` terminal CLI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# CLI operations

Use this sub-skill when the task is about the `honcho` command-line interface,
its config file, command groups, JSON output, or operator debugging flows.

## What this route covers

- `honcho init` and `honcho doctor`.
- Workspace, peer, session, message, and conclusion commands.
- CLI config file semantics and environment-variable scoping.
- Human output versus JSON output.
- CLI-driven inspection of memory and queue state.

## What it does not cover

- API server startup or database setup.
- SDK integration code.
- Repo-wide test and release maintenance.

Use `sub-skills/self-hosting/` for runtime setup, `sub-skills/integrations/` for
SDK and REST usage, and `sub-skills/maintenance/` for tests and release tasks.

## Read first

- `../../references/cli-reference.md`
- `../../references/configuration-and-environment.md`
- `../../references/troubleshooting.md`
- `references/cli-workflows.md`
- `references/troubleshooting.md`
- `scripts/cli_help_capture.py`

## Typical questions this route should answer

- How do I initialize the CLI correctly?
- Which command should I use to inspect a workspace or peer?
- How do I get JSON output instead of tables?
- How do I inspect a session context or message history?
- How do I debug auth or scope issues from the terminal?

## Practical workflow

1. Start with `honcho doctor`.
2. Confirm the current config file and scoped environment variables.
3. Use the narrowest inspect command that answers the question.
4. Switch to `--json` when a machine or another tool needs the output.
5. Treat `honcho peer inspect`, `honcho session context`, and `honcho
   conclusion search` as the usual memory debugging trio.

## Decision points

- Use `honcho init` when the config file needs to be created or updated.
- Use `honcho doctor` when connectivity or queue health is uncertain.
- Use `honcho peer inspect` before `honcho peer chat`.
- Use `honcho session view` when you need the raw transcript.
- Use `honcho config` when you only need to see the active settings.

## Troubleshooting focus

This route owns problems such as:

- missing or stale config in `~/.honcho/config.json`,
- wrong base URL or API key,
- wrong workspace / peer / session scope,
- JSON parsing issues caused by human output,
- trying to inspect or delete without first checking the target,
- confusion about which CLI command family owns a workflow.

See `references/troubleshooting.md` for symptom-level guidance.

## Helpful bundled script

`scripts/cli_help_capture.py` prints the CLI help and selected subcommand help
in a repeatable way. Use it when you need the current command catalog without
reading the source tree.

## Good handoff phrases

- "How do I set up the Honcho CLI?"
- "How do I inspect a peer from the terminal?"
- "How do I read the current session context?"
- "How do I make `honcho` emit JSON?"
- "How do I debug a CLI auth problem?"
