# Workflow CLI reference

The console entry point is `inference`; the Workflow command group is
`inference workflows`.

## Shared Workflow options

These options appear across the processing commands unless noted otherwise.

| Option | Applies to | Meaning |
| --- | --- | --- |
| `--workflow_spec`, `-ws` | image, directory, video | Path to a JSON Workflow specification file. Use instead of hosted identifiers. |
| `--workspace_name`, `-wn` | image, directory, video | Roboflow workspace for a hosted Workflow. Use with `--workflow_id`. |
| `--workflow_id`, `-wid` | image, directory, video | Hosted Workflow identifier. Use with `--workspace_name`. |
| `--workflow_version_id`, `-wvid` | image, directory, video | Optional hosted Workflow version; latest is used when omitted. |
| `--workflow_params` | image, directory, video | Path to JSON Workflow runtime parameters. Extra CLI parameters override this file. |
| `--image_input_name` | image, directory, video | Name of the Workflow input that should receive the image/frame. Default: `image`. |
| `--api-key`, `-a` | image, directory, video | Roboflow API key. Environment fallback is used when omitted. |
| `--allow_override` / `--no_override` | image, directory, video | Allow the output directory to contain or receive overwritten files. Default: no override. |
| `--debug_mode` / `--no_debug_mode` | image, directory, video | Show stack traces / detailed logged errors instead of only concise failures. |

All three commands accept trailing extra CLI args as Workflow parameters because
unknown options are intentionally allowed. Example:

```bash
inference workflows process-image \
  --image_path ./image.jpg \
  --output_dir ./out \
  --workspace_name my-workspace \
  --workflow_id detector \
  --model_id yolov8n-640 \
  --confidence 0.5 \
  --classes person car
```

The extra Workflow parameters parsed here are:

```json
{
  "model_id": "yolov8n-640",
  "confidence": 0.5,
  "classes": ["person", "car"]
}
```

## `process-image`

Purpose: process one image file with a Workflow.

Minimal hosted/API command:

```bash
inference workflows process-image \
  --image_path ./image.jpg \
  --output_dir ./out \
  --workspace_name my-workspace \
  --workflow_id detector \
  --model_id yolov8n-640
```

Minimal local-spec command:

```bash
inference workflows process-image \
  --image_path ./image.jpg \
  --output_dir ./out \
  --processing_target inference_package \
  --workflow_spec ./workflow.json \
  --model_id yolov8n-640
```

Command-specific options:

| Option | Default | Notes |
| --- | --- | --- |
| `--image_path`, `-i` | required | Path to the image to process. |
| `--output_dir`, `-o` | required | Output directory. Must be empty unless `--allow_override` is used. |
| `--processing_target`, `-pt` | `api` | `api` or `inference_package`. |
| `--api_url` | `https://detect.roboflow.com` | API endpoint used only for `--processing_target api`. |
| `--save_image_outputs` / `--no_save_image_outputs` | save | Controls whether image-valued Workflow outputs are persisted as JPG files. |
| `--force_reprocessing` / `--no_reprocessing` | no reprocessing | Reprocess even when the image basename is already in `progress.log`. Requires `--allow_override` if the directory is non-empty. |

Expected output: `progress.log`, plus `<basename(image)>/results.json` and
optional image-output JPG files.

## `process-images-directory`

Purpose: process all recognized images in a directory.

Default aggregate CSV command:

```bash
inference workflows process-images-directory \
  --input_directory ./images \
  --output_dir ./out \
  --processing_target api \
  --workspace_name my-workspace \
  --workflow_id detector \
  --model_id yolov8n-640
```

JSONL aggregate with bounded failures:

```bash
inference workflows process-images-directory \
  --input_directory ./images \
  --output_dir ./out \
  --processing_target api \
  --api_url http://localhost:9001 \
  --workspace_name my-workspace \
  --workflow_id detector \
  --aggregation_format jsonl \
  --threads 4 \
  --max-failures 3
```

Command-specific options:

| Option | Default | Notes |
| --- | --- | --- |
| `--input_directory`, `-i` | required | Directory containing images. Recognized common image extensions are selected. |
| `--output_dir`, `-o` | required | Output directory. Must be empty unless `--allow_override` is used. |
| `--processing_target`, `-pt` | `api` | `api` or `inference_package`. |
| `--api_url` | `https://detect.roboflow.com` | API endpoint used only for `--processing_target api`. |
| `--save_image_outputs` / `--no_save_image_outputs` | save | Controls per-image JPG outputs. |
| `--force_reprocessing` / `--no_reprocessing` | no reprocessing | Reprocess files already recorded in `progress.log`; use with `--allow_override` for resumed directories. |
| `--aggregate` / `--no_aggregate` | aggregate | Whether to write one aggregate structured-results file after processing. |
| `--aggregation_format`, `-af` | `csv` | `csv` creates `aggregated_results.csv`; `jsonl` creates `aggregated_results.jsonl`. |
| `--threads` | target-dependent | API request threads. Hosted API defaults to 32; non-hosted API defaults to 1. Not the local Workflow-step concurrency setting. |
| `--max-failures` | unlimited | Stop after this many failed Workflow executions and mark the rest as aborted. |

Expected output: `progress.log`, one subdirectory per processed image containing
`results.json` and optional JPG outputs, an aggregate file unless disabled, and a
timestamped failure JSONL if failures occurred.

## `process-video`

Purpose: process one video file through a Workflow with the local video pipeline.

CSV results with preview video outputs:

```bash
inference workflows process-video \
  --video_path ./input.mp4 \
  --output_dir ./video-out \
  --workspace_name my-workspace \
  --workflow_id detector \
  --model_id yolov8n-640 \
  --max_fps 1.0
```

JSONL results without preview MP4 outputs:

```bash
inference workflows process-video \
  --video_path ./input.mp4 \
  --output_dir ./video-out \
  --workflow_spec ./workflow.json \
  --workflow_params ./params.json \
  --output_file_type jsonl \
  --no_save_out_video
```

Command-specific options:

| Option | Default | Notes |
| --- | --- | --- |
| `--video_path`, `-v` | required | Path to the video file to process. |
| `--output_dir`, `-o` | required | Output directory. Existing files are refused unless `--allow_override` is used. |
| `--output_file_type`, `-ft` | `csv` | Structured result file type: `csv` or `jsonl`. |
| `--max_fps` | unset | Drop/skip frames above this processing rate. Lower values reduce rows and preview frames. |
| `--save_out_video` / `--no_save_out_video` | save | Controls preview MP4 outputs for image-valued Workflow fields. |

There is no `--processing_target`, `--api_url`, `--threads`, `--aggregate`, or
`--max-failures` option for `process-video`.

Expected output: `workflow_results_source_0.csv` or `.jsonl`, and when preview
saving is enabled, files named `source_0_output_<field>_preview.mp4`.

## Option name pitfalls

- The commands use underscores in most long option names (`--output_dir`,
  `--workflow_id`, `--max_fps`) but `--max-failures` uses a hyphen.
- Boolean negations are command-specific: `--no_save_image_outputs`,
  `--no_save_out_video`, `--no_aggregate`, and `--no_reprocessing`.
- `--allow_override` bypasses the output-directory preflight but does not delete
  stale files. Clean the directory yourself if you need a fresh result.
- `--aggregation_format` is for image-directory aggregation. `--output_file_type`
  is for video structured results.
