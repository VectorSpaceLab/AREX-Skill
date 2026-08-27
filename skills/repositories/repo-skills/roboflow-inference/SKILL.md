---
name: roboflow-inference
description: "Route Roboflow Inference users through CLI operations, SDK/WebRTC,
  workflow processing, and model runtime selection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Roboflow Inference

Use this skill when the task is about Roboflow Inference's public runtime
surfaces: the `inference` CLI and server, `inference_sdk`, workflow image/video
processing, or `inference-models` runtime selection.

This skill is self-contained. Use the bundled references and scripts in this tree
instead of reopening the source repository once the route is clear.

## Start here

1. Identify the user-facing surface the request names.
2. Open the matching sub-skill.
3. If the problem is installation or a predictable failure mode, open the
   cross-cutting references first.

## Route map

- [`sub-skills/cli-operations/SKILL.md`](sub-skills/cli-operations/SKILL.md)
  - Server lifecycle, `infer`, benchmarks, cloud deploy, Roboflow Cloud staging,
    batch processing, and enterprise compilation.
  - Also covers the experimental `benchmark inference-models-speed` path, but
    backend/package-choice questions still belong in `model-runtime`.
- [`sub-skills/sdk-webrtc/SKILL.md`](sub-skills/sdk-webrtc/SKILL.md)
  - `InferenceHTTPClient`, workflow and pipeline HTTP APIs, and WebRTC
    streaming with webcam, video file, RTSP, MJPEG, local stream, or manual
    sources.
- [`sub-skills/workflow-processing/SKILL.md`](sub-skills/workflow-processing/SKILL.md)
  - `inference workflows process-image`, `process-images-directory`, and
    `process-video`, including parameter files, output layout, and overwrite
    controls.
- [`sub-skills/model-runtime/SKILL.md`](sub-skills/model-runtime/SKILL.md)
  - `AutoModel`, backend selection, local packages, cache/offline behavior,
    environment inspection, and runtime load failures.

## Package family map

- `inference` / `inference-cli` → CLI, server, cloud, rf-cloud, and workflow
  command families.
- `inference-sdk` → HTTP client and WebRTC streaming.
- `inference-models` → model loading, backend negotiation, and package/runtime
  inspection.

If the user asks about a surface that spans more than one family, start from the
family that owns the user-facing command or API, then hand off to the neighbor
sub-skill for shared troubleshooting or backend selection.

## Common request cues

Use the owning sub-skill by the exact surface the user mentions:

- `inference server start|status|stop` → cli-operations
- `inference infer` → cli-operations
- `inference benchmark api-speed` or `python-package-speed` → cli-operations
- `inference cloud ...`, `rf-cloud ...`, `enterprise inference-compiler ...` → cli-operations
- `inference workflows process-*` → workflow-processing
- `InferenceHTTPClient`, `run_workflow`, `start_inference_pipeline_with_workflow`,
  `client.webrtc.stream(...)` → sdk-webrtc
- `AutoModel.from_pretrained(...)`, `describe_compute_environment()`, backend
  extras, local packages, cache/offline mode → model-runtime

## Read these next

- [Overview](references/overview.md) for the high-level surface map.
- [Installation](references/installation.md) when a package is missing or the
  environment needs to be prepared.
- [Troubleshooting](references/troubleshooting.md) when a command, stream, or
  model load fails.
- [Repository provenance](references/repo-provenance.md) when you need the
  source snapshot for staleness checks.
- [Router metadata](references/repo-routing-metadata.json) when a machine-readable
  import or routing record is needed.

## Helpful probe scripts

- [`sub-skills/cli-operations/scripts/inspect_cli_help.py`](sub-skills/cli-operations/scripts/inspect_cli_help.py)
- [`sub-skills/sdk-webrtc/scripts/check_webrtc_surface.py`](sub-skills/sdk-webrtc/scripts/check_webrtc_surface.py)
- [`sub-skills/workflow-processing/scripts/inspect_workflow_outputs.py`](sub-skills/workflow-processing/scripts/inspect_workflow_outputs.py)
- [`sub-skills/model-runtime/scripts/describe_compute_environment.py`](sub-skills/model-runtime/scripts/describe_compute_environment.py)

Use the probe that matches the surface before reopening source files.

## When to switch sub-skills

- If the user is actually asking for workflow image/video processing, switch
  from CLI operations to workflow processing.
- If the user is choosing a backend, debugging cache/offline behavior, or
  loading a local package, switch to model runtime.
- If the user is trying to stream frames or configure the HTTP client, switch
  to SDK/WebRTC.
- If the user is trying to start the server, run cloud, rf-cloud, or enterprise
  commands, stay in CLI operations.
