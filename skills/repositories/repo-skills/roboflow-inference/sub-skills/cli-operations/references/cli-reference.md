# CLI Reference

The entry point is `inference` or the module form `python -m inference_cli.main`.
Workflow image/video processing is owned by the workflow-processing sub-skill; this page only keeps the `workflows` family on the routing map.

## Top-level command map

| Command | What it covers | Typical flags |
| --- | --- | --- |
| `inference --version` | Print installed package versions. | No subcommand flags. |
| `inference server start/status/stop` | Local inference server lifecycle. | `--port`, `--env-file`, `--dev`, `--tunnel`, `--volume`, `--image`, `--use-local-images`, `--metrics-enabled`, `--roboflow-api-key`. |
| `inference infer` | One-shot inference on an image, directory, or video. | `--input`, `--model_id`, `--host`, `--api-key`, `--output_location`, `--display`, `--visualise`, `--visualisation_config`, `--model_config`. |
| `inference benchmark api-speed` | Benchmark HTTP inference against a server or hosted endpoint. | Model or workflow flags, dataset selection, request counts, output path, confirmation, and error-rate threshold. |
| `inference benchmark python-package-speed` | Benchmark the installed `inference` package locally. | `--model_id`, dataset selection, warmup/benchmark counts, output path. |
| `inference benchmark inference-models-speed` | Experimental local `inference_models` benchmark. | Package-selection and trust flags. |
| `inference cloud deploy/start/stop/status/undeploy` | SkyPilot-based cloud VM deploys. | `--provider`, `--compute-type`, `--dry-run`, `--custom`, `--roboflow-api-key`. |
| `inference rf-cloud data-staging ...` | Roboflow batch staging, inspection, export, and ingest reporting. | Batch IDs, source selectors, file paths, API key, debug mode. |
| `inference rf-cloud batch-processing ...` | Roboflow Cloud workflow jobs and TRT compilation jobs. | Batch/job IDs, workflow params, machine sizing, notifications, logs. |
| `inference enterprise inference-compiler compile-model` | Direct enterprise TensorRT compilation. | `--model-id`, compilation mode, TensorRT compatibility flags, Docker image, env file, API key. |
| `inference workflows ...` | Workflow processing commands. | Hand off to workflow-processing. |

## Shared naming pitfalls

- Command names are hyphenated, but long option names are mixed: some keep underscores such as `--model_id` and `--output_location`, while others use hyphens such as `--workflow-id` and `--max-runtime-seconds`.
- Copy the exact spelling from the command help or from this reference. Do not normalize the names.
- Several commands use `--help` in a custom way. For example, `inference cloud deploy --help` prints the app-specific deployment primer in addition to Typer's help.

## `server`

### Minimal patterns

```bash
inference server start --port 9001
inference server status
inference server stop
```

### `start`

Key flags:

- `--port`, `-p`: exposed port, default `9001`.
- `--rf-env`, `-rfe`: Roboflow environment string, default `roboflow-platform`.
- `--env-file`, `-e`: path to `KEY=VALUE` lines. Explicit CLI flags override matching env-file keys.
- `--dev`, `-d`: development mode. Enables notebook/builder behavior and also opens port `9002`.
- `--roboflow-api-key`, `-k`: API key injected into the container environment.
- `--tunnel`: start a Roboflow tunnel after the server starts.
- `--image`: pin a specific Docker image instead of auto-selecting one.
- `--use-local-images/--not-use-local-images`: reuse or force-pull the image.
- `--metrics-enabled/--metrics-disabled`: control metrics.
- `--volume`, `-v`: repeatable volume mount flag.

Volume format must be `/host/path:/container/path[:ro]`.

### `status`

Shows whether an inference server container is running and prints basic container metadata.

### `stop`

Stops running inference containers and the tunnel container if present.

## `infer`

### Minimal patterns

```bash
inference infer --input ./image.jpg --model_id my-project/1
inference infer --input ./image.jpg --model_id my-project/1 --host http://localhost:9001
```

### Behavior

- Input can be a single image, a directory, a video file, or a URL.
- The command auto-detects video by extension and directories by filesystem path.
- `--host` defaults to `http://localhost:9001` and can also point at a hosted endpoint.
- `--api-key` falls back to `ROBOFLOW_API_KEY`.
- `--output_location` writes predictions and any requested visualisations to disk.
- `--display` and `--visualise` control on-screen display and visualisation generation.
- `--visualise` defaults to true.
- `--visualisation_config`, `-c` accepts either a bundled config name or a YAML path.
- `--model_config`, `-mc` accepts a YAML model-configuration file.

### Output pattern hints

- Image and directory inputs write `*_prediction.json` and optional JPG outputs.
- Video inputs write frame-numbered JSON outputs, and when visualisation is enabled they can also write a preview video.

## `benchmark`

### `api-speed`

Minimal model benchmark:

```bash
inference benchmark api-speed --model_id my-project/1 --dataset_reference coco --host http://localhost:9001
```

Minimal workflow benchmark:

```bash
inference benchmark api-speed \
  --workflow-id my-workflow \
  --workspace-name my-workspace \
  --workflow-specification '{"type":"workflow-specification"}' \
  --workflow-parameters '{"threshold":0.5}'
```

Important flags:

- `--model_id`, `-m`: benchmark a model endpoint.
- `--workflow-id`, `-wid`: benchmark a hosted workflow.
- `--workspace-name`, `-wn`: workspace for hosted workflow benchmarks.
- `--workflow-specification`, `-ws`: inline JSON string, not a file path.
- `--workflow-parameters`, `-wp`: inline JSON string, not a file path.
- `--dataset_reference`, `-d`: predefined dataset name or image directory path. Default: `coco`.
- `--host`, `-h`: endpoint to benchmark.
- `--warm_up_requests`, `-wr`: warm-up count.
- `--benchmark_requests`, `-br`: measured request count.
- `--batch_size`, `-bs`: request batch size.
- `--clients`, `-c`: concurrent client count when `--rps` is not set.
- `--rps`: target request rate.
- `--api-key`, `-a`: API key fallback to `ROBOFLOW_API_KEY`.
- `--model_config`, `-mc`: YAML model configuration.
- `--output_location`, `-o`: save benchmark results to a file or directory.
- `--legacy-endpoints/--no-legacy-endpoints`, `-L/-l`: switch to legacy self-hosted endpoints.
- `--yes/--no`, `-y/-n`: confirm hosted benchmarks without prompting.
- `--max_error_rate`: fail the command if the measured error rate is above the threshold.

Notes:

- If the host contains `roboflow.com` and `--yes` is not set, the CLI asks for confirmation because the run may consume credits.
- When `--output_location` is omitted, the command only enforces the optional error-rate threshold.

### `python-package-speed`

```bash
inference benchmark python-package-speed --model_id my-project/1
```

Important flags:

- `--model_id`, `-m`
- `--dataset_reference`, `-d`
- `--warm_up_inferences`, `-wi`
- `--benchmark_requests`, `-bi`
- `--batch_size`, `-bs`
- `--api-key`, `-a`
- `--model_config`, `-mc`
- `--output_location`, `-o`

This command requires the local `inference` package.

### `inference-models-speed`

This experimental command benchmarks the `inference_models` package and adds package-selection and trust flags. Keep backend/package-selection questions out of this sub-skill.

## `cloud`

### Minimal patterns

```bash
inference cloud deploy --provider aws --compute-type gpu
inference cloud status
inference cloud stop my-cluster
inference cloud start my-cluster
inference cloud undeploy my-cluster
```

### `deploy`

Important flags:

- `--provider`, `-p`: `aws` or `gcp`.
- `--compute-type`, `-t`: `cpu` or `gpu`.
- `--dry-run`, `-d`: print the SkyPilot config without launching.
- `--custom`, `-c`: path to a custom SkyPilot YAML file.
- `--roboflow-api-key`, `-r`: inject the Roboflow API key into the deployment.
- `--help`, `-h`: print the app-specific deployment primer.

Notes:

- The cloud family requires `inference[cloud-deploy]` and the `sky` dependency.
- `status`, `start`, `stop`, and `undeploy` take the cluster name as a positional argument.

## `rf-cloud data-staging`

### Common commands

- `list-batches` (`--pages`, `--page-size`)
- `list-batch-content` (`--part-name`, `--limit`, `--output-file`)
- `create-batch-of-images`
- `create-batch-of-videos`
- `show-batch-details`
- `export-batch`
- `list-ingest-details` (`--page-size`)

### Key flags

- `--api-key`, `-a`: Roboflow API key fallback to `ROBOFLOW_API_KEY`.
- `--debug-mode/--no-debug-mode`: show stack traces instead of only concise command failures.
- `--batch-id`, `-b`: required batch identifier.
- `--batch-name`, `-bn`: display name for the batch.
- `--ingest-id`, `-i`: explicit ingest identifier when relevant.
- `--notifications-url`: webhook for ingest notifications.
- `--notification-category`: filter ingest notifications.
- `--output-file`, `-o`: JSONL output file for list commands.
- `--target-dir`, `-t`: export destination.
- `--override-existing/--no-override-existing`: allow partial exports to be resumed or overwritten.

### `create-batch-of-images`

`--data-source`, `-ds` accepts:

- `local-directory`: use `--images-dir`.
- `references-file`: use `--references`.
- `cloud-storage`: use `--bucket-path`.
- `roboql`: use `--query`.

`--bucket-path` can include an optional glob and supports S3, GCS, and Azure paths.

### `create-batch-of-videos`

`--data-source`, `-ds` accepts:

- `local-directory`: use `--videos-dir`.
- `references-file`: use `--references`.
- `cloud-storage`: use `--bucket-path`.

Video batches do not expose the RoboQL source branch.

### `list-batch-content` and `export-batch`

- `list-batch-content` supports `--part-name`, `--limit`, and `--output-file`.
- `export-batch` supports `--part-name`, `--target-dir`, and `--override-existing`.
- `list-ingest-details` uses `--page-size` when pagination needs to be limited.

## `rf-cloud batch-processing`

### Common commands

- `list-jobs` (`--max-pages`)
- `show-job-details` (`--job-id`)
- `process-images-with-workflow`
- `process-videos-with-workflow`
- `trt-compile`
- `abort-job` (`--job-id`)
- `restart-job` (`--job-id`)
- `fetch-logs` (`--job-id`, `--log-severity`, `--output-file`)

### Shared flags

- `--api-key`, `-a`
- `--debug-mode/--no-debug-mode`
- `--job-id`, `-j`
- `--notifications-url`
- `--job-name`, `-jn`

### Workflow-job flags

Use these for `process-images-with-workflow` and `process-videos-with-workflow`:

- `--batch-id`, `-b`
- `--workflow-id`, `-w`
- `--workflow-params`: path to a JSON file with workflow parameters.
- `--image-input-name`
- `--save-image-outputs/--no-save-image-outputs`
- `--image-outputs-to-save`
- `--part-name`, `-p`
- `--images-metadata-part-name`, `-imp` (images only)
- `--machine-type`, `-mt`
- `--workers-per-machine`
- `--machine-size`, `-ms` (deprecated; use workers per machine instead)
- `--max-runtime-seconds`
- `--max-parallel-tasks`
- `--max-image-failure-rate`
- `--aggregation-format`
- `--inference-backend`, `-ib`
- `--metadata-mapping`, `-mm` as repeatable `workflow_input=metadata_key` pairs

Video jobs also add `--max-video-fps`.

### `trt-compile`

This queues cloud model compilation instead of the direct enterprise compiler.

- `--model-id`, `-m`
- `--device`, `-d`: repeatable target devices, such as `nvidia-l4`, `nvidia-t4`, or `nvidia-l40s`.

### `fetch-logs`

- `--log-severity`: `info`, `warning`, or `error`.
- `--output-file`, `-o`: JSONL output.

## `enterprise inference-compiler`

### `compile-model`

Minimal pattern:

```bash
inference enterprise inference-compiler compile-model --model-id my-project/1
```

Important flags:

- `--model-id`, `-m`
- `--api-key`, `-a`
- `--debug-mode/--no-debug-mode`
- `--trt-forward-compatible/--no-trt-forward-compatible`
- `--trt-same-cc-compatible/--no-trt-same-cc-compatible`
- `--compilation-mode`: `auto`, `container`, or `python`.
- `--image`
- `--use-local-images/--not-use-local-images`
- `--env-file-path`

Notes:

- `auto` tries in-process compilation first and falls back to the container when `inference_models` or TensorRT is unavailable.
- `container` mode needs Docker.
- CPU inference-server images are not valid compilation images.
- The model ID must not contain spaces.

## Option-name pitfalls

- `benchmark api-speed` accepts inline JSON strings for `--workflow-specification` and `--workflow-parameters`; they are not file paths.
- `rf-cloud batch-processing --workflow-params` is a file path, not inline JSON.
- `inference infer` and `server` use a mixed underscore/hyphen flag style; copy the exact spelling from the reference.
- `inference workflows` exists, but workflow image/video processing belongs to the workflow-processing sub-skill.
