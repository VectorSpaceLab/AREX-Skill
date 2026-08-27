# PaLM Modeling API Reference

This reference distills the package's transformer-core API for future agents. It is intentionally self-contained and should be used with the installed `palm_rlhf_pytorch` package, not with the original source checkout.

## Public Imports and Internal Building Blocks

Primary runtime import:

```python
from palm_rlhf_pytorch import PaLM
```

Core implementation concepts:

- `PaLM` is the public transformer module exported by the package root.
- The transformer stack uses parallel attention/feedforward blocks, RMS-style query/key normalization when requested, rotary positional embeddings with XPOS scaling for causal models, tied token embedding/logit weights, and optional LoRA adapters.
- `Attention` is an internal module used by the transformer blocks. You usually configure it through `PaLM(..., flash_attn=...)` rather than instantiating it directly.
- `LoRA` is an internal low-rank adapter module used when finetune scopes are added.
- Sampling helpers live in `palm_rlhf_pytorch.utils`; `PaLM.generate` defaults to `top_k` filtering and gumbel sampling.

## Constructor

Verified constructor shape:

```python
PaLM(
    *,
    dim,
    num_tokens,
    depth,
    causal=True,
    dim_head=64,
    heads=8,
    ff_mult=4,
    attn_dropout=0.0,
    ff_dropout=0.0,
    qk_rmsnorm=False,
    lora_r=8,
    rotary_xpos_scale_base=512,
    flash_attn=False,
    finetune_scopes=(),
    cross_entropy_ignore_index=0,
)
```

Important choices:

| Argument | Use |
| --- | --- |
| `num_tokens` | Vocabulary size. Token ids must be in `[0, num_tokens)` except negative ids for masking in non-causal mode. |
| `dim`, `depth`, `heads`, `dim_head`, `ff_mult` | Model size knobs. For smoke checks, use very small values such as `dim=32`, `depth=1`, `heads=2`, `dim_head=16`. |
| `causal` | `True` for autoregressive language modeling and generation. `False` enables encoder-like masking where negative input token ids are treated as masked positions. |
| `attn_dropout`, `ff_dropout` | Dropout probabilities. Set to `0.0` for deterministic-ish checks. Change later with `set_dropout`. |
| `qk_rmsnorm` | Enables normalized query/key vectors with learned scales and a different attention scale. |
| `lora_r`, `finetune_scopes` | Default LoRA rank and initial named finetune adapter scopes. You can add scopes later. |
| `rotary_xpos_scale_base` | XPOS scaling base for rotary embeddings in causal mode. |
| `flash_attn` | Enables PyTorch scaled-dot-product attention path. This is not the external `flash-attn` package. It requires PyTorch 2.0+ by assertion; project metadata already requires newer torch. |
| `cross_entropy_ignore_index` | Ignore index used by `return_loss=True` next-token cross entropy. Defaults to `0`, so token id 0 labels are ignored in the loss. |

## Forward Modes

Verified signature:

```python
PaLM.forward(
    x,
    return_loss=False,
    disable_lora=False,
    finetune_scope=None,
    extra_embed=None,
    return_only_embedding=False,
    return_logits_with_embedding=False,
)
```

Input `x` is a `LongTensor` shaped `(batch, seq_len)`.

### Loss Mode

```python
loss = palm(tokens, return_loss=True)
loss.backward()
```

- `return_loss=True` shifts tokens internally: inputs are `x[:, :-1]`, labels are `x[:, 1:]`.
- The returned value is a scalar cross-entropy loss.
- Sequence length must be at least 2 for meaningful next-token loss.
- The default ignore index is token id `0`; if `0` is a real token in your task, pass a different `cross_entropy_ignore_index` at construction.

### Logit Mode

```python
logits = palm(tokens)
# shape: (batch, seq_len, num_tokens)
```

This is the default inference/training output when neither embedding-only nor loss mode is requested.

### Embedding Mode

```python
embeds = palm(tokens, return_only_embedding=True)
# shape: (batch, seq_len, dim)
```

Use this for downstream modules that need final normalized hidden states, or for shape checks that avoid the output vocabulary projection.

### Logits with Embeddings

```python
logits, embeds = palm(tokens, return_logits_with_embedding=True)
# logits: (batch, seq_len, num_tokens)
# embeds: (batch, seq_len, dim)
```

Generation uses this mode internally to sample from the final token while retaining the final embedding.

### Extra Embeddings

`extra_embed` is added to token embeddings before transformer layers. It should broadcast to the embedded token tensor shape `(batch, seq_len, dim)` and be on the same device/dtype. It is useful for experiments that inject side information, but it is not shown in the public README examples.

### Non-Causal Masking

When `causal=False`, negative token ids are treated as masked positions. The model replaces them with `0` before embedding and passes a key-padding mask into attention. Do not feed negative token ids in causal language-modeling mode.

## Generation

Verified signature:

```python
PaLM.generate(
    seq_len,
    prompt=None,
    temperature=1.0,
    filter_logits_fn=top_k,
    filter_thres=0.9,
    pad_value=0.0,
    eos_token=None,
    return_seq_without_prompt=True,
    use_tqdm=False,
    **kwargs,
)
```

Key semantics:

- `seq_len` is the **target total sequence length**, not the number of new tokens.
- If `prompt` is provided and `return_seq_without_prompt=True` (default), the returned tensor contains only generated tokens after the prompt.
- Therefore, with a prompt length `p` and `seq_len > p`, the default output length is `seq_len - p`.
- If `prompt` is omitted, the method creates a random one-token prompt on the model device and returns the full sequence by forcing `return_seq_without_prompt=False`.
- If `seq_len <= prompt_len`, the implementation still samples at least one token internally, so do not use `seq_len <= prompt_len` when you need exact suffix-length assertions.
- `**kwargs` are forwarded to `forward`, so generation can use `finetune_scope=...` or `disable_lora=True`.

Example with explicit shape handling:

```python
import torch
from palm_rlhf_pytorch import PaLM

num_tokens = 128
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = PaLM(num_tokens=num_tokens, dim=32, depth=1, heads=2, dim_head=16).to(device)
prompt = torch.randint(0, num_tokens, (2, 4), device=device)

suffix = model.generate(seq_len=7, prompt=prompt, temperature=1.0, use_tqdm=False)
assert suffix.shape == (2, 3)  # 7 target total length - 4 prompt tokens

full = model.generate(seq_len=7, prompt=prompt, return_seq_without_prompt=False, use_tqdm=False)
assert full.shape == (2, 7)
```

### Sampling Helpers

`generate` defaults to:

- `filter_logits_fn=top_k`
- `filter_thres=0.9`
- `temperature=1.0`
- gumbel sampling over filtered logits

Available utility filters include `top_k` and `top_p` from `palm_rlhf_pytorch.utils`. Pass `filter_logits_fn=None` to sample from unfiltered logits. Use a fixed torch seed for deterministic-ish smoke tests, but remember gumbel sampling is still stochastic by design.

## Attention and Flash-Attention Decision Points

`flash_attn=True` routes attention through `torch.nn.functional.scaled_dot_product_attention` with `torch.backends.cuda.sdp_kernel` configuration. It does **not** require installing the external `flash-attn` package.

Decision guide:

| Situation | Recommended setting |
| --- | --- |
| CPU smoke tests or unknown torch backend | `flash_attn=False` first; optionally test `True` only if torch is new enough. |
| PyTorch < 2.0 | `flash_attn=False`; the package asserts if `flash_attn=True`. |
| CUDA A100 | `flash_attn=True` may use the flash-only SDPA backend when tensors are on CUDA. |
| Non-A100 CUDA | `flash_attn=True` may use math or memory-efficient SDPA backends. |
| Debugging masks or numerical issues | Compare with `flash_attn=False`. |

The project metadata requires `torch>=2.2`, so a normal package install should satisfy the version gate. Still, future agents may run in pre-existing environments; check `torch.__version__` when diagnosing.

## Save and Load

`PaLM.load(path)` asserts the path exists and then calls `load_state_dict(torch.load(str(path)))`.

For saving, use PyTorch directly:

```python
torch.save(palm.state_dict(), checkpoint_path)

restored = PaLM(num_tokens=num_tokens, dim=dim, depth=depth)
restored.load(checkpoint_path)
```

Keep constructor settings compatible with the saved weights. If LoRA scopes are present in the state dict, recreate the same scopes before loading or use the exact same construction recipe.

## Dropout Operations

```python
palm.set_dropout(0.0)
```

`set_dropout` walks dropout modules inside transformer layers and updates their `p` values, then returns `self`. It is useful for deterministic-ish checks or changing regularization for finetuning.

Generation is decorated to switch the model to eval mode temporarily and then restore the previous training/eval state.

## LoRA Finetune Scopes

LoRA adapters are managed by named scopes stored in `palm.finetune_modules`.

### Add a Scope

```python
palm.add_finetune_params("actor", lora_r=4)
```

- Scope names must be unique; adding an existing scope raises an assertion.
- If `lora_r` is omitted, the constructor's `lora_r` is used.
- A scope creates LoRA modules for each layer's query, key, value, and output projection.
- New modules are moved to the current model device.

You can also pass `finetune_scopes=("default",)` in the constructor.

### Select Optimizer Parameters

```python
base_optim = torch.optim.AdamW(palm.palm_parameters(), lr=1e-4)

palm.add_finetune_params("actor")
lora_optim = torch.optim.AdamW(palm.finetune_parameters("actor"), lr=1e-3)
```

- `palm_parameters()` returns base model parameters excluding all LoRA scope parameters.
- `finetune_parameters(scope="default")` asserts that the scope exists and returns only that scope's LoRA parameters.
- Avoid optimizing both full base parameters and LoRA parameters unless that is intentional for the experiment.

### Use a Scope in Forward or Generation

```python
logits = palm(tokens, finetune_scope="actor")
suffix = palm.generate(12, prompt=tokens[:, :4], finetune_scope="actor")
base_logits = palm(tokens, finetune_scope="actor", disable_lora=True)
```

- `finetune_scope` selects a named adapter for the current call.
- `disable_lora=True` bypasses selected LoRA modules.
- Passing a missing scope raises an assertion.

### Remove or Merge a Scope

```python
removed_modules = palm.remove_finetune_params("actor")

palm.add_finetune_params("actor")
# ... train LoRA params ...
palm.merge_finetune_params("actor")
```

- `remove_finetune_params(scope)` deletes and returns the scope modules; it asserts if the scope is absent.
- `merge_finetune_params(scope)` adds the LoRA weights into the base projection weights and removes the scope. Use it only when you intentionally want a fused base model for subsequent rounds.
- After merging, that scope no longer exists; calling `finetune_parameters(scope)` will assert.

## Tiny Smoke Expectations

The bundled `scripts/tiny_palm_smoke.py` checks:

- installed package import from `palm_rlhf_pytorch`;
- loss scalar and backward pass;
- logits shape `(batch, seq_len, num_tokens)`;
- embedding shape `(batch, seq_len, dim)`;
- combined logits+embeddings shapes;
- generation suffix and full-sequence shapes;
- optional LoRA scope add/use/parameter/remove/merge assertions.

Use this helper as the first diagnostic before adapting larger workflows.
