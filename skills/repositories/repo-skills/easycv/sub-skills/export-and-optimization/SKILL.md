---
name: export-and-optimization
description: "Routes EasyCV export, pruning, quantization, TorchAccelerator, and
  inference-optimization workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Export and optimization

Use this sub-skill when the task is to package, speed up, compress, prune, or otherwise optimize an EasyCV checkpoint for inference.

It covers the export front door, the compression utilities, and the advanced backend-dependent optimization paths.

## Read these references first

- `references/export.md` for raw / JIT / Blade / ONNX export behavior and artifact naming.
- `references/optimization.md` for pruning, quantization, TorchAccelerator, and analysis helpers.
- `references/troubleshooting.md` for missing extras, backend mismatches, and export-format issues.
- Root `references/cli-reference.md` for the installed-package command front doors.

## What belongs here

Include tasks such as:

- exporting a checkpoint for inference consumption
- choosing raw, JIT, Blade, or ONNX export behavior
- keeping preprocess / postprocess sidecars together with the exported model
- pruning or quantizing a YOLOX-style model
- using TorchAccelerator-specific configs or runtime notes
- checking FLOPs, parameters, or inference time with the repo analysis helpers

## What stays elsewhere

- Training or finetuning the source checkpoint -> `sub-skills/training-and-evaluation/`
- Running the exported artifact on files or tables -> `sub-skills/prediction-and-inference/`
- Dataset layout and conversion helpers -> `sub-skills/data-preparation/`

## Typical decision flow

1. Decide whether the model should stay raw or be exported for inference.
2. Check whether the target environment has the backend package for the chosen optimization path.
3. Choose the export format and any preprocess / postprocess wrapping.
4. Keep the exported sidecar files together.
5. For pruning or quantization, confirm the extra dependency stack before you start.

## Common success signals

- The export command writes the expected model file and sidecars.
- The exported artifact reloads with the corresponding predictor class.
- Optional optimization dependencies are installed only for the paths that need them.
- The output format matches the predictor path that will consume it later.

## Common optimization surfaces

- `blade_compression` and `pai_nni` are optional extras for advanced compression flows.
- `onnxruntime` is needed for ONNX consumption paths.
- `torchacc` requires the documented CUDA runtime and container path.
- Exported JIT / Blade models may need a matching `test_pipeline` or preprocess artifact.

