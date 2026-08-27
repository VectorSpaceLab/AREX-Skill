---
name: "model-export"
description: "Routes Torchreid checkpoint export to ONNX, OpenVINO, and
  TFLite-style artifacts with explicit model-name, input-shape, and optional
  dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-export

Use this sub-skill when a Torchreid checkpoint must be packaged for deployment rather than trained or queried.

## Use this route for

- Exporting a Torchreid checkpoint to ONNX.
- Chaining ONNX into OpenVINO and TFLite-style artifacts.
- Choosing input height/width, opset, dynamic axes, or FP16 conversion settings.
- Resolving model-name selection before export.
- Checking optional export dependencies and known limitations.

## Do not use this route for

- Training a checkpoint first. Use `training-evaluation`.
- Feature extraction, embeddings, or model-key discovery only. Use `feature-extraction`.
- Project-specific model families that are not accepted by core `build_model`; those project workflows are excluded long-tail gaps in this generated skill.

## Read first

- [Export workflows](references/export-workflows.md)
- [Optional dependencies](references/optional-dependencies.md)
- [Troubleshooting](references/troubleshooting.md)
- [Bundled export helper](scripts/export_torchreid_model.py)

## Skill-owned script

- `scripts/export_torchreid_model.py` — argparse-driven helper with `--help` and `--dry-run`, explicit `--model-name`, `--weights`, `--imgsz`, `--include`, `--dynamic`, `--opset`, safe optional-dependency checks, and non-destructive defaults unless `--force` is supplied.

## Typical workflow

1. Confirm the checkpoint already exists and belongs to a core Torchreid model family.
2. Supply `--model-name` when the filename does not clearly identify the architecture.
3. Export ONNX first, then request OpenVINO and/or TFLite-style outputs only when the corresponding tools are installed.
4. Verify the generated artifact path and any dependency or shape warnings.

## Limits to keep explicit

- `--help` and `--dry-run` must stay safe and side-effect free.
- ONNX export can run on CPU when `onnx` is installed.
- OpenVINO and TFLite-style conversion remain optional and unverified unless their extra packages are present.
- Existing outputs should not be overwritten unless `--force` is supplied.
- Do not claim a successful deployment export unless the artifact was actually written.
