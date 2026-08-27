# AIMET install and build guide

Use this reference for package installation, source builds, dependency variants, and safe validation. The commands are distilled from AIMET's install docs, package metadata, dependency tree, and build scripts.

## Package map

| Distribution | Import module | Primary use |
| --- | --- | --- |
| `aimet-torch` | `aimet_torch` | PyTorch QuantSim, model preparation, QAT, PTQ utilities, compression, Torch export helpers. |
| `aimet-onnx` | `aimet_onnx` | ONNX QuantSim, ONNX Runtime sessions/providers, graph passes, QDQ/export, ONNX PTQ utilities. |
| `aimet_common` | deprecated alias | Avoid for new code. It aliases either Torch or ONNX common modules and raises when both packages make the alias ambiguous. |

AIMET requires Python `>=3.10`. The source tree uses CMake/scikit-build for compiled components and exposes `ENABLE_TORCH`, `ENABLE_ONNX`, and `ENABLE_CUDA` build switches.

## PyPI install path

Use the PyPI path when the user needs AIMET as a library and does not need source changes:

```bash
python -m pip install --upgrade pip
python -m pip install aimet-torch aimet-onnx
python -m pip check
python scripts/quick_smoke.py --framework both
```

For ONNX Runtime CUDA execution, add the GPU provider package that matches the environment:

```bash
python -m pip install onnxruntime-gpu
python scripts/quick_smoke.py --framework onnx --onnx-cuda
```

If package resolution becomes unstable, prefer a clean Python 3.10/3.11 environment over repairing a broad shared environment.

## Source build path

Use the source path when the user is editing the AIMET checkout or needs a build variant. Run inside a dedicated environment with CMake, compilers, and package build tools available.

```bash
python -m pip install "scikit-build-core[wheels]==0.11.1" build pybind11 "cython>=3.0"
CMAKE_ARGS="-DENABLE_CUDA=OFF -DENABLE_TORCH=ON -DENABLE_ONNX=OFF" \
  python -m pip install --no-build-isolation -e .
python -m pip check
python scripts/quick_smoke.py --framework torch
```

Variant examples:

| Desired variant | CMake args |
| --- | --- |
| Torch CPU | `-DENABLE_CUDA=OFF -DENABLE_TORCH=ON -DENABLE_ONNX=OFF` |
| ONNX CPU | `-DENABLE_CUDA=OFF -DENABLE_TORCH=OFF -DENABLE_ONNX=ON` |
| Torch + ONNX CPU | `-DENABLE_CUDA=OFF -DENABLE_TORCH=ON -DENABLE_ONNX=ON` |
| Torch CUDA | `-DENABLE_CUDA=ON -DENABLE_TORCH=ON -DENABLE_ONNX=OFF` |
| ONNX CUDA | `-DENABLE_CUDA=ON -DENABLE_TORCH=OFF -DENABLE_ONNX=ON` |
| Torch + ONNX CUDA | `-DENABLE_CUDA=ON -DENABLE_TORCH=ON -DENABLE_ONNX=ON` |

The bundled `scripts/build_from_source.sh` applies these switches, refuses CUDA builds when `nvcc` is absent unless the user overrides the plan, and can run the bundled smoke check after install.

## Dependency-file orientation

The repository's dependency tree separates runtime and test inputs by backend family:

- `packaging/dependencies/torch-cpu/` and `torch-gpu/` for Torch-only builds.
- `packaging/dependencies/onnx-cpu/` and `onnx-gpu/` for ONNX-only builds.
- `packaging/dependencies/onnx-torch-cpu/` for combined CPU-style development.
- `packaging/dependencies/fast-release/*` for release-oriented wheel dependency sets.
- `packaging/dependencies/reqs_pip_test*.txt` for focused test dependencies.

Do not install every dependency file by default. Choose the smallest set that matches the selected package and backend.

## GenAILab environment setup

GenAILab local and pod runs require more than the base AIMET package: Hugging Face `transformers`/`datasets`, GenAILab requirements, optional `qai_hub_models`, and usually a CUDA-capable Torch stack. In a pod or dedicated environment, the source repo provides `scripts/environment/setup_genai.sh`, but treat it as a mutating bootstrap script because it installs system packages, creates `.venv`, installs PyTorch CUDA wheels, installs GenAILab requirements, optionally installs AWS CLI, and logs in to Hugging Face when `HF_TOKEN` is set.

Safer planning sequence:

```bash
python scripts/genai_config_preflight.py config.yaml --framework torch --print-command
# In a dedicated AIMET checkout/pod, after user approval:
bash scripts/environment/setup_genai.sh --repo-dir /scratch/aimet --skip-aimet
# Then install/build AIMET wheels or run the source build wrapper as appropriate.
```

Do not run `setup_genai.sh` in a shared base environment. For online runs, prefer `python -m GenAILab --online` only after `gh auth status` passes and the intended code is pushed.

## Focused repository checks

For package-use tasks, prefer the bundled smoke script. For GenAILab configs, prefer the bundled static preflight before model downloads. For maintainer tasks inside an AIMET checkout, run the smallest native test that exercises the changed surface; examples below are source-checkout commands, not generic runtime requirements:

```bash
python -m pytest TrainingExtensions/torch/test/python/v2/quantsim/test_quantsim.py::TestQuantsim::test_invalid_bw_instantiation -v
python -m pytest TrainingExtensions/onnx/test/python/test_quantsim.py::TestQuantSim::test_insert_quantize_op_nodes -v
python -m pytest TrainingExtensions/onnx/test/python/test_seq_mse.py -k "single" -v
python -m pytest TrainingExtensions/torch/test/python -m "not cuda" -v
```

Run CUDA-marked tests only when the task specifically needs CUDA behavior and a CUDA-capable AIMET/Torch/ONNX Runtime environment has been verified.
