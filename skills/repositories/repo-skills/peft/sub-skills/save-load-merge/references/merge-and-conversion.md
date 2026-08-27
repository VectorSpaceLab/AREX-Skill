# Merge, Mixed Adapters, Hotswap, and Conversion

## `merge_and_unload`

Use `merge_and_unload` when the final artifact should be a plain base-model object with adapter deltas folded into the base weights:

```python
merged_model = model.merge_and_unload()
merged_model.save_pretrained("merged_model")
```

Trade-offs:

- The returned model no longer exposes PEFT adapter helper methods.
- You cannot disable, switch, unmerge, or continue PEFT adapter composition on the merged result.
- The saved artifact is much larger because it contains full base weights.
- Not every PEFT method, quantization setup, or method option supports merging.
- Merged inference can be faster and simpler for deployment when merging is supported.

Before merging, set the intended active adapter or pass supported `adapter_names` arguments where available. If multiple adapters are active, validate merged outputs against unmerged outputs on a small input before distributing the full model.

## Weighted adapter merging

For compatible LoRA adapters, create a new adapter by combining loaded adapters:

```python
model.load_adapter("adapter_b", adapter_name="b")
model.load_adapter("adapter_c", adapter_name="c")
model.add_weighted_adapter(
    adapters=["default", "b", "c"],
    weights=[1.0, 0.7, 0.3],
    adapter_name="blend",
    combination_type="ties",
    density=0.2,
)
model.set_adapter("blend")
```

Common LoRA `combination_type` choices include linear/SVD-style combinations plus TIES and DARE-TIES variants. TIES trims redundant values and resolves sign conflicts; DARE drops and rescales before merging. Start with conservative weights and test task outputs because the best weights are empirical.

For (IA)³ adapters, weighted merging is linear and uses `add_weighted_adapter` without LoRA-specific `combination_type`.

Embedding caution: when merging fully trained models or adapters trained after vocabulary extension, ensure all adapters share the intended tokenizer and embedding layout. Resize token embeddings before loading/merging if special tokens would otherwise collide at the same indices.

## Mixed adapter types

Use `PeftMixedModel` for inference-time composition of compatible adapter types:

```python
from peft import PeftMixedModel

model = PeftMixedModel.from_pretrained(base_model, "adapter_lora", adapter_name="lora")
model.load_adapter("adapter_loha", adapter_name="loha")
model.set_adapter(["lora", "loha"])
```

Rules:

- Mixed adapter support is for compatible tuner types and primarily for inference.
- Training mixed adapter models is not recommended unless the method combination is explicitly validated for the task.
- Mixed adapter models are not saved as one portable mixed checkpoint; save and load the individual adapters and recreate the composition script.
- Loading same-type adapters consecutively is usually faster than alternating types when many adapters are composed.
- Adapter order can affect outputs for non-commutative combinations; treat order as part of the inference recipe.

## Hotswapping LoRA adapters

Hotswap replaces an already-loaded adapter's weights in place. It is useful when repeatedly serving compatible LoRA adapters and when avoiding `torch.compile` recompilation.

```python
from peft import PeftModel
from peft.utils.hotswap import hotswap_adapter

model = PeftModel.from_pretrained(base_model, "adapter_a")
hotswap_adapter(model, "adapter_b", adapter_name="default", torch_device=device)
```

For compiled models whose ranks or scaling values may differ:

```python
from peft.utils.hotswap import prepare_model_for_compiled_hotswap

prepare_model_for_compiled_hotswap(model, target_rank=max_rank)
compiled_model = torch.compile(model)
hotswap_adapter(compiled_model, "adapter_b", adapter_name="default", torch_device=device)
```

Hotswap caveats:

- LoRA is the supported primary use case.
- The replacement adapter must use the same PEFT method.
- The replacement adapter must target the same layers as the current adapter or a subset; it cannot introduce new target layers.
- If possible, initially load the adapter with the broadest target-module coverage.

## Conversion utilities

PEFT includes helpers for converting compatible adapter families to LoRA-like artifacts. Typical use cases include approximating LoKr or other supported tuners with LoRA for downstream compatibility.

```python
from peft.utils.transformers_weight_conversion import convert_to_lora, save_as_lora

lora_config, lora_state_dict = convert_to_lora(peft_model, rank=8, adapter_name="default")
save_as_lora("converted_lora", peft_model, rank=8, adapter_name="default")
```

Conversion notes:

- `rank` can be an integer or supported fractional compression setting, depending on the source adapter and helper behavior.
- Approximate conversions should be evaluated against source outputs; low but nonzero error can be expected for compressed approximations.
- Conversion may reject unsupported modules, incompatible trainable bias, or method features that cannot be represented as LoRA.
- When multiple adapters are loaded, pass `adapter_name` explicitly.

## Saving a full Transformers model

If a Transformers-only artifact is required and `merge_and_unload` is unsuitable, LoRA adapters loaded through Transformers integration can sometimes be saved as a full model by saving a temporary PEFT-loaded model, loading it with Transformers, clearing the PEFT-loaded flag, and saving again. Prefer `merge_and_unload` when it is supported because the intent is clearer and easier to validate.
