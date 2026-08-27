---
name: workflow-processing
description: "Route Roboflow Inference workflow CLI commands for processing
  images, image directories, and videos, including parameter merging, output
  layout, aggregation, overwrite controls, rate limits, and API versus local
  execution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Workflow Processing

Use this sub-skill when a user wants to run Roboflow Workflows from the `inference`
CLI over a single image, an image directory, or a video file, or when they need to
understand the output files produced by those commands.

## Route here when

- The user mentions `inference workflows process-image`, `process-images-directory`,
  or `process-video`.
- They need to load a Workflow from `--workflow_spec` or from
  `--workspace_name` plus `--workflow_id` / `--workflow_version_id`.
- They need to pass Workflow parameters via `--workflow_params` and extra CLI
  arguments, choose `api` versus `inference_package`, or tune `--max_fps`,
  `--max-failures`, `--threads`, `--allow_override`, or `--force_reprocessing`.
- They ask what files to expect in an output directory, why aggregation is CSV or
  JSONL, or why a previous run was skipped or refused to overwrite output.

## Do not route here when

- The user is asking how to start, configure, or expose the Inference server.
  Use [CLI operations](../cli-operations/SKILL.md) instead.
- The user is asking for Python `InferenceHTTPClient`, HTTP request/response
  shapes, WebRTC streams, or long-running pipeline API calls. Use
  [SDK and WebRTC](../sdk-webrtc/SKILL.md) instead.
- The user is asking about model backend/package selection outside Workflow CLI
  execution; keep that with the model-runtime sub-skill when available.

## First decisions to make

1. **Input kind**: one image, an image directory, or one video file.
2. **Workflow source**: either a local JSON Workflow specification via
   `--workflow_spec`, or a Roboflow-hosted Workflow via `--workspace_name` and
   `--workflow_id` with optional `--workflow_version_id`. Do not tell users to
   supply both sources for the same run.
3. **Processing target**:
   - Image and directory commands default to `--processing_target api` and can
     also run through `--processing_target inference_package`.
   - Video processing has no `--processing_target`; it always requires the local
     `inference` package because it uses the local video pipeline.
4. **Output safety**: choose a clean `--output_dir` unless the user explicitly
   wants to reuse or merge into prior outputs with `--allow_override`.
5. **Parameters**: combine `--workflow_params params.json` with trailing Workflow
   parameters only when needed; trailing CLI parameters override matching file
   keys.
6. **Result format**: use directory `--aggregation_format csv|jsonl` for
   `process-images-directory`; use video `--output_file_type csv|jsonl` for
   `process-video`.

## Read these bundled references

- [Workflow command patterns and output behavior](references/workflows.md) for
  command recipes, parameter merging, output layout, aggregation, target choice,
  and resume/overwrite behavior.
- [CLI reference](references/cli-reference.md) for the workflow command family
  and option-level routing.
- [Troubleshooting](references/troubleshooting.md) for non-empty directories,
  invalid JSON paths, missing local packages, target confusion, `--max_fps`,
  `--max-failures`, aggregation format surprises, and debug-mode advice.

A small optional helper is bundled at
[`scripts/inspect_workflow_outputs.py`](scripts/inspect_workflow_outputs.py). Use it
only to validate JSON config files or inspect an already-produced output
folder; it is not a replacement for the Roboflow CLI.

A separate helper,
[`scripts/provision_workflow_fonts.py`](scripts/provision_workflow_fonts.py),
provisions the approved workflow font assets when a workflow visualization path
needs the bundled font set outside the original repository checkout.

## Answer pattern

When responding to a workflow-processing request, provide:

1. The exact `inference workflows ...` command for the input kind.
2. The Workflow source choice (`--workflow_spec` or hosted identifiers).
3. The processing target and any package/API preconditions.
4. The expected output layout and which files are safe to consume downstream.
5. The overwrite/resume/rate/failure controls that matter for the user's run.
6. A troubleshooting branch, with `--debug_mode` only when a stack trace is useful.
