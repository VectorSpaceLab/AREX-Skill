# Model Configuration Reference

This reference focuses on API-level configuration for MPT and Hugging Face model wrappers. It is not a full training or inference recipe.

## MPTConfig essentials

`MPTConfig` is a Hugging Face `PretrainedConfig` subclass with model type `mpt`. It validates component configs during construction and sets nested defaults for attention, FFN, init, and FC-layer choices.

Core shape parameters:

| Field | Default | Notes |
| --- | ---: | --- |
| `d_model` | `2048` | Hidden size. Must be divisible by `n_heads`. |
| `n_heads` | `16` | Attention head count. |
| `n_layers` | `24` | Transformer block count. |
| `head_dim` | `None` | Optional explicit attention head dimension; otherwise derived from `d_model / n_heads`. |
| `expansion_ratio` | `4` | FFN expansion ratio. |
| `max_seq_len` | `2048` | Must be integer-like; coerced to `int`. |
| `vocab_size` | `50368` | Token embedding vocabulary size. |
| `resid_pdrop`, `emb_pdrop` | `0.0` | Must be probabilities in `[0, 1]`. |
| `learned_pos_emb` | `True` | Automatically set to `False` when `alibi` or `rope` is enabled. |
| `init_device` | `cpu` | Common values are `cpu`, `meta`, or platform-specific/mixed through higher-level wrappers. |
| `norm_type` | `low_precision_layernorm` | Other registered norms include layer norm/RMS norm variants; some require flash/Triton support. |
| `norm_eps` | `1e-5` | Epsilon for normalization layers. |
| `fc_type` | `torch` | May be a string or `{name: ..., ...}` dict. `te` requires Transformer Engine. |
| `tie_word_embeddings` | `True` | If `False`, `MPTForCausalLM` creates a separate `lm_head`. |

Safe tiny CPU inspection config:

```python
from llmfoundry.models.mpt import MPTConfig, MPTForCausalLM

cfg = MPTConfig(
    d_model=64,
    n_heads=4,
    n_layers=2,
    max_seq_len=128,
    vocab_size=1024,
    attn_config={'attn_impl': 'torch', 'attn_type': 'multihead_attention'},
    ffn_config={'ffn_type': 'mptmlp'},
    init_config={'name': 'kaiming_normal_'},
    fc_type='torch',
)
model = MPTForCausalLM(cfg)
```

Use this pattern only for API/constructor checks; it is not a meaningful model for quality or throughput.

## Attention config

Default `attn_config` is:

```python
{
    'attn_type': 'multihead_attention',
    'attn_pdrop': 0.0,
    'attn_impl': 'flash',
    'qk_ln': False,
    'qk_gn': False,
    'fused_qkv': True,
    'clip_qkv': None,
    'softmax_scale': None,
    'attn_uses_sequence_id': False,
    'sliding_window_size': -1,
    'attn_logit_softcapping': None,
    'alibi': False,
    'alibi_bias_max': 8,
    'rope': False,
    'nope': False,
    'rope_theta': 10000,
    'rope_impl': 'dail',
    'rope_dail_config': {
        'type': 'original',
        'pos_idx_in_fp32': True,
        'xpos_scale_base': 512,
    },
    'rope_hf_config': {
        'type': 'no_scaling',
        'factor': 1.0,
    },
    'attn_temperature_tuning': {
        'floor_scale': 8192,
        'attn_scale': 0.0,
    },
    'kv_dim': None,
}
```

Important attention options:

- `attn_impl`: `torch` or `flash`. The default is `flash`, but CPU-only inspection should use `torch`.
- `attn_type`: `multihead_attention`, `multiquery_attention`, or `grouped_query_attention`.
- `qk_ln` / `qk_gn`: enable query/key layer norm or group norm. Do not set both unless the target attention implementation explicitly supports the combination.
- `fused_qkv`: fuses Q/K/V projections. Set `False` when `kv_dim` is specified.
- `kv_dim`: cross-attention key/value input dimension; incompatible with `fused_qkv=True`.
- `attn_uses_sequence_id`: restricts attention to tokens with the same `sequence_id`; supported by torch attention and flash attention only when the flash version is new enough.
- `sliding_window_size`: `-1` disables local sliding-window attention. Non-negative values require torch attention or a sufficiently new flash attention.
- `alibi`: disables learned position embeddings and requires an attention implementation/version that supports ALiBi.
- `rope`: disables learned position embeddings and enables rotary position embeddings.
- `rope_impl`: `hf` or `dail`. `dail` requires flash-attention; `hf` uses Hugging Face-style rotary embedding support.
- `rope_hf_config.type`: `no_scaling`, `linear`, `dynamic`, or `llama3`.
- `rope_dail_config.type`: `original` or `xpos`.
- `nope`: no position encoding. It cannot be the default position encoding; use it only inside `block_overrides` and respect learned-position/ALiBi restrictions.
- `attn_logit_softcapping`: must be positive when set; flash attention needs a sufficiently new version.

## FFN, FC, norm, and init config

Default `ffn_config`:

```python
{'ffn_type': 'mptmlp'}
```

Common FFN choices:

- `mptmlp`: standard MPT MLP path.
- `mptglu`: gated linear unit path.
- `te_ln_mlp`: Transformer Engine layer-norm MLP; requires `transformer-engine[pytorch]` and a compatible accelerator/runtime.
- MegaBlocks MoE FFNs such as `mb_moe` or `mb_dmoe` require MegaBlocks/grouped-GEMM packages and CUDA-compatible runtime.

Default `fc_type`:

```python
{'name': 'torch'}
```

Use `fc_type: te` only when Transformer Engine is installed and supported by the target hardware. `fc_type` can also be a dict with `name` plus layer-specific kwargs.

Default `init_config`:

```python
{
    'name': 'kaiming_normal_',
    'fan_mode': 'fan_in',
    'init_nonlinearity': 'relu',
    'init_div_is_residual': True,
    'emb_init_std': None,
    'emb_init_uniform_lim': None,
    'init_std': None,
    'init_gain': 0.0,
}
```

Recognized initializer names include `default_`, `baseline_`, `kaiming_uniform_`, `kaiming_normal_`, `neox_init_`, `small_init_`, `xavier_uniform_`, and `xavier_normal_`.

## Block overrides

`block_overrides` is experimental and must contain both `order` and `overrides`. The override name `default` is reserved and cannot be used as a custom override key.

Allowed override families include:

```yaml
block_overrides:
  order:
  - name: default
  - name: sliding_window_layer
  overrides:
    sliding_window_layer:
      attn_config:
        sliding_window_size: 1024
```

Allowed override fields include `attn_config.sliding_window_size`, `attn_config.reuse_kv_layer_idx`, `attn_config.reuse_kv_x_layer_idx`, `attn_config.attn_temperature_tuning`, and `attn_config.nope`.

## MPTForCausalLM

`MPTForCausalLM(config)` constructs an HF-compatible causal LM around `MPTModel`.

Important behaviors:

- If `tie_word_embeddings=True`, output embeddings use the token embedding layer; if `False`, a separate `lm_head` is created.
- `logit_scale` can be numeric or `inv_sqrt_d_model`.
- Forward accepts `input_ids`, `past_key_values`, `attention_mask`, `sequence_id`, `labels`, `return_dict`, `output_attentions`, `output_hidden_states`, `use_cache`, `inputs_embeds`, and `position_ids`.
- Labels are shifted internally for causal LM loss.
- Generation does not support right padding.
- `fsdp_wrap_fn` and `activation_checkpointing_fn` expose FSDP/activation-checkpointing behavior for Composer integration.

## ComposerMPTCausalLM

`ComposerMPTCausalLM` wraps `MPTForCausalLM` as a Composer `HuggingFaceModel` and builds default metrics through the metrics registry.

Key configuration rules:

```yaml
model:
  name: mpt_causal_lm
  d_model: 64
  n_heads: 4
  n_layers: 2
  max_seq_len: 128
  vocab_size: 1024
  attn_config:
    attn_impl: torch
  loss_fn: torch_crossentropy
```

- Default `loss_fn` is `fused_crossentropy`; it requires flash-attention fused cross entropy. Use `torch_crossentropy` for CPU or minimal API checks.
- `additional_train_metrics` appends registry metric names to both train and eval metric lists.
- MegaBlocks FFN types clear/load balancing loss state during forward/loss and fail if MegaBlocks is missing.

## ComposerHFCausalLM

`ComposerHFCausalLM` wraps Hugging Face `AutoModelForCausalLM`.

Key options:

- `pretrained_model_name_or_path`: local path or HF model id.
- `pretrained=True`: loads pretrained weights and may download.
- `pretrained=False`: constructs from config; safer for offline API tests when config is available.
- `trust_remote_code=True` by default. Disable unless remote code is explicitly trusted.
- `use_auth_token=True` expects HF authentication to be configured.
- `use_flash_attention_2=True` forces `attn_implementation='flash_attention_2'` and requires flash-attention 2.
- `load_in_8bit=True` requires a compatible bitsandbytes/accelerate stack.
- `init_device='meta'` is not supported with `pretrained=True`.
- `peft_config` requires the PEFT extra.
- MPT models hosted under the historical Mosaic MPT Hugging Face namespace are explicitly rejected by current LLM Foundry; use native MPT classes or a compatible package version.

## ComposerHFT5

`ComposerHFT5` is experimental and wraps Hugging Face seq2seq/T5 models.

Key options:

```yaml
model:
  name: hf_t5
  pretrained_model_name_or_path: t5-small
  pretrained: false
  init_device: cpu
```

- The underlying config must be encoder-decoder (`is_encoder_decoder=True`).
- `config_overrides` are validated against existing config attributes; mapping overrides cannot introduce unknown subkeys.
- Public introspection can show `(*args, **kwargs)` because of the experimental decorator, so use the operational constructor signature from the API reference.

## Configuration transforms

`llmfoundry.registry.config_transforms` contains config-transform callables. The built-in transform is `update_batch_size_info`.

Rules:

- `apply_transforms_to_config(cfg, transforms=None)` returns the config unchanged.
- A list can contain transform names or callables.
- The special string `all` applies all registered transforms.
- Unknown transform names fail through the registry.

Train/eval dataclass conversion rejects unused top-level keys. Put experiment variables under `variables` instead of arbitrary top-level fields.
