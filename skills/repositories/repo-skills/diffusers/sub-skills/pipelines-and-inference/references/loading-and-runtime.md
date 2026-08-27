# Loading and Runtime Decisions

Use this reference when writing code that loads a Diffusers pipeline, chooses local/offline behavior, places components on devices, selects dtype, configures offload/memory options, or makes generation reproducible.

## Loading APIs

Installed package inspection confirms these public entry points:

- `DiffusionPipeline.from_pretrained(pretrained_model_name_or_path, **kwargs)`
- `AutoPipelineForText2Image.from_pretrained(pretrained_model_or_path, **kwargs)`

Diffusers also exposes task-specific auto pipelines such as image-to-image and inpainting variants, plus model-specific classes. Prefer task-specific classes when the workflow is known because their call signatures make expected inputs clearer.

Common `from_pretrained` keyword choices:

| Keyword | Use when | Caution |
| --- | --- | --- |
| `torch_dtype=torch.float16` | CUDA inference on models that support fp16 | Do not use fp16 on CPU. |
| `torch_dtype=torch.bfloat16` | CUDA/modern accelerator inference where bf16 is supported | MPS and older GPUs may not support all bf16 ops. |
| `local_files_only=True` | Offline, air-gapped, CI, or local snapshot-only workflows | Requires the full model snapshot/components to already exist locally. |
| `variant="fp16"` | Loading repos that publish fp16 variant files | The variant must exist in the model repo/local snapshot. |
| `use_safetensors=True` | Prefer safetensors checkpoints where available | Fails if the repo only has another format. |
| `device_map="auto"` or `"balanced"` | Large models or multi-device placement through Accelerate | Requires Accelerate and should not be followed blindly by `.to("cuda")`. |
| `revision=...` | Pinning a model revision | Useful for reproducibility; verify the revision exists offline before `local_files_only`. |

## Device and Dtype Matrix

| Runtime | Recommended baseline | Avoid |
| --- | --- | --- |
| CPU | Load with default dtype or `torch.float32`; do not pass CUDA-only placement | `torch.float16` CPU inference, CUDA generators, xFormers-only options. |
| CUDA | `torch.float16` or `torch.bfloat16`; `.to("cuda")` or `device_map="cuda"` | CPU generators are OK for reproducibility; tensor inputs must still land on compatible devices. |
| Multi-GPU / limited VRAM | `device_map="auto"` or `"balanced"`; inspect `pipeline.hf_device_map` | Moving the whole pipeline after device-map loading unless intentionally resetting. |
| MPS | Load then `.to("mps")`; consider attention slicing for memory pressure | Unsupported dtypes/ops; run a small warmup when comparing determinism. |
| HPU/special accelerators | Use the accelerator's `.to("hpu")`/library-specific path | Assuming CUDA-only optimization flags exist. |

Default helper:

```python
import torch

def choose_device_and_dtype(prefer_cuda=True):
    if prefer_cuda and torch.cuda.is_available():
        return "cuda", torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32
```

## Placement Patterns

### Whole-pipeline placement

```python
pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype, local_files_only=True)
pipe = pipe.to(device)
```

Use this for single-device CPU/CUDA/MPS scripts.

### Accelerate device map

```python
pipe = DiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto",
    local_files_only=True,
)
print(pipe.hf_device_map)
```

Use this for large models or multi-GPU placement. Let Accelerate place components and inspect `hf_device_map` when debugging.

### CPU offload

```python
pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe.enable_model_cpu_offload()
```

Rules:

- Enable offload after loading all components/adapters that should participate in offload.
- `enable_model_cpu_offload()` trades speed for lower peak GPU memory.
- `enable_sequential_cpu_offload()` can reduce memory further and is slower.
- If using IP-Adapter or other image encoders, load those adapters before enabling model CPU offload; otherwise image-encoder placement can be wrong.

## Memory and Speed Levers

Use only the levers supported by the installed optional dependencies and hardware.

| Lever | Typical call | When useful |
| --- | --- | --- |
| Attention slicing | `pipe.enable_attention_slicing()` | MPS or low-memory single-device runs. |
| VAE slicing/tiling | `pipe.vae.enable_slicing()` / `pipe.vae.enable_tiling()` when present | Large images or video frames. |
| CPU offload | `pipe.enable_model_cpu_offload()` | CUDA VRAM pressure. |
| Sequential offload | `pipe.enable_sequential_cpu_offload()` | Severe VRAM pressure, slower generation. |
| Attention backend | `model.set_attention_backend(...)` when available | Advanced speed/memory tuning; verify backend package/hardware. |
| `torch.compile` | compile selected modules after loading | Stable deployment shapes; first run may be slow. |

Do not add xFormers, FlashAttention, CacheDiT, OpenVINO, Neuron, Core ML, or other optional optimizations unless the user asks for that backend and the environment supports it.

## Reproducibility and Generators

Diffusers pipelines use PyTorch generators for sampling. For stable cross-device behavior, prefer CPU generators.

```python
generator = torch.Generator(device="cpu").manual_seed(0)
image = pipe(prompt, generator=generator).images[0]
```

Rules:

- A generator is stateful. Reusing the same generator object for multiple calls advances the state and changes later outputs.
- For repeated identical outputs, recreate or reseed a fresh generator before each call.
- For batches, create one generator object per batch item:

```python
generators = [torch.Generator(device="cpu").manual_seed(seed) for seed in range(batch_size)]
images = pipe(prompts, generator=generators).images
```

- Do not use list multiplication for generators.
- Deterministic algorithms can reduce nondeterminism but may affect speed and backend support.

## Offline and Local-Only Skeleton

```python
from pathlib import Path
import torch
from diffusers import DiffusionPipeline

model_path = Path("/models/local-snapshot")
if not model_path.exists():
    raise FileNotFoundError(f"local model path does not exist: {model_path}")

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
pipe = DiffusionPipeline.from_pretrained(
    str(model_path),
    torch_dtype=dtype,
    local_files_only=True,
    use_safetensors=True,
)
pipe = pipe.to(device)
```

For public skill content, keep placeholders generic and do not include machine-specific paths.

## Output Handling

Most image pipelines return a dataclass-like output with an `images` field.

```python
result = pipe(prompt="a cat")
first_image = result.images[0]
```

If `return_dict=False`, the first tuple element is usually the images collection:

```python
images = pipe(prompt="a cat", return_dict=False)[0]
```

Use `output_type="np"`, `"pil"`, `"pt"`, or `"latent"` only when the concrete pipeline supports it. Callbacks that inspect latent tensors often set `output_type="latent"` in tests.
