# W&B CLI and Local Workflow Troubleshooting

## API Key Problems

Symptoms:

- `wandb login` prompts unexpectedly in CI.
- `wandb sync` asks to log in before uploading.
- `wandb verify` fails login checks.

Checks:

```bash
wandb status
wandb login --verify
```

Resolution patterns:

- In CI, inject `WANDB_API_KEY` through the secret manager and run `wandb login --verify` before training or syncing.
- For self-hosted W&B, pair the key with the matching host: `wandb login --host "$WANDB_BASE_URL" --verify`.
- Use `wandb login --relogin --verify` if stale credentials are being reused.
- Do not paste literal keys into scripts, issue comments, or shell snippets intended for logs.

## Self-Hosted Host Mismatch

Symptoms:

- Login succeeds against one host but sync or verify targets another.
- `wandb status` shows an unexpected base URL.
- Runs upload to public cloud instead of the intended self-hosted instance.

Checks:

```bash
echo "$WANDB_BASE_URL"
wandb status
wandb login --host "$WANDB_BASE_URL" --verify
```

Resolution patterns:

- Set `WANDB_BASE_URL` before login, init, verify, and sync in non-interactive environments.
- Use `wandb login --cloud --verify` only when intentionally switching to the public cloud.
- Re-run `wandb status` after changing host configuration.
- For dedicated/self-hosted diagnostics, use `wandb verify --host <url>` only when networked test uploads are acceptable.

## Non-Interactive Login Hangs or Fails

Symptoms:

- CI waits for an API key prompt.
- A container lacks a TTY for interactive login.

Resolution patterns:

```bash
export WANDB_API_KEY="${WANDB_API_KEY:?missing secret}"
wandb login --host "$WANDB_BASE_URL" --verify
```

- Prefer environment/secret-manager injection over key arguments.
- Ensure `WANDB_BASE_URL` is exported before login for self-hosted deployments.
- Use `wandb status` afterward, but redact credential-like fields from logs.

## Offline Runs Not Found

Symptoms:

- `wandb sync` says no runs need syncing.
- A user points at a parent directory that does not contain run transaction logs.
- The run directory exists under a different `WANDB_DIR`.

Checks:

```bash
python sub-skills/cli-and-local-workflows/scripts/inspect_wandb_local_state.py --root .
wandb sync --show 20
find wandb .wandb -name '*.wandb' -maxdepth 3 2>/dev/null
```

Resolution patterns:

- Sync the exact run directory or exact `run-<RUN_ID>.wandb` file.
- Check both `wandb/` and `.wandb/` directories.
- If training used `WANDB_DIR`, inspect that directory rather than the current working directory.
- Use `--include-offline`, `--include-online`, `--include-synced`, `--include-globs`, and `--exclude-globs` to adjust candidate selection.

## Recover Unsynced Offline Runs Without Deleting Data

Safe sequence:

```bash
wandb status
wandb sync --show 50
wandb sync ./wandb/offline-run-YYYYMMDD_HHMMSS-RUN_ID/run-RUN_ID.wandb \
  --project my-project --entity my-team --no-mark-synced
```

Then verify in the W&B UI or with an approved API query. Only after the user confirms recovery should you consider marking synced or cleaning local copies.

Avoid:

- `wandb sync --clean` before upload verification.
- `wandb sync --clean-force` unless the user explicitly accepts deletion.
- Broad `--sync-all` before confirming host, project, entity, and candidate list.

## Destructive Cleanup Mistakes

Commands that delete local data:

```bash
wandb sync --clean
wandb sync --clean --clean-force
wandb purge-cache --force
```

Guardrails:

- Run non-destructive summaries first: `wandb sync`, `wandb sync --show N`, and the bundled inspector.
- Explain that `wandb sync --clean` removes synced run directories, not just temporary files.
- Use `--clean-old-hours` to narrow cleanup by age.
- Keep a backup or copy before cleanup if the user is uncertain.

## Cache Cleanup Confusion

`wandb purge-cache` targets files under the local W&B cache directory, selected by age. It is not the command for removing active run directories or artifact registry objects.

Use it when:

- The local cache is consuming disk.
- The user accepts deletion of cached logs, history, and artifact cache files.

Do not use it as a substitute for:

- Syncing offline runs.
- Deleting cloud artifacts.
- Removing project run directories.

## Local Service and Server Caveats

- `wandb server` is a CLI command group for operating a local W&B server, not the same as ordinary offline mode.
- `wandb verify` performs networked integration checks and may create test data; do not treat it as a pure dry-run.
- `wandb offline` writes local run data for later sync; it does not start a server.
- `WANDB_BASE_URL` changes which backend the CLI targets; it does not migrate existing offline run metadata by itself.

## Docker Credential Issues

Symptoms:

- Runs inside a container do not authenticate.
- `wandb docker-run` reports the host is not logged in.
- The image metadata variable is missing.

Resolution patterns:

- Run `wandb login --verify` on the host before `wandb docker-run`.
- Prefer `wandb docker-run ...` to inject host credentials into an existing `docker run` command.
- If using raw `docker run`, pass `WANDB_API_KEY`, `WANDB_BASE_URL`, `WANDB_ENTITY`, and `WANDB_PROJECT` through the container environment from the secret manager.
- If `WANDB_DOCKER` is missing, confirm the image name is detectable and available locally or in a registry.

## Quick Triage Checklist

1. `wandb --version` and `wandb --help` work.
2. `wandb status` shows the expected mode, base URL, entity, and project.
3. Secrets are present but redacted.
4. `wandb sync` with no arguments shows expected local candidates.
5. A single explicit offline run sync succeeds before broad `--sync-all`.
6. No `--clean`, `--clean-force`, or `purge-cache --force` is used without explicit deletion approval.
