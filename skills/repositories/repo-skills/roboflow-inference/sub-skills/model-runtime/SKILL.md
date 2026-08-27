---
name: model-runtime
description: "Route inference-models users through AutoModel, backend selection,
  model/package negotiation, local packages, environment inspection, and runtime
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# model-runtime

Use this sub-skill when the user needs to inspect, install, select, or debug `inference-models` at runtime.

## Route here when

- Choosing a backend, quantization, batch size, or device for `AutoModel.from_pretrained(...)`.
- Inspecting available packages with `AutoModel.describe_model(...)` or `AutoModel.describe_model_package(...)`.
- Checking hardware and dependency availability with `AutoModel.describe_compute_environment()`.
- Loading a Roboflow model, a cached package, a local package directory, or a local checkpoint.
- Debugging backend extras, offline mode, cache reuse, package negotiation, or runtime load failures.
- Understanding when a package is rejected because of trust, device, batch size, quantization, or model-feature constraints.

## Do not handle here

- CLI command surfaces, server lifecycle, or workflow CLI commands.
- WebRTC streaming or any task whose primary surface is a model-id stream.
- Training, export, or repository-maintenance work.

## Read order

1. Read `references/api-reference.md` for the public API and load flow.
2. Read `references/backends.md` for installation and backend-selection guidance.
3. Read `references/troubleshooting.md` when the user reports a failure.
4. Use `scripts/describe_compute_environment.py` for a deterministic environment probe when the runtime is unclear.

## Operating rules

- Start with `AutoModel.describe_compute_environment()` or the bundled probe whenever the user asks what this machine can run.
- Prefer `AutoModel.describe_model(model_id)` before forcing `backend`, `quantization`, `batch_size`, or `model_package_id`.
- Prefer `AutoModel.describe_model_package(model_id, package_id)` before forcing a specific package or diagnosing a mismatch.
- Treat `AutoModel.from_pretrained(...)` as the primary entry point.
- Use `weights_provider="local"` only for local directories or checkpoint files.
- Treat a path-like `model_id_or_path` as local storage only when the user actually intends a local load.
- Keep `allow_local_code_packages=True` only for trusted custom packages that ship `model_module` and `model_class`.
- Keep `allow_untrusted_packages=False` unless the user explicitly accepts the trust trade-off.
- For checkpoint files, require `model_type` and a supported `task_type` / `backend` combination.
- Keep `allow_loading_dependency_models=True` unless the user intentionally wants to block nested dependency loads.
- When negotiation fails, report the rejected constraints, installed extras, and runtime facts rather than guessing.

## Current selection stance

- Current package ranking priority in the code path is: `trt` > `onnx` > `torch` > `hugging-face` > `torch-script` > `ultralytics` > `custom`.
- Ranking still depends on trust, batch size, quantization, runtime/device compatibility, model features, and package metadata.
- If a user forces a backend, the loader still filters for compatibility before load.

## What this sub-skill should answer

- What backend or extra should I install for this model on this machine?
- Why did `AutoModel` choose a different package than I expected?
- How do I load a local package, a cached package, or a direct checkpoint safely?
- Which env vars or cache settings are relevant to this runtime failure?
