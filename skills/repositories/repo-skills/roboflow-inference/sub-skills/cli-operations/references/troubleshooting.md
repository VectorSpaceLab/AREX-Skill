# CLI Troubleshooting

Use this for `server`, `infer`, `benchmark`, `cloud`, `rf-cloud`, and enterprise CLI failures. For workflow image/video processing details, route to the workflow-processing sub-skill unless the issue is a shared CLI startup or dependency problem.

## The CLI fails before showing help

Symptom:

```text
ModuleNotFoundError: No module named 'docker.errors'
```

What happened:

- The top-level CLI imports `inference_cli.lib` during startup, and that import pulls in Docker support.
- A missing Python dependency can break even `--help` or `--version`.

Fixes:

1. Install the CLI environment with the repo's normal editable install or the appropriate dependency set.
2. If you are only trying to inspect help text, use the bundled smoke helper after the environment is repaired.
3. Do not treat this as a command-syntax issue; it is an environment issue.

## Docker is missing or not running

Symptoms:

- `Error connecting to Docker daemon. Is docker installed and running?`
- `server start`, `server status`, `server stop`, or enterprise `compile-model` container mode exit immediately.
- The enterprise compiler prints that it is offloading to container or fails while trying to use Docker.

What happened:

- Local server lifecycle commands require Docker.
- Enterprise compilation needs Docker in container mode, and the local server also uses Docker for the inference container.

Fixes:

1. Install Docker if it is missing.
2. Start the Docker daemon before rerunning the command.
3. If you expected the enterprise compiler to stay in Python mode, use `--compilation-mode python` on a machine that already has the required local compiler dependencies.

## Invalid `--volume` formatting

Symptom:

```text
Invalid volume format: ... Expected /host/path:/container/path[:ro]
```

What happened:

- `inference server start --volume` only accepts the exact mount format above.
- The flag is repeatable, but each item must contain at least a host path and a container path.

Fixes:

1. Rewrite the mount as `/host/path:/container/path` or `/host/path:/container/path:ro`.
2. If you need several mounts, pass `--volume` multiple times.
3. Remember that explicit CLI flags override any env-file value with the same target variable.

## API key required for tunnel or cloud features

Symptoms:

- `Roboflow API Key is required to start the tunnel`
- Unauthorized or missing-key errors from `rf-cloud` commands
- Cloud deploy or cloud status commands fail immediately

What happened:

- `server start --tunnel` requires a Roboflow API key.
- `cloud` commands require the SkyPilot dependency and a valid Roboflow key when the deployment uses Roboflow-injected credentials.
- `rf-cloud data-staging` and `rf-cloud batch-processing` also need a valid key.

Fixes:

1. Pass `--api-key` or `--roboflow-api-key` where the command expects it.
2. Or export `ROBOFLOW_API_KEY` in the environment before running the CLI.
3. If you are just testing locally, omit `--tunnel` and keep the command to local server lifecycle only.

## Hosted benchmark confirmation or credit warning

Symptoms:

- The benchmark appears to pause and wait for input.
- You see the warning about potentially consuming Roboflow inference credits.

What happened:

- `benchmark api-speed` checks for `roboflow.com` in the host.
- If `--yes` is not set, the command prompts before continuing.

Fixes:

1. Pass `--yes` in automation or other noninteractive runs.
2. Use `--no` if you want the command to abort instead of continuing.
3. If you expected a local benchmark, point `--host` at your local server.

## Missing local `inference` package for workflow-related commands

Symptoms:

```text
You need to install `inference` package to use this feature
```

Where it shows up:

- `benchmark python-package-speed`
- `workflows process-image`, `process-images-directory`, and `process-video` when they run through the local package

Fixes:

1. Install the `inference` package in the environment that runs the CLI.
2. In noninteractive automation, set `ALLOW_INTERACTIVE_INFERENCE_INSTALLATION=False` to fail fast instead of prompting.
3. If the user intended workflow image/video processing, hand them to the workflow-processing sub-skill for the detailed command-specific fix.

## Non-empty output directory and override rules

Symptoms:

- Workflow commands refuse to write into the target directory.
- Export or resume behavior is unclear because stale files already exist.

What happened:

- `workflows process-image` and `process-images-directory` reject existing content unless `--allow_override` is passed.
- `workflows process-video` also refuses existing output unless `--allow_override` is passed.
- `rf-cloud data-staging export-batch` uses `--override-existing` for partial export reuse instead of the workflow-style flag.

Safe fixes:

1. Prefer a fresh output directory.
2. If you are intentionally resuming, use the command's explicit override flag.
3. For workflow directory reruns, combine `--allow_override` with `--force_reprocessing` when you really want to reprocess previously logged files.
4. If you are in the wrong command family, route the user to workflow-processing instead of inventing new flags.

## CLI misuse or option mismatch

Common mistakes and fixes:

- `inference infer` on a directory or video with only one of `--display` or `--visualise` set: the command needs either an output directory or both flags together.
- `benchmark api-speed` with file paths in `--workflow-specification` or `--workflow-parameters`: those flags expect inline JSON text, not paths.
- `rf-cloud batch-processing --metadata-mapping`: each item must be `workflow_input=metadata_key`.
- `cloud deploy`: `--provider` is only `aws` or `gcp`, and `--compute-type` is only `cpu` or `gpu`.
- `enterprise inference-compiler compile-model`: the model ID must not contain spaces.
- `rf-cloud data-staging create-batch-of-images` or `create-batch-of-videos`: the `--data-source` value must match the accompanying path flag.
- `server start --tunnel` without a key: pass `--roboflow-api-key` or `ROBOFLOW_API_KEY`.

## Cloud deploy dependency missing

Symptom:

- The `cloud` family tells you to install `inference[cloud-deploy]`.

Fix:

1. Install the cloud-deploy extra or the repo's equivalent environment.
2. Confirm that the `sky` dependency is importable before retrying.

## Enterprise compiler falls back to container

Symptom:

- `compile-model` says it is offloading to container even though you expected an in-process run.

What happened:

- `auto` mode could not import `inference_models` or did not detect TensorRT.

Fixes:

1. Install the local compiler dependencies if you want in-process execution.
2. Or accept the container fallback and ensure Docker is available.
3. If the image is a CPU image, pick a GPU/Jetson compilation image instead.

## Unsure which CLI family owns the problem

Use this routing rule:

- If the issue is `workflows process-*`, use workflow-processing.
- If the issue is Docker, server lifecycle, benchmark setup, cloud deploy, rf-cloud, or enterprise compile-model, stay here.
- If the issue is SDK/WebRTC or backend/package selection, route elsewhere.
