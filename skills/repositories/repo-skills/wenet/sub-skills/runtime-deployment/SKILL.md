---
name: runtime-deployment
description: "Choose and prepare WeNet runtime deployment paths for libtorch,
  ONNX Runtime, OpenVINO, mobile, web, GPU/Triton/TensorRT, IPEX, BPU, and XPU
  targets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Runtime Deployment

Use this sub-skill when the user wants to deploy a trained/exported WeNet model
outside ordinary Python package transcription: C++ libtorch, ONNX Runtime,
OpenVINO, Android, iOS, web demos, Raspberry Pi, GPU Triton/TensorRT, Intel
IPEX, Horizon BPU, or Kunlun XPU.

## Start here

1. Identify the target platform and inference engine.
2. If the model is not exported yet, route to
   [../model-export/SKILL.md](../model-export/SKILL.md).
3. Use the runtime chooser to list expected artifacts and prerequisites:

   ```bash
   python sub-skills/runtime-deployment/scripts/choose_runtime.py \
     --platform linux --backend libtorch
   ```

4. Read [references/runtime-platforms.md](references/runtime-platforms.md) for
   the platform matrix, U2 streaming concepts, artifact mapping, and deployment
   templates.
5. Read [references/troubleshooting.md](references/troubleshooting.md) for
   build/toolchain, artifact mismatch, streaming, service endpoint, GPU, mobile,
   and LM/context graph failures.

## Route by task

- Export JIT/ONNX/vendor artifacts with
  [../model-export/SKILL.md](../model-export/SKILL.md).
- Train or decode experiments with
  [../training-and-decoding/SKILL.md](../training-and-decoding/SKILL.md).
- Use simple installed-package transcription with
  [../package-transcription/SKILL.md](../package-transcription/SKILL.md).

## Safety boundary

Runtime builds can download SDKs, compile C++ code, start services, use GPUs,
or require mobile/vendor toolchains. Do not run builds or servers unless the
user authorizes platform-specific dependencies, hardware, network, ports,
storage, and runtime duration. The bundled chooser is safe and only reports
requirements.
