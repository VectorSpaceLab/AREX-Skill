---
name: export-and-speed
description: "Routes Ultra-Fast-Lane-Detection TorchScript export, synthetic
  speed checks, and deployment benchmarking workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# export-and-speed

Use this sub-skill when a task is about exporting a lane model for deployment, timing its throughput, or understanding the C++/LibTorch demo path.

## Read this when

- You need to export a checkpoint to TorchScript.
- You need a quick synthetic speed benchmark.
- You need to explain the C++/LibTorch deployment example.
- You need to reason about `cls_dim`, anchors, device choice, or half precision for export and timing.

## What this sub-skill owns

- TorchScript export commands and model input shape.
- Synthetic throughput timing.
- Deployment caveats for the C++ demo.
- Speed-related checkpoint, device, and dimension assumptions.

## What it does not own

- Training command construction: see `training`.
- Dataset layout and conversion: see `data-and-config`.
- Accuracy evaluation and demo metrics: see `evaluation-and-visualization`.

## Start here

- Read `references/export-workflows.md` for the export and benchmark flow.
- Read `references/speed-and-deployment.md` for the LibTorch/OpenCV notes and practical timing caveats.
- Read `references/api-reference.md` for the verified model signature and dimension assumptions.
- Read `references/troubleshooting.md` for hardcoded path, checkpoint, and device issues.
- Run `scripts/export_torchscript.py` when you need a portable TorchScript file.
- Run `scripts/benchmark_synthetic.py` when you need a configurable synthetic timing check.

## Typical flow

1. Decide whether the user wants a CPU or CUDA export/benchmark path.
2. Confirm the checkpoint file and model dimensions.
3. Export or benchmark using a helper that accepts explicit paths and device options.
4. If the user wants C++ deployment, read the deployment caveats before building anything.

## Caution points

- The source `export.py` has a hardcoded checkpoint path and CUDA map_location.
- The source speed scripts are demos, not robust command-line tools.
- The C++ example hardcodes LibTorch and OpenCV paths.
- `cls_dim` must match the chosen dataset family and backbone setup.

## Reference and script links

- `references/export-workflows.md` for export patterns and safe invocation advice.
- `references/speed-and-deployment.md` for deployment and benchmark caveats.
- `references/api-reference.md` for the verified signature notes.
- `references/troubleshooting.md` for export and timing failures.
- `scripts/export_torchscript.py` for a parameterized export helper.
- `scripts/benchmark_synthetic.py` for a configurable speed helper.
