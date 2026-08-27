# Precision and Devices

Use this reference to choose Lightning `accelerator`, `devices`, and `precision` values and to state hardware limitations clearly.

## Accelerator Names

| Value | Meaning | Good for | Notes |
| --- | --- | --- | --- |
| `"auto"` | Let Lightning choose from available backends | Portable scripts and examples | Pair with `devices="auto"` when hardware varies. |
| `"cpu"` | CPU accelerator | Smoke tests, CI, CPU-only development | Multi-process CPU DDP can launch workers; do not use it for simple syntax checks. |
| `"gpu"` | Generic GPU selection | User wants any available GPU backend | On Apple systems this can select MPS; use `"cuda"` to require NVIDIA CUDA. |
| `"cuda"` | NVIDIA CUDA GPUs | Multi-GPU DDP/FSDP/DeepSpeed | Requires CUDA-visible PyTorch and hardware. |
| `"mps"` | Apple Metal Performance Shaders | Apple silicon local training | Feature/precision coverage differs from CUDA. |
| `"tpu"` or XLA paths | TPU/XLA accelerator | XLA/TPU environments | Requires XLA dependencies and TPU runtime setup. |

## `devices` Formats

Lightning accepts several forms for GPU devices:

```python
Trainer(accelerator="cuda", devices=1)        # first CUDA GPU
Trainer(accelerator="cuda", devices=4)        # first four CUDA GPUs
Trainer(accelerator="cuda", devices=[0, 2])   # explicit local GPU indices
Trainer(accelerator="cuda", devices="0,2")   # string form
Trainer(accelerator="cuda", devices=-1)       # all visible CUDA GPUs
Trainer(accelerator="cuda", devices="auto")  # Lightning-selected count
```

Guidelines:

- Respect `CUDA_VISIBLE_DEVICES`: indices are relative to visible devices, not necessarily physical PCI bus IDs.
- Avoid explicit GPU index lists on managed clusters unless the scheduler requires them; schedulers usually set visibility.
- `devices=N` means processes per node for distributed strategies; it must match launcher/scheduler task counts.
- For CPU, `devices=1` is a simple single-process baseline; `devices>1` with DDP means multiple CPU worker processes.

## Precision Modes

| Precision | CPU | CUDA GPU | TPU/XLA | Typical use |
| --- | --- | --- | --- | --- |
| `"32-true"` | Yes | Yes | Yes | Stable default and smoke tests. |
| `"64-true"` | Yes | Yes | No in standard docs table | Scientific/high-accuracy workloads; doubles memory. |
| `"16-mixed"` | Not a CPU target in docs table | Yes | No in standard docs table | Faster/lower-memory CUDA training with gradient scaling. |
| `"16-true"` | Hardware/backend dependent | Yes with stability caveats | XLA true half has dedicated plugin paths | Lower memory but more numerical risk. |
| `"bf16-mixed"` | Yes | Yes on supported GPUs | Yes | More stable than FP16; GPU speedups need Ampere-class or newer for best results. |
| `"bf16-true"` | Yes | Yes | XLA paths support true BF16 in tests | Lower-memory BF16 weights; check model/optimizer stability. |
| `"transformer-engine"` | No | Hopper-class NVIDIA GPUs | No | FP8-style training through NVIDIA Transformer Engine. |
| `"transformer-engine-float16"` | No | Hopper-class NVIDIA GPUs | No | FP8 with FP16 base weights. |

Prefer string precision values (`"16-mixed"`, `"bf16-mixed"`, `"32-true"`) in new examples. Legacy integer aliases such as `precision=16` or `precision=32` may exist but are less explicit.

## Mixed Precision Rules

- Do not wrap Lightning steps in manual `torch.autocast` or call `.half()` on tensors/models when Lightning precision plugins are active.
- Use `"16-mixed"` mainly on CUDA GPUs; it uses autocast plus gradient scaling.
- Use `"bf16-mixed"` when the user wants better numerical range or is on CPU/TPU/GPU hardware that supports BF16.
- If NaNs appear with `"16-true"`, check optimizer `eps` values such as Adam `eps=1e-8`, which can underflow in FP16; use a larger epsilon or switch to BF16/FP32.
- Keep numerically sensitive scatter/reduction/custom ops in FP32 if the model requires it.

## Precision Plugins and Optional Packages

Lightning exposes precision plugins for advanced workflows. Recommend them only when the task needs the specific feature and the optional dependency is installed.

- `BitsandbytesPrecision`: CUDA/Linux-oriented weight quantization for `torch.nn.Linear`; computation still happens in a chosen dtype. It does not automatically replace the optimizer with an 8-bit optimizer.
- `TransformerEnginePrecision`: NVIDIA Transformer Engine FP8-style workflows; requires Hopper-class GPUs and `transformer_engine`.
- `FSDPPrecision`: FSDP-specific mixed/true precision behavior.
- `DeepSpeedPrecision`: DeepSpeed handles precision through DeepSpeed-aware plugins/config.
- XLA precision plugins: TPU/XLA-specific; require XLA runtime and dependency setup.

When imports fail, provide install guidance but avoid claiming the local environment validated GPU behavior. This skill was created with CPU inspection evidence only.

## Device Visibility Checks

Use these before diagnosing Lightning code:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('cuda_count', torch.cuda.device_count())
print('mps_available', hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())
PY
```

For Lightning package visibility:

```bash
python - <<'PY'
import lightning as L
from lightning.pytorch import Trainer
print('lightning', L.__version__)
print(Trainer(accelerator='cpu', devices=1, strategy='auto', precision='32-true'))
PY
```

## CPU-Safe Fallback Pattern

When writing examples that must work on CPU and GPU, compute settings before constructing `Trainer`:

```python
import torch

if torch.cuda.is_available():
    accelerator = "cuda"
    devices = min(4, torch.cuda.device_count())
    precision = "16-mixed"
    strategy = "ddp" if devices > 1 else "auto"
else:
    accelerator = "cpu"
    devices = 1
    precision = "32-true"
    strategy = "auto"

trainer = L.Trainer(accelerator=accelerator, devices=devices, precision=precision, strategy=strategy)
```

Do not silently switch a user’s intended production configuration to CPU. Present fallback as a local smoke-test path and keep the production settings documented separately.
