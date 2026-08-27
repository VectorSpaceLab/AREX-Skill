# LoRA API and Variant Reference

This reference summarizes PEFT LoRA configuration choices that can be made without relying on source-tree paths.

## Main entry points

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(...)
model = get_peft_model(base_model, config)
```

Useful constructor facts:

- `LoraConfig(...)` stores adapter configuration and defaults to `r=8`, `lora_alpha=8`, `lora_dropout=0.0`, `bias="none"`, `init_lora_weights=True`, and `use_rslora=False`.
- `get_peft_model(model, peft_config, adapter_name="default", mixed=False, autocast_adapter_dtype=True, revision=None, low_cpu_mem_usage=False)` wraps a model with PEFT adapters.
- `PeftModel(model, peft_config, adapter_name="default", autocast_adapter_dtype=True, low_cpu_mem_usage=False)` is the wrapped model class.

## Targeting modules and parameters

`target_modules` accepts:

- `None`: PEFT tries architecture-specific defaults; unknown architectures raise and require manual targets.
- `"all-linear"`: all linear/Conv1D modules, except output layer for `PreTrainedModel` where applicable. This is the usual QLoRA-style setting.
- `list[str]`: exact name or suffix match, such as `q_proj`, `v_proj`, `query`, `value`.
- `str`: regular-expression match.
- `[]`: target no modules, usually because `target_parameters` is being used.

Use `exclude_modules` to remove specific matches from a broad target set.

Use `target_parameters` for LoRA on raw parameters that do not have a module `forward`, such as some MoE expert parameters. `target_parameters` must be a list of strings; regex string matching is not implemented for this field. When only parameter targets are desired, set `target_modules=[]`.

`layers_to_transform` and `layers_pattern` only work when `target_modules` is a list, not a regex string.

## Rank, scaling, dropout, and bias

- `r`: adapter rank. Higher rank increases trainable parameters and capacity.
- `lora_alpha`: scaling numerator. In standard LoRA, effective scaling is `lora_alpha / r`.
- `use_rslora=True`: changes scaling to `lora_alpha / sqrt(r)` and is useful for higher ranks.
- `lora_dropout`: dropout applied in LoRA branch. Use `0.0` for many large-model instruction tuning runs; increase when overfitting or small data calls for regularization.
- `bias="none"`: safest default. `"all"` and `"lora_only"` train bias terms and can change model output even with adapters disabled.
- `lora_bias=True`: specialized LoRA-B bias support for extracted LoRA weights; only works with `init_lora_weights=True` or `False` and not with DoRA.

Use `rank_pattern` and `alpha_pattern` for module-specific overrides. Keys can be layer names or regexes; unmatched layers use `r` and `lora_alpha`.

## Initialization choices

- `init_lora_weights=True`: default no-op initialization; LoRA B starts at zero.
- `False`: random non-no-op initialization; use for debugging/testing, not normal training.
- `"gaussian"`: Gaussian LoRA A, zero LoRA B.
- `"orthogonal"`: orthogonal LoRA A/B for linear layers; requires even `r`; does not mutate base weights.
- `"pissa"`: exact SVD PiSSA; can take minutes for large models.
- `"pissa_niter_N"`: fast-SVD PiSSA with `N` subspace iterations; `N` must be nonnegative.
- `"olora"`: QR-based OLoRA; mutates base weights during initialization.
- `"eva"`: activation-SVD EVA; provide or accept `EvaConfig`, wrap model, then call `initialize_lora_eva_weights(peft_model, dataloader)`.
- `"corda"`: CorDA; provide or accept `CordaConfig`, run CorDA preprocessing over representative data, then wrap.
- `"loftq"`: LoftQ; requires `LoftQConfig`, requires `scipy`, and quantizes the backbone itself.
- `"lora_ga"`: LoRA-GA; provide `LoraGAConfig`, run `preprocess_loraga`, and use full-precision weights.

If a sub-config is set without the matching `init_lora_weights` value, PEFT warns and ignores it for several variants.

## Variant configuration patterns

### DoRA

```python
config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    r=8,
    lora_alpha=16,
    use_dora=True,
)
```

DoRA adds a learnable magnitude parameter. It supports linear and Conv2D layers. It has more runtime overhead than standard LoRA; merge for inference when the downstream save/load workflow permits it. DoRA does not support Megatron LoRA config. QDoRA can work with bitsandbytes, but DeepSpeed ZeRO-2 has known caveats.

### RS-LoRA

```python
config = LoraConfig(r=64, lora_alpha=128, use_rslora=True, target_modules="all-linear")
```

RS-LoRA is usually a low-risk improvement when using larger ranks. Avoid combining RS-LoRA, `rank_pattern`/`alpha_pattern`, and post-training conversion of mutated-base initializers such as PiSSA, CorDA, OLoRA, or LoRA-GA if you plan to restore initial base values during save.

### PiSSA

```python
config = LoraConfig(init_lora_weights="pissa_niter_16", target_modules="all-linear", r=16, lora_alpha=32)
```

Use `"pissa"` for exact SVD or `"pissa_niter_N"` for faster approximate SVD. PiSSA can improve convergence and reduce quantization error compared with plain QLoRA.

### CorDA

```python
from peft import CordaConfig, LoraConfig

corda_config = CordaConfig(corda_method="kpm")
config = LoraConfig(init_lora_weights="corda", corda_config=corda_config, target_modules="all-linear")
```

Run CorDA preprocessing before `get_peft_model`. Choose knowledge-preserved mode when retaining pretrained knowledge matters, and instruction-previewed mode when task adaptation speed/quality is the priority.

### EVA

```python
from peft import EvaConfig, LoraConfig, get_peft_model, initialize_lora_eva_weights

config = LoraConfig(init_lora_weights="eva", eva_config=EvaConfig(rho=2.0), target_modules="all-linear")
peft_model = get_peft_model(base_model, config, low_cpu_mem_usage=True)
initialize_lora_eva_weights(peft_model, dataloader)
```

`rho >= 1.0` controls rank redistribution. `rho=1.0` disables redistribution; `rho=2.0` allows up to `2r` per layer. EVA works with bitsandbytes-quantized models.

### LoftQ

```python
from peft import LoftQConfig, LoraConfig

config = LoraConfig(
    init_lora_weights="loftq",
    loftq_config=LoftQConfig(loftq_bits=4, loftq_iter=1),
    target_modules="all-linear",
)
```

Do not pass an already quantized model to this path. For already quantized bitsandbytes 4-bit models, use ordinary LoRA and then `replace_lora_weights_loftq` instead.

### QALoRA

```python
config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    use_qalora=True,
    qalora_group_size=16,
)
```

QALoRA is currently implemented for GPTQ and linear layers. Every targeted module input dimension must be divisible by `qalora_group_size`.

### aLoRA

```python
config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    alora_invocation_tokens=tokenizer.encode("<tool_adapter>", add_special_tokens=False),
)
```

aLoRA activates adapter weights only at and after the invocation tokens. Use it for causal-LM pipelines that can reuse base-model KV cache before the invocation. Merging is not possible.

### Trainable tokens with LoRA

```python
config = LoraConfig(
    target_modules="all-linear",
    trainable_token_indices={"embed_tokens": new_token_ids},
)
```

Add tokens to the tokenizer and resize the model embeddings before wrapping. With FSDP, use `use_orig_params=True` because only selected embedding rows are trainable.

### LoRA-GA

```python
from peft import LoraConfig, LoraGAConfig
from peft.tuners.lora import preprocess_loraga

config = LoraConfig(
    init_lora_weights="lora_ga",
    lora_ga_config=LoraGAConfig(direction="ArB2r", scale="stable"),
    target_modules="all-linear",
)
preprocess_loraga(base_model, config, train_step)
```

Run a small gradient-estimation phase before training. LoRA-GA modifies base weights and does not support quantized models.

### MonteLoRA, VeLoRA, BdLoRA, and Arrow

- MonteLoRA: pass `monteclora_config` to add stochastic sampling/regularization. Increase `num_samples` for smoother estimates and decrease it for speed.
- VeLoRA: pass `velora_config` to reduce activation memory through compressed activation storage in the LoRA A path.
- BdLoRA: pass `use_bdlora=BdLoraConfig(...)`; keep target lists for block-diagonal A and B non-overlapping.
- Arrow: use `create_arrow_model` with compatible task/general LoRA adapter paths and an `ArrowConfig`. Loaded adapters must agree on target modules and rank before adding the router adapter.

## AdaLoRA

AdaLoRA has a separate `AdaLoraConfig` and dynamically allocates rank budget during training. It is LoRA-like but should be treated as its own tuner configuration, especially for schedule parameters. It does not support DoRA or LoftQ config. AdaLoRA supports bitsandbytes and GPTQ quantization.
