# Core integration workflows

## Replace a dense layer

```python
import torch
import torch.nn as nn
import loralib as lora

class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = lora.Linear(768, 2, r=8, lora_alpha=16, lora_dropout=0.05)

model = Classifier()
lora.mark_only_lora_as_trainable(model)
optimizer = torch.optim.AdamW(
    (parameter for parameter in model.parameters() if parameter.requires_grad),
    lr=1e-3,
)
```

Inspect the selected parameters before training:

```python
[name for name, parameter in model.named_parameters() if parameter.requires_grad]
# ['proj.lora_A', 'proj.lora_B']
```

## Save and load an adapter-only checkpoint

```python
adapter_state = lora.lora_state_dict(model)
torch.save(adapter_state, "task-lora.pt")

base_model = Classifier()
base_model.load_state_dict(torch.load("base-model.pt", map_location="cpu"), strict=False)
missing, unexpected = base_model.load_state_dict(
    torch.load("task-lora.pt", map_location="cpu"), strict=False
)
```

`strict=False` is intentional because the adapter checkpoint omits ordinary
base weights. Log `missing` and `unexpected`; unexpected `lora_` keys usually
mean that the layer path or rank/configuration differs.

For bias training, use the same policy at both points:

```python
lora.mark_only_lora_as_trainable(model, bias="lora_only")
torch.save(lora.lora_state_dict(model, bias="lora_only"), "task-lora-with-bias.pt")
```

## Fused QKV projection

```python
qkv = lora.MergedLinear(
    hidden_size,
    3 * hidden_size,
    r=8,
    lora_alpha=16,
    enable_lora=[True, False, True],
    fan_in_fan_out=True,
    merge_weights=False,
)
```

This adapts Q and V while leaving K as an ordinary slice. If the host model
uses three separate projections, use `lora.Linear` only on the desired ones.
If it stores a transposed Conv1D-like weight, preserve `fan_in_fan_out=True`.

## Merge timing

With the default `merge_weights=True`, `model.eval()` changes the layer's
`merged` flag and adds the low-rank update to the base weight for inference.
`model.train()` removes that update before training resumes. Do not save a base
checkpoint while making assumptions about whether a layer is already merged;
use one consistent mode and verify `layer.merged` in a smoke test.

## Minimal verification

Run `python scripts/check_lora_core.py --json` from the generated skill root.
A successful result should show:

- dense, embedding, fused-linear, and convolution output shapes;
- `merged_after_eval: true` and `unmerged_after_train: true`;
- only LoRA parameters (plus the requested bias policy) marked trainable; and
- only `lora_A`/`lora_B` keys in the default adapter state.
