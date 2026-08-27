# PyTorch New Model Support

LMDeploy's PyTorch backend loads a Hugging Face config/model description, builds an LMDeploy `ModelConfig`, then replaces or builds supported model classes through a module-map based patching layer. Add support in small, testable layers: config parsing first, model class second, registration last.

## Extension Surfaces

| Surface | Purpose |
| --- | --- |
| `lmdeploy.pytorch.configurations.*` | Convert Hugging Face config objects into LMDeploy `ModelConfig`. |
| `AutoModelConfigBuilder` | Registry base for model config builders; each builder declares a `condition(hf_config)`. |
| `lmdeploy.pytorch.models.*` | Optimized PyTorch model implementations using LMDeploy kernels/modules. |
| `lmdeploy.pytorch.models.module_map.MODULE_MAP` | Maps HF architecture/class names to LMDeploy model classes. |
| `DEVICE_SPECIAL_MODULE_MAP` | Device-specific overrides for Ascend/MACA/CAMB when needed. |
| `CUSTOM_MODULE_MAP` / `custom_module_map` | External override map for experiments without editing installed LMDeploy. |
| `lmdeploy.pytorch.models.patch` | Resolves rewrite classes from full qualname, class name, submodule name, `auto_map`, or architectures. |

## Config Builder Workflow

Add or adapt a builder when the Hugging Face config does not match existing default field names.

Checklist:

1. Create a builder class under `lmdeploy.pytorch.configurations` or reuse an existing family builder.
2. Implement `condition(cls, hf_config)` so only the intended model family matches.
3. Implement `build(cls, hf_config, model_path=None, ...)` to return `ModelConfig` with at least hidden size, layer count, attention heads, KV heads, token IDs, head dim, vocab size, and any model-specific flags.
4. Let `ModelConfig.from_hf_config()` attach `dist_config`, resolve dtype, normalize EOS IDs, and assert TP head divisibility.
5. Add focused tests for head splitting, defaults, special config names, and TP divisibility.

Config smoke pattern:

```bash
python - <<'PY'
from types import SimpleNamespace
from lmdeploy.pytorch.config import DistConfig, ModelConfig

hf_config = SimpleNamespace(
    architectures=['YourModelForCausalLM'],
    bos_token_id=1,
    eos_token_id=2,
    hidden_size=4096,
    model_type='your_model',
    num_attention_heads=32,
    num_hidden_layers=1,
    num_key_value_heads=8,
    vocab_size=32000,
)
model_config = ModelConfig.from_hf_config(hf_config, dist_config=DistConfig(tp=4))
print(model_config.get_num_qkv_head_by_tp())
PY
```

The upstream docs mention `lmdeploy.pytorch.check_env.check_model` for config parsing checks. In version 0.13.0 check whether that helper exists in the installed package before relying on it; if absent, use `ModelConfig.from_pretrained()` or `ModelConfig.from_hf_config()` as the config smoke check.

## Model Implementation Checklist

Follow existing model files such as Llama/Qwen/Gemma for structure. Required pieces for a generation-capable model class:

- Constructor accepts the Hugging Face config, a `StepContextManager`, optional `dtype`, and optional `device`.
- `forward(...)` accepts `input_ids`, `position_ids`, `past_key_values`, `attn_metadata`, optional `inputs_embeds`, and `**kwargs` as appropriate for the family.
- `prepare_inputs_for_generation(...)` returns a dict whose keys match `forward` parameters.
- `load_weights(self, weights)` maps incoming state-dict names/tensors into LMDeploy modules and handles packed/merged projections.
- `support_cuda_graph = True` or a callable/property when CUDA graph support depends on input/model state.
- Uses LMDeploy NN helpers (`build_merged_colwise_linear`, `build_rowwise_linear`, norms, rotary embedding, MoE helpers, quantized linear builders) so TP and quantization remain consistent.
- Handles quantization config from the HF config where applicable.
- Does not silently ignore unmatched critical weights; return/log skipped names only when intentional.

## Module Map Registration

For built-in support, update `MODULE_MAP` with the Hugging Face architecture key and the LMDeploy class qualname:

```python
MODULE_MAP.update({
    'YourModelForCausalLM':
    f'{LMDEPLOY_PYTORCH_MODEL_PATH}.your_model.YourModelForCausalLM',
})
```

Resolution behavior in `patch.py`:

- `_get_rewrite_qualname()` first tries exact map keys, then regex search against the origin qualname.
- `_find_rewrite_module_qualname()` tries full module/class qualname, class name, then submodule/class name.
- `_get_model_class()` checks `auto_map['AutoModelForCausalLM']`, then `architectures`.
- Device-specific maps augment the base map for non-CUDA devices.
- `CUSTOM_MODULE_MAP` overrides are applied after base/device maps.

Use `scripts/inspect_backend_config.py --module-map --filter yourmodel` to check installed registration keys without importing model weights.

## External `custom_module_map`

Use `PytorchEngineConfig(custom_module_map=...)` for prototypes or downstream private models. The path should be a Python file that defines `MODULE_MAP` or `CUSTOM_MODULE_MAP`.

Example external map file:

```python
MODULE_MAP = {
    'YourModelForCausalLM': 'YourModelForCausalLM',
}
```

When the value has no dot, LMDeploy loads the custom file as an internal `_custom_mod` module and qualifies the class under the custom module namespace. When the value contains dots, it is treated as an importable qualname.

Use this path when:

- The user cannot or should not edit installed LMDeploy source.
- You need to validate a new model implementation before upstreaming.
- You are debugging map resolution independently from a wheel install.

Avoid it when maintaining LMDeploy itself and the model should be first-class; update `MODULE_MAP` and tests instead.

## Focused Tests

Run the smallest relevant tests first:

```bash
pytest tests/pytorch/config/test_model_config.py
pytest tests/pytorch/paging/test_scheduler.py
```

Add focused tests near the edited surface:

- Config builder: `ModelConfig.from_hf_config()` for common and edge configs, TP head splitting, EOS ID normalization, dtype behavior, and model-specific flags.
- Module registration: map key exists and resolves to an importable class without loading weights.
- Model class: instantiate with a small synthetic config on meta/CPU where possible, check `prepare_inputs_for_generation()` keys, and check `load_weights()` name transforms with synthetic tensors.
- CUDA graph: check `support_cuda_graph` for unsupported input modes and ensure graph runner falls back when needed.
- Scheduler/cache changes: extend scheduler unit tests with block allocation, eviction, prefix-cache rollback, or state-cache scenarios.

GPU/full model validation should come after static/config checks and can be limited to a tiny model or known local fixture if available.

## Common Review Questions

- Does the config builder match only the intended model family?
- Are attention/KV heads divisible under the intended TP settings?
- Are packed QKV/gate-up/down projections loaded in the same order as the source checkpoint?
- Does the implementation use LMDeploy linear/norm/attention helpers so quantization and TP work?
- Does `custom_module_map` remain an optional extension path rather than a hidden runtime dependency?
- Are tests focused enough to run without downloading large models?
