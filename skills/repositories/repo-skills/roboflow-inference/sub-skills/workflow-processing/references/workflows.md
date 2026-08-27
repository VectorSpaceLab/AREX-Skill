# Workflow command patterns and output behavior

This reference covers the `inference workflows` CLI commands that process local
images, image directories, and video files. It is self-contained: do not reopen
the source repository to answer routine workflow-processing questions.

## Command selection

| User goal | Command | Processing location |
| --- | --- | --- |
| Process one image | `inference workflows process-image` | Defaults to hosted/API execution; can use local `inference_package`. |
| Process all images in a directory | `inference workflows process-images-directory` | Defaults to hosted/API execution; can use local `inference_package`. |
| Process one video file | `inference workflows process-video` | Always local video pipeline; requires the `inference` package. |

Use sibling sub-skills for non-CLI surfaces: server startup belongs in
[`../../cli-operations/SKILL.md`](../../cli-operations/SKILL.md), and Python SDK,
HTTP, or WebRTC Workflow calls belong in [`../../sdk-webrtc/SKILL.md`](../../sdk-webrtc/SKILL.md).

## Workflow source

Each command needs exactly one practical source of Workflow definition:

1. **Local specification file**:

   ```bash
   inference workflows process-image \
     --image_path ./image.jpg \
     --output_dir ./workflow-out \
     --workflow_spec ./workflow.json
   ```

   The file is loaded as JSON before execution. Invalid paths or malformed JSON
   fail the command before processing. Use this source when the user has an
   exported Workflow spec and wants local/reproducible configuration.

2. **Roboflow-hosted Workflow identity**:

   ```bash
   inference workflows process-images-directory \
     --input_directory ./images \
     --output_dir ./workflow-out \
     --workspace_name my-workspace \
     --workflow_id my-workflow \
     --workflow_version_id 3
   ```

   `--workflow_version_id` is optional; omitting it asks for the latest version.
   A private Workflow normally needs `--api-key` or an API-key environment
   variable. Do not advise users to pass both `--workflow_spec` and hosted
   identifiers for the same run.

## Parameter merging

The Workflow commands accept a JSON parameter file plus trailing unknown CLI
options. This is intentional: command parsing allows extra args and treats them
as Workflow parameters.

```bash
cat > params.json <<'JSON'
{
  "model_id": "yolov8n-640",
  "confidence": 0.25,
  "labels": ["person", "car"],
  "save_debug": false
}
JSON

inference workflows process-image \
  --image_path ./frame.jpg \
  --output_dir ./out \
  --workspace_name my-workspace \
  --workflow_id detector \
  --workflow_params params.json \
  --confidence 0.4 \
  --save_debug true
```

Rules to remember:

- If `--workflow_params` is absent, only trailing extra args become Workflow
  parameters.
- If `--workflow_params` is present and no extra args are supplied, the JSON
  file is used as-is.
- If both are present, values from trailing extra args override matching JSON
  keys from the file.
- Extra arg values are converted only to simple types: integers, floats, and
  booleans (`yes`, `y`, `true`, `no`, `n`, `false`, case-insensitive). Multiple
  values after one name become a list. A name with no following value is ignored.
- Use `--flag true`, not a bare `--flag`, when the Workflow parameter itself is
  boolean.
- Nested objects are easiest to pass through `--workflow_params` JSON rather than
  shell arguments.

## Processing target choice

### API target for images and directories

`process-image` and `process-images-directory` default to:

```bash
--processing_target api --api_url https://detect.roboflow.com
```

Use this when the user wants hosted execution, higher request throughput, or a
local/on-prem server exposed through an HTTP API. For a local server, change
`--api_url`, for example:

```bash
inference workflows process-image \
  --image_path ./frame.jpg \
  --output_dir ./out \
  --processing_target api \
  --api_url http://localhost:9001 \
  --workspace_name my-workspace \
  --workflow_id detector
```

The API path uses an SDK client internally; if the user wants to script that
client directly, route to [`../../sdk-webrtc/SKILL.md`](../../sdk-webrtc/SKILL.md).
If they need to start `http://localhost:9001`, route to
[`../../cli-operations/SKILL.md`](../../cli-operations/SKILL.md).

For directory API processing, `--threads` controls concurrent requests. If it is
omitted, hosted Roboflow API URLs use 32 threads, while other API URLs use 1.

### Local `inference_package` target for images and directories

Use local package execution when the user wants to run the Workflow execution
engine and model manager inside the installed `inference` package:

```bash
inference workflows process-images-directory \
  --input_directory ./images \
  --output_dir ./out \
  --processing_target inference_package \
  --workflow_spec ./workflow.json \
  --model_id yolov8n-640
```

Local execution requires the `inference` package to import successfully. When it
is missing, the CLI may prompt to install it unless interactive installation is
disabled; in non-interactive jobs set `ALLOW_INTERACTIVE_INFERENCE_INSTALLATION=False`
so the command fails with an actionable install error instead of waiting.

### Video target

`process-video` has no `--processing_target` and no `--api_url`. It always calls
the local video pipeline and requires the `inference` package:

```bash
inference workflows process-video \
  --video_path ./input.mp4 \
  --output_dir ./video-out \
  --workspace_name my-workspace \
  --workflow_id detector \
  --model_id yolov8n-640 \
  --max_fps 2.0
```

For remote stream management or SDK pipeline APIs, use
[`../../sdk-webrtc/SKILL.md`](../../sdk-webrtc/SKILL.md), not this CLI sub-skill.

## Output directory safety and resume behavior

The CLI checks the target output directory before processing:

- `process-image` and `process-images-directory` reject any existing content in
  `--output_dir` unless `--allow_override` is set. Existing files or subfolders
  both count as content.
- `process-video` rejects existing files in `--output_dir` unless
  `--allow_override` is set. Existing subdirectories alone do not trigger the
  same preflight check.
- `--allow_override` does not clean the directory; it allows the command to add
  or overwrite files in place. Prefer a fresh directory for reproducible runs.

Image and directory processing create `progress.log`. It records processed image
basenames, one per line. If the same output directory is reused with
`--allow_override`, an image whose basename is already in `progress.log` is
skipped unless `--force_reprocessing` is passed.

## Single-image output layout

Typical successful output:

```text
out/
  progress.log
  image.jpg/
    results.json
    <image-output-field>.jpg
    <nested>/<image-output-field>.jpg
```

Details:

- The per-image folder is named from `basename(--image_path)`.
- `results.json` contains structured Workflow output.
- Image-valued fields are replaced in `results.json` with the literal
  `"<deducted_image>"`.
- If `--save_image_outputs` is enabled (default), image-valued fields are also
  written as `.jpg` files. Nested Workflow keys become nested directories.
- If `--no_save_image_outputs` is passed, `results.json` is still written but
  the `.jpg` image outputs are not saved.

## Image-directory output layout

Typical default output for three images:

```text
out/
  progress.log
  aggregated_results.csv
  0.jpg/
    results.json
    bounding_box_visualization.jpg
  1.jpg/
    results.json
    bounding_box_visualization.jpg
  2.jpg/
    results.json
    bounding_box_visualization.jpg
```

Additional behavior:

- Only recognized image extensions are selected from the input directory.
- `--aggregate` is enabled by default. Disable it with `--no_aggregate`.
- The default CLI aggregate format is CSV. Use `--aggregation_format jsonl` for
  JSON Lines.
- Aggregate files are named `aggregated_results.csv` or
  `aggregated_results.jsonl`.
- Every aggregate record includes an `image` field with the processed image
  basename.
- CSV aggregation converts nested lists/dicts/sets into JSON-encoded strings so
  that they fit in cells. JSONL preserves structured JSON values.
- If failures occur, a report named like
  `failed_files_processing_<timestamp>.jsonl` is written with `file_path` and
  `cause` fields.

## Video output layout

Typical default output:

```text
video-out/
  workflow_results_source_0.csv
  source_0_output_<workflow-image-field>_preview.mp4
```

Details:

- `--output_file_type csv` is the default; `--output_file_type jsonl` writes
  `workflow_results_source_0.jsonl`.
- Structured results are written per video source. For the CLI's single input
  file, the source id is `0`.
- Image-valued fields in structured records are deducted; for CSV, nested values
  are JSON-encoded strings.
- `--save_out_video` is enabled by default. It creates one preview MP4 per
  image-valued Workflow output field using the pattern
  `source_0_output_<field>_preview.mp4`.
- `--no_save_out_video` suppresses preview MP4 creation but still writes
  structured results when predictions are produced.
- `--max_fps` rate-limits video processing by dropping/skipping frames above the
  requested frame rate. This changes the number of result rows and preview
  frames; it is not merely a display throttle.

## Failure, rate, and debug controls

- `--max-failures` applies to `process-images-directory`. If omitted, failures
  are effectively unlimited for the batch. Once the count reaches the threshold,
  remaining unprocessed files are marked as aborted in the failure report.
- `--debug_mode` re-raises top-level command errors for stack traces and makes
  per-image directory failures log exception details. Without it, the CLI prints
  a concise `Command failed. Cause: ...` message and exits non-zero.
- `KeyboardInterrupt` is caught by the CLI and reports that partial results may
  not be fully consistent.
