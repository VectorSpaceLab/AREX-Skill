# W&B Cross-Cutting Troubleshooting

Read this for install/import, authentication, self-hosted host, optional dependency, source-build, and local service failures that affect more than one W&B workflow.

## Import or install fails

Symptoms:
- `ModuleNotFoundError: No module named 'wandb'`
- `ImportError` from `google.protobuf`, `pydantic`, `click`, or other core dependencies
- CLI command not found after install

Actions:
1. Verify the Python environment that will run the user code: `python -m pip show wandb` and `python -c "import wandb; print(wandb.__version__)"`.
2. Reinstall the public package in that environment: `python -m pip install -U wandb`.
3. Confirm `python -m pip check` passes.
4. If the CLI is missing, run `python -m wandb --help` as a fallback and inspect whether the environment's script directory is on `PATH`.
5. Run `python scripts/check_wandb_environment.py --check-cli` from this skill for a non-secret diagnostic summary.

## Source checkout build fails

The W&B source tree builds compiled helper artifacts for local source installs. Failures may mention missing Go, Rust/Cargo, `wandb-core`, or native build tooling.

Actions:
1. Prefer a public wheel (`python -m pip install wandb`) unless the user is intentionally developing W&B itself.
2. For source development, install the build tools named by the error, then retry the editable install.
3. Avoid installing broad optional extras unless the selected workflow needs them.
4. If optional XPU or backend artifacts fail and the task does not use that backend, look for documented build toggles or skip that optional path rather than changing runtime guidance for ordinary users.

## Authentication and host confusion

Symptoms:
- `wandb.errors.AuthenticationError`
- Public API calls fail with 401/403
- CLI logs into the wrong W&B instance
- Code works locally but fails in CI

Actions:
1. Never print the API key. Check only whether `WANDB_API_KEY` is set.
2. For non-interactive environments, configure `WANDB_API_KEY` through the secret store and run `wandb login --verify` only when network verification is intended.
3. For self-hosted or dedicated cloud, set `WANDB_BASE_URL` or use `wandb login --host URL`.
4. Use full entity/project/run paths when defaults might point to another account.
5. If verification would hit a private server or external network, ask before running it.

## Offline, disabled, and online modes are mixed up

Use cases:
- `mode="offline"` records local run data for later sync.
- `mode="disabled"` turns W&B into a no-op style run object for tests or opt-out paths.
- `WANDB_MODE=offline` or CLI `wandb offline` affects process/default behavior.

Actions:
1. For a safe local smoke test, use `mode="offline"` and a temporary run directory.
2. For unit tests that must not create run data, use disabled mode.
3. Use `wandb status` and the local workflow sub-skill to inspect active settings.
4. Use the CLI/local workflow sub-skill before syncing or deleting offline run directories.

## Optional dependency or backend missing

Symptoms:
- Artifact references to `s3://`, `gs://`, or Azure URLs fail.
- Rich media logging fails for images/video/audio/plots.
- Launch backends fail to import provider SDKs.

Actions:
1. Install only the extra or provider dependency required by the workflow.
2. For storage references, route to `../sub-skills/artifacts-and-registries/SKILL.md`.
3. For media, route to `../sub-skills/experiment-tracking/SKILL.md` and degrade to scalars/tables when rich media dependencies are unavailable.
4. For Launch, route to `../sub-skills/sweeps-and-launch/SKILL.md` and require real backend credentials/config from the user.

## Local service or `wandb-core` startup fails

Symptoms:
- Init timeout waiting for the internal service.
- A message says `wandb-core exited` or service port file creation failed.
- Runs hang on finish/upload.

Actions:
1. Reproduce with a small offline run using `sub-skills/experiment-tracking/scripts/offline_tracking_smoke.py`.
2. Check write permissions for the run directory and temp directory.
3. Reduce complexity: disable rich media, use offline mode, and avoid background uploads while isolating the issue.
4. Inspect W&B logs only for error fragments; do not expose secrets or full private paths in user-facing output.
5. If the issue happens only online, separate authentication/network/base URL failures from SDK local-service failures.
