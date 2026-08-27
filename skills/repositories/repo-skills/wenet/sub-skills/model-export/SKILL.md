---
name: model-export
description: "Preflight and run WeNet checkpoint export to TorchScript, ONNX CPU
  or GPU, IPEX, Horizon BPU, and deployment-ready model artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Model Export

Use this sub-skill when the user has a trained WeNet checkpoint and wants
TorchScript/JIT, quantized JIT, ONNX, IPEX, Horizon BPU, or other deployment
artifacts.

## Start here

1. Confirm the experiment has a compatible `train.yaml` and checkpoint. If the
   user provides a model directory, preflight it first:

   ```bash
   python sub-skills/model-export/scripts/check_export_inputs.py \
     --model-dir exp/conformer --mode jit
   ```

2. Read [references/export-reference.md](references/export-reference.md) for
   export modes, command templates, required files, streaming chunk choices,
   output artifacts, and optional dependencies.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when
   files are missing, ONNX dependencies are absent, streaming parameters are
   inconsistent, CUDA providers are unavailable, quantized export fails, or a
   vendor toolchain is missing.

## Route by task

- Use [../training-and-decoding/SKILL.md](../training-and-decoding/SKILL.md)
  when the user still needs to train, average, or locate checkpoints.
- Use [../runtime-deployment/SKILL.md](../runtime-deployment/SKILL.md) after
  export to choose C++/mobile/web/server runtime targets.
- Use [../package-transcription/SKILL.md](../package-transcription/SKILL.md)
  when a local model directory is intended only for package `load_model()`.

## Key decisions

- JIT export is the common CPU-safe deployment artifact for the C++ libtorch
  runtime.
- ONNX CPU export creates separate encoder, CTC, and decoder graphs and checks
  them with ONNX Runtime CPU when dependencies are installed.
- ONNX GPU, TensorRT, IPEX, Horizon BPU, and vendor exports require matching
  optional packages and toolchains. Treat parser acceptance as weaker evidence
  than a completed export and runtime check.
- Streaming export must use chunk settings compatible with the intended runtime
  mode; non-streaming `-1/-1` export should not be reused as a streaming model.
