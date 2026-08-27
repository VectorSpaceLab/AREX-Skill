# Model and Layer Workflows

This reference distills common FLA layer, module, and Transformers model workflows into self-contained recipes. The examples avoid checkpoint downloads unless a path or model id is explicitly provided by the caller.

## Installation and runtime prerequisites

- Python must be 3.10 or newer.
- The package's base metadata does not install `torch` or `triton`; select one backend extra for the intended hardware (`cuda`, `rocm`, `xpu`, `npu`, or `cpu`) and use a matching PyTorch wheel source.
- CUDA and CPU extras include upstream `triton`; ROCm and XPU get the matching Triton flavor through the PyTorch wheel; NPU uses `torch_npu` and `triton-ascend`.
- `fla.layers` and `fla.models` require `transformers` and `einops`. FLA models are registered with Hugging Face auto classes when their model subpackages are imported.
- CPU installs are useful for import and construction checks. Most real layer forward paths are Triton/GPU-oriented, so treat CPU forward success as optional unless a task explicitly targets CPU import-only behavior.

## Replace a standard attention block with an FLA layer

Use `fla.layers` classes when you are modifying an existing PyTorch module and want a token-mixing layer rather than a whole Hugging Face model.

```python
import torch
from fla.layers import GatedLinearAttention

layer = GatedLinearAttention(
    mode="chunk",
    hidden_size=1024,
    num_heads=4,
    expand_k=0.5,
    expand_v=1.0,
    use_short_conv=False,
    layer_idx=0,
).to(device="cuda", dtype=torch.bfloat16)

hidden_states = torch.randn(2, 128, 1024, device="cuda", dtype=torch.bfloat16)
attention_mask = torch.ones(2, 128, device="cuda", dtype=torch.bool)
output, attentions, past_key_values = layer(
    hidden_states=hidden_states,
    attention_mask=attention_mask,
    use_cache=False,
)
assert output.shape == hidden_states.shape
```

Layer API conventions:

- Inputs are `[batch, sequence, hidden_size]` tensors.
- Padding masks, when used, are 2D `[batch, sequence]` 0/1 or boolean masks. Arbitrary 3D attention matrices are rejected.
- Returned tuples follow `(hidden_states, attentions_or_none, cache_or_none)`.
- If `past_key_values` is supplied, pass a real `layer_idx`; cache update paths use it to index the layer state.
- Keep kernel/performance choices out of this sub-skill. Choose public layer/config parameters only; route kernel implementation and benchmarking elsewhere.

### GatedLinearAttention replacement checklist

- `mode` supports `chunk`, `fused_recurrent`, and `fused_chunk`.
- `hidden_size * expand_k` and `hidden_size * expand_v` must be divisible by `num_heads`.
- `num_kv_heads=None` means `num_kv_heads == num_heads`.
- `use_short_conv=True` adds short convolution state and makes cache behavior more important.
- `fuse_norm=True` plus a swish output gate uses fused RMSNorm-gated modules; set `fuse_norm=False` for easier tiny construction or CPU import smoke checks.

### KimiDeltaAttention replacement checklist

- `mode` supports `chunk` and `fused_recurrent`.
- Training requires `chunk` mode; inference may switch short sequences to recurrent mode internally.
- `head_dim * expand_v` and `num_v_heads * head_dim * expand_v` must be integer-compatible with the projected dimensions.
- If `num_v_heads > num_heads`, then `num_v_heads` must be divisible by `num_heads`.
- `safe_gate=True` requires a `lower_bound` value; `-5` is the documented recommendation.

## Build a Transformers model from an FLA config

Use configs from `fla.models`, not top-level `fla`.

```python
from transformers import AutoModelForCausalLM
from fla.models import GLAConfig

config = GLAConfig(
    hidden_size=32,
    num_hidden_layers=2,
    num_heads=4,
    hidden_ratio=2,
    max_position_embeddings=64,
    vocab_size=128,
    fuse_norm=False,
    fuse_swiglu=False,
    fuse_cross_entropy=False,
)
model = AutoModelForCausalLM.from_config(config)
```

Important details:

- `AutoModelForCausalLM.from_config(config)` constructs the registered FLA causal LM class; it does not download weights.
- `AutoModelForCausalLM.from_pretrained(path_or_id)` may download model weights/tokenizers unless `path_or_id` is a local path and the cache is already populated.
- Model configs include `fuse_norm`, `fuse_swiglu`, `fuse_cross_entropy`, `use_l2warp`, and model-specific attention parameters. Disable fused options for small construction checks when the runtime backend is uncertain.
- For direct model loss, pass unshifted labels in the usual causal LM form. The model shifts labels internally and uses the configured criterion.

## Hybrid attention plans through `config.attn`

FLA configs that include the hybrid mixin accept `attn=None`, one dictionary, or a list of dictionaries. A matched layer uses the standard `Attention` layer; omitted layers keep the model's native linear/recurrent/state-space mixer.

Single shared specification:

```python
from fla.models import GLAConfig

config = GLAConfig(num_hidden_layers=4)
config.attn = {
    "layers": [1, 3],
    "num_heads": 4,
    "num_kv_heads": 2,
    "qkv_bias": True,
    "window_size": 128,
    "rope_theta": 20000.0,
}
```

Heterogeneous list of specifications:

```python
config.attn = [
    {
        "layers": [1, 3],
        "num_heads": 4,
        "num_kv_heads": 2,
        "qkv_bias": True,
        "window_size": 128,
        "rope_theta": 20000.0,
    },
    {
        "layers": [5],
        "num_heads": 8,
        "num_kv_heads": 4,
        "qkv_bias": False,
        "window_size": None,
        "rope_theta": 40000.0,
    },
]
```

Normalization and validation behavior:

- Required fields per specification: `layers` and `num_heads`.
- Defaults per specification: `num_kv_heads=num_heads`, `qkv_bias=False`, `window_size=None`, `rope_theta=10000.0`.
- `layers` must be a list or tuple of integer indices in `[0, num_hidden_layers)`, with no duplicates inside a spec and no overlap across list items.
- `num_heads`, `num_kv_heads`, and non-`None` `window_size` must be positive integers; `qkv_bias` must be a bool; `rope_theta` must be positive and finite.
- Unknown extension keys are preserved in the config dictionary; only documented keys are consumed by the standard attention constructor.
- A one-item list and one dictionary produce equivalent layer structure, but serialization preserves the outer type.
- Standard `Attention` used by hybrid plans requires the optional FlashAttention package at construction time. If it is absent, avoid hybrid attention or install the optional dependency in the active environment.

## Fused modules in model code

```python
import torch
from fla.modules import RMSNorm, FusedLinearCrossEntropyLoss

norm = RMSNorm(hidden_size=1024, eps=1e-6)
hidden = norm(hidden)

criterion = FusedLinearCrossEntropyLoss(reduction="mean", num_chunks=8)
loss = criterion(hidden_states, shifted_targets, lm_head.weight, lm_head.bias)
```

Fused module guidance:

- `RMSNorm.forward(x, residual=None, prenorm=False, residual_in_fp32=False)` supports residual/pre-norm forms used by FLA blocks.
- `FusedLinearCrossEntropyLoss` consumes hidden states, target ids, output projection weights, and optional bias so logits do not need to be materialized.
- Fused linear cross entropy is memory-efficient but may reduce numerical precision. If loss diverges or training becomes unstable, disable it and compare against the non-fused criterion.
- In configs that expose both `fuse_cross_entropy` and `fuse_linear_cross_entropy`, do not enable both at once; the config rejects that combination.

## Generation workflow

Use Hugging Face generation APIs after loading or constructing a model and tokenizer.

```python
import torch
import fla  # ensures FLA model registrations are imported
from transformers import AutoModelForCausalLM, AutoTokenizer

path_or_id = "local-or-remote-fla-model"
tokenizer = AutoTokenizer.from_pretrained(path_or_id)
model = AutoModelForCausalLM.from_pretrained(path_or_id).to("cuda").eval()

prompt = "Flash linear attention is"
input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to("cuda")
with torch.no_grad():
    output_ids = model.generate(input_ids, max_new_tokens=32)
text = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
```

Generation caveats:

- `from_pretrained` and tokenizer loading can require network access unless files are already local or cached.
- Generation should use a GPU-capable backend for realistic workloads.
- Some FLA causal LM classes translate unsupported cache-manipulating generation strategies into a clear error. If that happens, try a simpler strategy before changing model internals.
- The repository's generation benchmark is intentionally not bundled here; use a minimal Hugging Face snippet unless the task explicitly asks for performance measurement.

## Training workflow

Training support is centered around a separate `flame` framework built on `torchtitan`, plus normal Hugging Face-style configs and checkpoints.

Use this decision checklist instead of starting training immediately:

1. Confirm that the caller wants an expensive training run rather than a config/model construction check.
2. Confirm GPU count, backend extra, dataset availability, tokenizer path, checkpoint policy, logging policy, and wall-clock budget.
3. For from-scratch runs, prepare a model config JSON, tokenizer path, optimizer/scheduler settings, batch size, sequence length, gradient accumulation, total steps, and checkpoint interval.
4. For continual pretraining, first convert or create a compatible Hugging Face checkpoint, then convert it into the distributed checkpoint format expected by the training launcher.
5. Treat dataset streaming, preprocessing workers, checkpoint conversion, and `wandb` logging as side effects that need explicit approval in constrained environments.

Skip training when the task only needs API guidance or a smoke check.

## Evaluation workflow

Two evaluation surfaces are relevant:

- `lm_eval` harness integration: imports `fla` before delegating to the harness and registers a `fla` model wrapper name in addition to the normal Hugging Face path.
- Perplexity evaluation: loads a tokenizer/model, streams or loads a dataset, chunks token blocks, runs model forward passes, and reports total plus block-wise perplexity.

Evaluation checklist:

1. Confirm that model weights and tokenizer are local/cached or that network access is allowed.
2. Confirm dataset name/path, split, text column, block size, bucket size, batch size, dtype, and device.
3. Use small tasks or a dry configuration display first; full zero-shot or long-context perplexity evaluation can be expensive.
4. Prefer local paths in offline or reproducibility-sensitive environments.
5. Do not run evaluation as a smoke check unless the caller has explicitly approved downloads, dataset reads, and GPU time.
