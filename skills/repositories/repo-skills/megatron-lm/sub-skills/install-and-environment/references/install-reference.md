# Megatron-LM install and environment reference

## Package identity

- Distribution name: `megatron-core`.
- Primary imports: `megatron.core` and `megatron.training`.
- Current metadata: Python `>=3.12`; base dependencies `torch>=2.6.0`, `numpy`, `packaging>=24.2`.
- Dynamic version comes from `megatron.core.package_info` and may include a VCS suffix when installed from a checkout.

## Choose an install mode

| Situation | Recommended path | Notes |
|---|---|---|
| Package-user import or API inspection | `uv pip install megatron-core` or editable source install | Verify with `python -c "import megatron.core as m; print(m.__version__)"`. |
| Training scripts with tokenizers and HF helpers | install `megatron-core[training]` or source equivalent | Adds packages such as `sentencepiece`, `tiktoken`, `transformers`, `accelerate`, and `omegaconf`. |
| Full development or CI parity | NGC/PyTorch container plus repo `uv` workflow | This avoids fragile host builds for CUDA extension packages. |
| TransformerEngine-specific kernels | install the repo-supported TE variant or use a container that already ships it | Match Torch/CUDA ABI; do not mix arbitrary TE wheels with a different Torch build. |
| ModelOpt / post-training examples | use the dev/container path that includes `nvidia-modelopt[torch]` | Treat ModelOpt as optional until the workflow requires it. |
| Mamba/SSM examples | install the `ssm` dependencies only when those examples are selected | Source builds may require CUDA toolkit/compiler compatibility. |

## Source install patterns

For a lightweight source install:

```bash
uv pip install -e .
```

For training dependencies:

```bash
uv pip install -e ".[training]"
```

For broad development, prefer the project container and the repository's `uv` workflow rather than installing every optional dependency on the host. Full development can pull in CUDA extension builds, TransformerEngine, ModelOpt, Mamba, FlashMLA, DeepGEMM, and other packages that are sensitive to Torch/CUDA/Python ABI.

## Container guidance

Megatron-LM development and CI assume NVIDIA CUDA, NCCL, PyTorch, and optional compiled kernels. The repo's container guidance distinguishes:

- `dev`: the default, latest CI path for ordinary development.
- `lts`: older long-term-support path; use only when explicitly requested.

For local/public Docker builds of the dev image, stop before internal-only stages and pass the public stage target. If the user is doing dependency work, route to [../../testing-ci-and-maintenance/SKILL.md](../../testing-ci-and-maintenance/SKILL.md) for `uv.lock`, CI labels, and base-image pin rules.

## CUDA and Torch checks

Run a backend check before claiming CUDA readiness:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
PY
```

Interpretation:

- `torch.cuda.is_available() == False` with visible GPUs usually means CPU-only Torch, missing container GPU passthrough, driver/wheel mismatch, or hidden devices.
- A successful CPU import does not validate NCCL, distributed training, FP8, TransformerEngine kernels, or inference CUDA graphs.
- A driver-reported CUDA version is the maximum runtime the driver supports; it is not proof that `nvcc` or matching source-build tooling is installed.

## Optional dependency groups

| Group/surface | Use when | Common risk |
|---|---|---|
| `training` | Pretrain scripts need tokenizers/HF/config helpers. | Missing tokenizer files or external model access still fail at runtime. |
| `dev` | Full CI/dev parity and optional integrations. | Heavy CUDA deps and git-sourced packages. |
| `te` | TransformerEngine kernels, FP8/FP4, TE layer specs. | ABI mismatch with Torch/CUDA; source build time. |
| `ssm` | Mamba/SSM models. | CUDA extension builds and compiler/toolkit needs. |
| `test` dependency group | Running selected repo tests. | Many tests assume GPUs, a canonical shared-data mount, or CI containers. |
| `linting` dependency group | Formatting/linting a contribution. | Belongs to repo maintenance rather than package use. |

## Build-memory mitigation

Editable/source installs compile `megatron.core.datasets.helpers_cpp`; broad extras may compile additional CUDA extensions. If a build is killed or OOMs, retry with a smaller job count:

```bash
MAX_JOBS=4 uv pip install --no-build-isolation -e ".[training,dev]"
```

Use `--no-build-isolation` only when build evidence says the extension must see the already installed Torch/build tools.
