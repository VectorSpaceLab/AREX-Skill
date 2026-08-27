# Install and backend reference

## Purpose

Read this before installing, inspecting, or debugging vLLM-Omni. The package extends vLLM with omni-modality inference and serving for text, image, audio, video, action, AR, diffusion, and TTS model families.

## Version alignment

vLLM-Omni releases are aligned to upstream vLLM major/minor releases. For the release line represented by this checkout, the public docs state that stable vLLM-Omni `0.26.x` expects upstream `vllm==0.26.x`.

If importing `vllm_omni` prints a warning like:

```text
vLLM and vLLM-Omni appear to have mismatched major/minor versions
```

then verify both packages from the same environment:

```bash
python - <<'PY'
from importlib.metadata import version
print('vllm', version('vllm'))
print('vllm-omni', version('vllm-omni'))
import vllm_omni, vllm
print('imports ok')
PY
```

A source checkout without release tags may produce a development version string even when the code is intended for an aligned release. Treat the warning as a gate to inspect before running models, not as proof that import failed.

## Python and base install

The docs emphasize Linux and Python 3.12 for current quickstarts. Use a fresh environment because vLLM, PyTorch, CUDA/ROCm libraries, attention kernels, and optional media packages can conflict with existing ML stacks.

CUDA quickstart pattern:

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm==0.26.0 --torch-backend=auto
uv pip install vllm-omni
```

Source checkout pattern:

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm==0.26.0 --torch-backend=auto
VLLM_OMNI_TARGET_DEVICE=cuda uv pip install -e .
```

ROCm users must install a matching upstream vLLM ROCm wheel/index before installing vLLM-Omni. NPU, XPU, and MUSA installs use vendor-specific requirements and images; do not mix those variants in one environment.

## Dynamic dependency routing

`setup.py` chooses requirements based on `VLLM_OMNI_TARGET_DEVICE` or detected Torch backend. Valid target values include:

- `cuda`
- `rocm`
- `npu`
- `xpu`
- `musa`
- `cpu`

Important behavior:

- If `VLLM_OMNI_TARGET_DEVICE` is set, it wins.
- If Torch is importable, setup checks CUDA, ROCm, NPU, XPU, and MUSA availability.
- If Torch is missing, setup defaults toward CUDA dependencies.
- ReadTheDocs builds use CPU requirements to avoid large GPU package downloads.

Use an explicit target in automation so a transient Torch install does not silently change dependency resolution:

```bash
VLLM_OMNI_TARGET_DEVICE=cuda pip install -e .
```

## Backend expectations

| Backend | Use when | Notes |
| --- | --- | --- |
| CUDA | NVIDIA GPU serving, most recipes, diffusion/TTS/omni examples. | vLLM 0.26 defaults to CUDA 13-compatible wheels. Verify `torch.cuda.is_available()` and a tiny allocation before running models. |
| ROCm | AMD GPU recipes or deployments. | Install the matching upstream vLLM ROCm build and avoid CUDA-only kernels. |
| NPU | Ascend deployments. | Use vendor docs/images and `VLLM_OMNI_TARGET_DEVICE=npu`. |
| XPU | Intel GPU deployments. | Use documented image/source route and verify vLLM platform detection. |
| MUSA | Moore Threads deployments. | Use `requirements/musa.txt` and vendor-compatible packages. |
| CPU | Parser/config/docs checks only. | CPU is not a full substitute for live model generation or serving throughput. |

## Minimal import/backend smoke

Use the bundled root checker first:

```bash
python scripts/check_environment.py --require-vllm 0.26 --require-cuda
```

It verifies distribution metadata, imports, and optional CUDA availability without loading model weights.

Manual equivalent:

```bash
python - <<'PY'
from importlib.metadata import version
print('vllm', version('vllm'))
print('vllm-omni', version('vllm-omni'))
import torch, vllm, vllm_omni
print('torch', torch.__version__, 'cuda', torch.version.cuda)
print('cuda available', torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device='cuda')
PY
```

## Extras and optional dependencies

Do not install all optional extras by default. Add only what the selected workflow needs:

- `demo`: Gradio/OpenCV/requests demo clients.
- `forced-aligner`: Qwen ASR forced aligner.
- `indextts2`, `longcat-video-avatar`, `soulx-svs`: model-specific optional dependencies.
- `quack`, `fa4`: Blackwell/CUDA-specific kernel packages.
- `dev`, `docs`, `local`: development, docs, and local test dependencies; skip for ordinary inference/serving.

## When not to run full examples

Most model examples require one or more of: large checkpoint downloads, gated model license acceptance, CUDA/ROCm/NPU/XPU/MUSA hardware, multiple GPUs, long warmup, or benchmark-scale runtime. Use no-network helpers and parser/config tests first, then run model examples only after prerequisites are explicit.
