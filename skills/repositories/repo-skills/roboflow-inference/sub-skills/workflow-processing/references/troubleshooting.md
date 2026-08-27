# Workflow CLI troubleshooting

Use this for workflow-specific failures in `inference workflows process-image`,
`process-images-directory`, and `process-video`. For server startup, Docker, or
non-Workflow CLI issues, route to [`../../cli-operations/SKILL.md`](../../cli-operations/SKILL.md).
For Python SDK, HTTP, or WebRTC API issues, route to
[`../../sdk-webrtc/SKILL.md`](../../sdk-webrtc/SKILL.md).

## Output directory is not empty

Symptom:

```text
Detected content in output directory: ... Command cannot run, as content override is forbidden.
Use `--allow_override` to proceed.
```

What happened:

- `process-image` and `process-images-directory` reject any existing file or
  subdirectory in `--output_dir` unless `--allow_override` is passed.
- `process-video` rejects existing files unless `--allow_override` is passed.
- The override flag does not clean the folder; it only allows the command to
  write into it.

Safe fixes:

1. Prefer a fresh output directory for a clean run.
2. If intentionally resuming or merging, add `--allow_override`.
3. If image files were skipped because their basenames already appear in
   `progress.log`, also add `--force_reprocessing` when reprocessing is desired.
4. If stale outputs are confusing aggregation, delete or archive the output
   directory and rerun from scratch.

## Invalid `--workflow_spec` or `--workflow_params`

Symptoms:

- Command fails before processing.
- Concise output says `Command failed. Cause: ...` with a JSON parse or file path
  error.
- Hosted/local source errors complain that Workflow identifiers and specification
  are missing or mutually exclusive.

Checks:

```bash
python -m json.tool ./workflow.json >/dev/null
python -m json.tool ./params.json >/dev/null
```

Rules:

- `--workflow_spec` must point to a readable JSON Workflow specification.
- `--workflow_params` must point to readable JSON parameters. Keep complex
  nested parameter structures in this file rather than trying to encode them in
  shell arguments.
- Use either `--workflow_spec` or `--workspace_name` plus `--workflow_id`; do not
  supply both as the Workflow source.
- When both `--workflow_params` and trailing extra args are used, the extra args
  override matching file keys. Unexpected results often come from an extra arg
  that shadows the JSON file value.

The bundled helper can validate both JSON files and summarize an output folder:

```bash
python sub-skills/workflow-processing/scripts/inspect_workflow_outputs.py \
  --workflow-spec ./workflow.json \
  --params-json ./params.json \
  --output-dir ./out \
  --mode auto
```

Run the helper from the generated repo-skill root, or adjust the path to the
script.

## Missing local `inference` package

Symptoms:

```text
You need to install `inference` package to use this feature. Run `pip install inference`
```

Where it happens:

- `process-image --processing_target inference_package`
- `process-images-directory --processing_target inference_package`
- every `process-video` run

Fixes:

1. Install the package in the environment that runs the CLI, for example
   `pip install inference` or an editable install when developing the repo.
2. In non-interactive automation, set
   `ALLOW_INTERACTIVE_INFERENCE_INSTALLATION=False` so the command fails instead
   of prompting for an install.
3. If the user did not intend local execution for image or directory processing,
   switch to `--processing_target api` and set `--api_url` to the hosted endpoint
   or a running local server.
4. For video, there is no API target in this CLI command; use local package
   execution or route to SDK/pipeline APIs for a different interface.

## API versus `inference_package` target confusion

Questions to ask:

- Does the user want hosted/cloud or HTTP server execution? Use
  `--processing_target api` for image/directory commands and set `--api_url` if
  not using the default hosted endpoint.
- Does the user want in-process local Workflow execution? Use
  `--processing_target inference_package` for image/directory commands and make
  sure the `inference` package imports.
- Is the input a video file with `process-video`? There is no target switch; it
  always uses the local `inference` video pipeline.

If the user asks how to start the local server for `--api_url http://localhost:9001`,
route to [`../../cli-operations/SKILL.md`](../../cli-operations/SKILL.md). If they ask
for Python client code instead of CLI, route to [`../../sdk-webrtc/SKILL.md`](../../sdk-webrtc/SKILL.md).

## `--max_fps` does not just change playback speed

`process-video --max_fps` limits processing frame rate. The CLI enables frame
dropping for video-file rate limiting and passes the limit into the local video
pipeline. Consequences:

- Fewer frames are processed.
- The structured result file has fewer rows/records.
- Preview MP4 outputs contain fewer frames.

If the user expected every frame to be processed, remove `--max_fps` or increase
it. If they wanted faster runs or lower cost, lower `--max_fps` and warn that
results are subsampled.

## `--max-failures` stops a directory batch early

`process-images-directory --max-failures N` counts failed Workflow executions. If
failures reach `N`, the command stops submitting more images and marks the rest
as aborted in `failed_files_processing_<timestamp>.jsonl`.

Notes:

- If `--max-failures` is omitted, the batch effectively tolerates all failures
  and continues through the input set.
- With `--debug_mode`, per-image failures log exception details; without it, the
  failure report still records a concise cause.
- Successful images are written before later failures, so partial outputs can be
  valid. Use `progress.log` plus the failure JSONL to decide what to rerun.

## CSV versus JSONL aggregation confusion

Image-directory aggregation uses `--aggregation_format`, not
`--output_file_type`:

```bash
# Directory aggregate CSV, the default
--aggregation_format csv

# Directory aggregate JSONL
--aggregation_format jsonl
```

Video structured output uses `--output_file_type`:

```bash
# Video structured CSV, the default
--output_file_type csv

# Video structured JSONL
--output_file_type jsonl
```

CSV behavior:

- Lists, dicts, and sets are JSON-encoded as strings inside cells.
- Inconsistent schemas across images create sparse columns.
- An empty CSV aggregate may raise an empty-data error in downstream pandas
  reads because there were no result rows.

JSONL behavior:

- One JSON object is written per image/frame result.
- Nested JSON values are preserved more naturally for downstream scripts.

## Missing output images or preview video

For image and directory commands:

- `--no_save_image_outputs` suppresses JPG files but still writes
  `results.json`.
- If a Workflow result has no image-valued fields, no JPG files are created.
- Image-valued fields are represented as `"<deducted_image>"` in `results.json`.

For video commands:

- `--no_save_out_video` suppresses preview MP4 files.
- Preview MP4 files are created only for image-valued Workflow output fields.
- Structured results may still be present even when no preview video is saved.

## Debug mode and error reporting

Default behavior catches most command errors and prints:

```text
Command failed. Cause: <summary>
```

Use `--debug_mode` when the summary is insufficient and the user can tolerate a
stack trace. It is especially useful for invalid Workflow specs, package import
problems, API exceptions, or per-image batch failures whose concise cause hides
the source exception.

For automation, capture stdout/stderr and the exit code. A non-zero exit means
the command-level run failed; for directory processing, also inspect the
failure-report JSONL because the command may complete while individual images
failed.
