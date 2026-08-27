# Troubleshooting

This file collects cross-cutting Honcho failure modes.

## Startup and runtime

### Symptom: API will not start

Likely causes:

- Database URI is wrong or the database is unreachable.
- Redis is unavailable when the deployment expects it.
- Embedding dimensions do not match the live schema.
- Required provider keys or model settings are missing for the selected path.

Next steps:

1. Check the database and cache connection settings.
2. Confirm the embedding dimension in config matches the stored schema.
3. Confirm the deployment is using the intended vector-store mode.
4. Review the startup log for the first validation error.

### Symptom: queue or memory updates lag behind writes

Likely cause: Honcho processes memory asynchronously.

Next steps:

- Verify the deriver worker is running.
- Check queue status for the workspace.
- Wait for the background pipeline to finish before expecting a richer
  representation.

## CLI and auth

### Symptom: CLI prompts for config every time

Likely causes:

- `~/.honcho/config.json` is missing or incomplete.
- `HONCHO_API_KEY` / `HONCHO_BASE_URL` are not set when needed.
- The wrong workspace or peer scope is being supplied per command.

### Symptom: JSON parsing fails

Likely cause: a command was run in interactive mode instead of with `--json`
or through a pipe.

Next steps:

- Add `--json`.
- Ensure the command is not attached to a TTY if machine parsing is expected.

### Symptom: auth errors or 403 responses

Likely causes:

- Wrong API key.
- Wrong workspace / peer / session scope.
- The caller is trying to access a resource outside its allowed scope.

## SDK and API misuse

### Symptom: 404 or empty result on a memory call

Likely causes:

- Wrong workspace ID.
- Wrong peer or session ID.
- The resource was never created in this workspace.

### Symptom: `peer.chat()` is slow

Likely cause: the dialectic performs live reasoning.

Next steps:

- Prefer `peer.representation()` or `session.context()` if a plain read is
  enough.
- Use the lowest reasoning level that answers the question.

### Symptom: a session or message appears with the wrong perspective

Likely cause: the request is targeting the wrong workspace/session/peer
combination.

Next steps:

- Re-check the ids.
- Re-check any per-command scope flags or environment variables.

## Development and test failures

### Symptom: test failure mentions the SDK TypeScript package

Likely cause: the supported monorepo path was not used.

Next steps:

- Use the pytest-driven TypeScript SDK test command from the repository root.
- Use direct TypeScript type checking only for static validation.

### Symptom: live provider tests fail or skip

Likely cause: credentials or model variables are missing.

Next steps:

- Confirm provider keys and model env vars.
- Treat live-provider suites as optional unless the task explicitly requires
  them.

## When in doubt

If the failure is not clearly one of the cases above, inspect the root
reference for the relevant workflow: self-hosting, integrations, CLI, or
maintenance.
