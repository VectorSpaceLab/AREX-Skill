# CLI troubleshooting

## Config keeps resetting

**Symptom:** `honcho init` appears to ask for the same values repeatedly.

**Likely cause:** the shared config file is missing, unreadable, or being
shadowed by environment variables.

**Recovery:**

- Confirm `~/.honcho/config.json` exists.
- Confirm `HONCHO_API_KEY` and `HONCHO_BASE_URL` are what you expect.
- Re-run `honcho init` and verify the saved values.

## JSON output is not parseable

**Symptom:** a command prints tables or banners instead of JSON.

**Likely cause:** the command is attached to a TTY or `--json` was omitted.

**Recovery:**

- Add `--json`.
- Pipe the command if a machine-readable result is required.

## Scope looks wrong

**Symptom:** a peer or session command hits the wrong workspace or returns
nothing useful.

**Likely cause:** the scope flags or `HONCHO_*` variables do not match the
resource being inspected.

**Recovery:**

- Re-check `-w`, `-p`, and `-s`.
- Re-run `honcho workspace inspect` and `honcho peer inspect`.

## Auth failure

**Symptom:** `honcho doctor` or another command reports auth problems.

**Likely cause:** wrong API key, wrong URL, or a stale config file.

**Recovery:**

- Re-run `honcho init`.
- Confirm the server URL.
- Confirm the key has the right scope.

## Queue or memory is stale

**Symptom:** `honcho doctor` passes, but the memory answer is not updated yet.

**Likely cause:** background processing has not caught up.

**Recovery:**

- Inspect queue status.
- Inspect the session context.
- Wait for the background pipeline before expecting a new representation.

## Wrong command family

**Symptom:** you know the goal, but the command feels awkward.

**Likely cause:** the workflow belongs to a different Honcho surface.

**Recovery:**

- Use the CLI reference to switch to the right command family.
- Fall back to the integrations sub-skill if the CLI cannot express the task.
