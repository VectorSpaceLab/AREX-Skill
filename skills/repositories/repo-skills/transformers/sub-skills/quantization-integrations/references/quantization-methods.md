# Quantization Methods

Use this reference to choose a Transformers quantization method before writing code or installing packages. Always combine the method decision with [compatibility](compatibility.md), because the same API shape can fail on unsupported hardware or missing kernels.

## Decision Tree

1. **Need the easiest 4-bit or 8-bit PyTorch loading path on GPU:** start with `BitsAndBytesConfig`.
2. **Need CPU-only local inference with a llama.cpp-style artifact:** use GGUF/GGML if the model family and file format support it; do not force `bitsandbytes` as the CPU default.
3. **Need high-quality 4-bit pre-quantized LLM inference:** load an AWQ or GPTQ checkpoint and match the checkpoint's `quantization_config` metadata.
4. **Need to create a new calibrated quantized checkpoint:** use GPTQ or AWQ only when calibration data, tokenizer, backend package, and enough compute are available.
5. **Need `torch.compile`, PyTorch-native quantization, or CPU/XPU flexibility:** consider `TorchAoConfig`, but check torchao version and config-object API.
6. **Need FP8 or vendor-specific formats:** choose compressed-tensors, FBGEMM FP8, fine-grained FP8, Quark, or backend-specific methods only when the checkpoint and hardware match.
7. **Need extreme compression or research methods:** consider AQLM, SpQR, VPTQ, HIGGS, SINQ, HQQ, or FourOverSix after accepting accuracy and ecosystem risks.

## Core APIs

Most methods plug into model loading with `quantization_config`:

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_4bit=True)
model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=quantization_config,
    device_map="auto",
    dtype="auto",
)
```

Common config classes include:

- `BitsAndBytesConfig`: 4-bit and 8-bit on-the-fly quantization, QLoRA-oriented workflows, optional CPU offload for 8-bit.
- `GPTQConfig`: GPTQ/GPT-QModel calibration and loading; use `bits`, `dataset`, `tokenizer`, and optional backend settings such as Marlin when supported.
- `AwqConfig`: AWQ loading and fused module options such as `do_fuse=True` and `fuse_max_seq_len` for supported architectures.
- `TorchAoConfig`: wraps torchao `AOBaseConfig` objects, not removed string aliases; useful for int4/int8/float8 and compile-oriented paths.
- Method-specific configs: AQLM, HQQ, Quanto, Quark, VPTQ, EETQ, FP8, compressed-tensors, Metal, SINQ, and others appear through Transformers quantizer and integration modules when installed.

## Common Method Profiles

| Method | Best fit | Main constraints | PEFT/training | Serialization notes |
|---|---|---|---|---|
| `bitsandbytes` 4-bit | Easy memory reduction, QLoRA | Backend package plus supported accelerator/CPU build; speedup not guaranteed | Good for training extra adapter parameters | Recent Transformers/bitsandbytes needed for pushing quantized weights |
| `bitsandbytes` 8-bit | Halve memory, outlier handling, offload | `LLM.int8()` hardware constraints; offloaded weights remain fp32 on CPU | Extra parameters only | Quantization config saved before weights when pushing |
| GPTQ/GPT-QModel | Accurate calibrated 2/3/4/8-bit checkpoints | Calibration can be slow; package `gptqmodel`; kernels vary | Some PEFT support, checkpoint-specific | Move fully to CPU/GPU before saving when loaded with `device_map` |
| AWQ | High-quality 4-bit pre-quantized LLMs | `autoawq` may constrain Transformers versions; fused modules are architecture-specific | PEFT support depends on backend/checkpoint | Check `quant_method: awq` metadata |
| GGUF/GGML | CPU and llama.cpp-style local inference formats | Format/model support differs from PyTorch checkpoints; not a general `quantization_config` replacement | Not a QLoRA path | Serialization support differs from normal Transformers weights |
| torchao | PyTorch-native int/float quantization and compile paths | Requires compatible torchao, PyTorch, and hardware; first compile can be expensive | Supports some training/optimizer/FSDP2 patterns through torchao | Some schemes serializable, others experimental |
| HQQ/SINQ/Quanto | On-the-fly low-bit quantization without calibration | Accuracy and backend performance vary by bit width and kernel | Method-specific | Some methods intentionally do not serialize quantized weights |
| FP8/compressed-tensors/Quark | Pre-quantized or vendor FP8 workflows | Highly hardware/checkpoint specific | Method-specific | Match checkpoint metadata exactly |
| AQLM/SpQR/VPTQ/HIGGS | Research or extreme compression | More setup, longer quantization, higher accuracy risk | Often limited | Treat as specialized checkpoint formats |

## Bitsandbytes Patterns

4-bit inference or QLoRA base model:

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
)
model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=quantization_config,
    device_map="auto",
    dtype="auto",
)
```

8-bit with explicit CPU offload risk:

```python
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_enable_fp32_cpu_offload=True,
)
```

If offloading is enabled, explain that CPU-dispatched weights are stored in fp32 and memory savings apply primarily to modules kept on the quantized backend.

## GPTQ Pattern

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, GPTQConfig

tokenizer = AutoTokenizer.from_pretrained("org/base-model")
quantization_config = GPTQConfig(bits=4, dataset="c4", tokenizer=tokenizer)
model = AutoModelForCausalLM.from_pretrained(
    "org/base-model",
    quantization_config=quantization_config,
    device_map="auto",
)
```

Use a list of calibration strings for a private or tiny calibration smoke, but warn that representative calibration data is required for quality. For existing GPTQ checkpoints, first try loading the checkpoint metadata without overriding the config; override only when the backend or kernel is intentional.

## AWQ Pattern

```python
from transformers import AutoModelForCausalLM, AwqConfig

quantization_config = AwqConfig(bits=4, do_fuse=True, fuse_max_seq_len=512)
model = AutoModelForCausalLM.from_pretrained(
    "org/awq-checkpoint",
    quantization_config=quantization_config,
    device_map="auto",
    dtype="auto",
)
```

Fused AWQ modules can improve speed for supported architectures, but they can conflict with other optimizations such as FlashAttention-style attention replacement. If the checkpoint already has AWQ metadata, do not invent a new `AwqConfig` unless a specific fuse or kernel option is required.

## GGUF/GGML Pattern

Use GGUF when the artifact itself is a GGUF file and the desired runtime is CPU-friendly or llama.cpp-compatible. Do not present GGUF as equivalent to loading a regular PyTorch checkpoint with `BitsAndBytesConfig`. Validate:

- The user has a GGUF file or Hub repository containing one.
- The model family is supported by the GGUF integration.
- The tokenizer and special tokens are compatible with the converted artifact.
- The target deployment can accept GGUF limitations around generation, adapters, and serialization.

## Method Selection Signals

Choose `bitsandbytes` when the user says: "QLoRA", "4-bit base model", "fit on one GPU", "simple low memory", or "device_map auto".

Choose AWQ/GPTQ when the user says: "pre-quantized checkpoint", "calibration", "TheBloke-style AWQ/GPTQ", "Marlin", "high-quality 4-bit inference", or the model config contains `quantization_config.quant_method`.

Choose GGUF when the user says: "CPU-only", "llama.cpp", "GGUF file", "local quantized file", or "no CUDA".

Choose torchao when the user says: "torch.compile", "PyTorch-native quantization", "int4 weight-only", "float8", "CPU/XPU torchao", or "FSDP2/optimizer quantization".

Choose a specialized method only when the checkpoint, package, hardware, and desired bit-width make that method clearly better than the common defaults.
