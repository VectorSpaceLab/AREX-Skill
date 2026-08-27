---
name: install-and-build
description: "Install, build, repair, and validate AIMET package environments
  and repository build/test workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET install and build

Use this sub-skill when the user asks to install AIMET, choose `aimet-torch` vs `aimet-onnx`, repair imports, select CPU/CUDA packages, build from source, package wheels, set up GenAILab dependencies, or run focused checks in an AIMET checkout.

## Read/run first

- Read [install and build](../../references/install-and-build.md) for package names, PyPI/source commands, build flags, and dependency-file orientation.
- Read [backend compatibility](../../references/backend-compatibility.md) when CUDA, ONNX Runtime providers, source CUDA builds, or target runtime claims matter.
- Read [troubleshooting](../../references/troubleshooting.md) for import, dependency, CMake, Torch/ONNX Runtime, and visualization failures.
- Run [quick_smoke.py](../../scripts/quick_smoke.py) after installation to verify imports and tiny Torch/ONNX QuantSim behavior.
- Use [build_from_source.sh](../../scripts/build_from_source.sh) only inside a dedicated environment when a source build is actually required.
- For GenAILab dependency setup, read [GenAILab workflows](../genai-lab/SKILL.md) and treat `scripts/environment/setup_genai.sh` as a mutating pod/dedicated-environment bootstrap script.

## Decision flow

1. **Confirm desired surface.** `aimet-torch`, `aimet-onnx`, or both; PyPI install versus editable/source build; CPU versus CUDA; repository maintenance versus package use.
2. **Choose an isolated environment.** Prefer Python 3.10 or 3.11 for compiled ML dependencies. Do not mutate Conda `base` or a broad user environment unless explicitly approved.
3. **Install the minimum variant.** Use PyPI for package use. Use `CMAKE_ARGS` source builds only when editing the checkout or validating build behavior.
4. **Run `pip check`.** Dependency conflicts usually explain AIMET import failures faster than source inspection.
5. **Run the bundled smoke.** A tiny QuantSim smoke is better than launching ImageNet or LLM examples while diagnosing install state.
6. **Escalate to native tests only for repo maintenance.** Pick the smallest source-checkout pytest target that covers the changed area; do not run all tests by default.

## Source build notes

AIMET's source build is controlled by three CMake switches:

- `ENABLE_TORCH=ON/OFF`
- `ENABLE_ONNX=ON/OFF`
- `ENABLE_CUDA=ON/OFF`

The default source documentation emphasizes CUDA-capable builds, but core package-use checks can be CPU-only. CUDA source builds need a development toolkit; CUDA runtime wheels alone are not proof that `nvcc` is available.

## Boundaries

- Route model quantization code to [torch-quantization](../torch-quantization/SKILL.md) or [onnx-quantization](../onnx-quantization/SKILL.md).
- Route accuracy loss, compression, mixed precision, and deployment artifact questions to [optimization-analysis-deployment](../optimization-analysis-deployment/SKILL.md).
- Route GenAILab/Hugging Face recipe automation to [genai-lab](../genai-lab/SKILL.md) and credential/download handling to [model-access-and-credentialed-evaluation](../model-access-and-credentialed-evaluation/SKILL.md); use this sub-skill only for the environment/package setup part.
- Do not install every requirements file or all optional extras unless the user explicitly asks for a broad dev/test environment.

## Good completion signals

- `python -m pip check` reports no broken requirements.
- `python scripts/quick_smoke.py --framework both` succeeds for the installed package set.
- CUDA claims include actual `torch.cuda` allocation or ONNX Runtime CUDA provider evidence.
- Source-build claims include the exact `CMAKE_ARGS`, Python version, build tools, and whether `nvcc` was present.
