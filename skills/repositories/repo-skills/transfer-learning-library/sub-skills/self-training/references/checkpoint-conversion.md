# Checkpoint Conversion for Self-Training Workflows

Some TLLib SSL workflows start from an unsupervised MoCo-style checkpoint, then fine-tune with ERM, Pseudo Label, UDA, FixMatch/FlexMatch, Self-Tuning, or DST. This reference describes the conversion pattern without copying benchmark scripts or assuming any local checkout layout.

For downstream fine-tuning decisions after conversion, also see [task-generalization checkpoint conversion](../../task-generalization/references/checkpoint-conversion.md).

## When conversion is needed

Use this conversion when a checkpoint has keys like:

```text
state_dict["module.encoder_q.conv1.weight"]
state_dict["module.encoder_q.layer1.0.conv1.weight"]
state_dict["module.encoder_q.fc.weight"]
state_dict["module.encoder_q.fc.bias"]
```

TLLib model factories usually expect a normal backbone state dict without the `module.encoder_q.` prefix. SSL examples that use a `--pretrained-backbone` style option expect the backbone weights separately from the MoCo projection/classifier `fc` weights.

Do **not** convert if the checkpoint is already a plain torchvision/TLLib backbone state dict or if its architecture/classifier layout is unknown.

## Conversion logic

1. Load the checkpoint on CPU.
2. Read `checkpoint["state_dict"]` if present; otherwise confirm the whole object is already a state dict.
3. Keep only keys that start with `module.encoder_q.`.
4. Strip that prefix.
5. Split stripped keys:
   - keys starting with `fc` go to an optional `fc` state dict;
   - all other keys go to the pretrained backbone state dict.
6. Save the two resulting state dicts separately.

Self-contained Python function:

```python
from pathlib import Path
import torch


def convert_moco_encoder_q(input_path, backbone_output_path, fc_output_path=None):
    checkpoint = torch.load(str(input_path), map_location="cpu")
    state = checkpoint.get("state_dict", checkpoint)
    if not isinstance(state, dict):
        raise TypeError("checkpoint does not contain a state_dict-like mapping")

    backbone = {}
    fc = {}
    prefix = "module.encoder_q."
    for key, value in state.items():
        if not key.startswith(prefix):
            continue
        stripped = key[len(prefix):]
        if stripped.startswith("fc"):
            fc[stripped] = value
        else:
            backbone[stripped] = value

    if not backbone:
        raise ValueError("no module.encoder_q.* backbone keys found; not a supported MoCo-style checkpoint")

    torch.save(backbone, str(backbone_output_path))
    if fc_output_path is not None:
        torch.save(fc, str(fc_output_path))
    return {"backbone_keys": len(backbone), "fc_keys": len(fc)}
```

## Safe dry-run checks

Before using a converted checkpoint in training:

```python
summary = convert_moco_encoder_q("moco_checkpoint.pth.tar", "moco_backbone.pth", "moco_fc.pth")
print(summary)

backbone_state = torch.load("moco_backbone.pth", map_location="cpu")
print(len(backbone_state), list(backbone_state)[:5])
```

Then instantiate the intended backbone and load non-strictly first to inspect compatibility:

```python
missing, unexpected = backbone.load_state_dict(backbone_state, strict=False)
print("missing", missing)
print("unexpected", unexpected)
```

Only switch to strict loading if architecture, key names, and expected classifier removal are all clear.

## Expected outputs

- `backbone` checkpoint: convolutional/residual backbone keys with no `module.encoder_q.` prefix and no `fc.*` keys.
- Optional `fc` checkpoint: `fc.weight`, `fc.bias`, or similar classifier/projection-head keys. These are not usually loaded into a new classification head with a different `num_classes`.

## Common incompatibilities

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No converted keys | Checkpoint is not MoCo-style, lacks `state_dict`, or uses another prefix | Inspect top-level keys and first state-dict keys; adapt the prefix only if the source is trusted. |
| Many unexpected keys | Architecture mismatch or prefix not fully stripped | Confirm backbone factory and strip exactly one `module.encoder_q.` prefix. |
| Many missing keys around `fc` | Expected when the target task has a new classifier head | Load backbone only; initialize the target classifier head normally. |
| Shape mismatch in early conv or layers | Different backbone family or input-channel stem | Use the matching architecture or discard incompatible layers intentionally. |
| Checkpoint loads on one device but not another | Saved CUDA tensors or unavailable device | Always load with `map_location="cpu"`, then move the model to the desired device. |
| Converted file works for ERM but not Self-Tuning/DST | Wrapper classifier expects `backbone.out_features` and a compatible pooling/head setup | Verify the backbone through [vision-data-models](../../vision-data-models/SKILL.md), then wrap it with the correct SSL classifier. |

## How to use in self-training

After conversion:

1. Create the backbone architecture that matches the MoCo checkpoint.
2. Load the converted backbone weights.
3. Attach the SSL classifier/head for the current task and class count.
4. Choose the SSL method in [self-training workflows](self-training-workflows.md).
5. Treat the converted checkpoint as external provenance; record its source, architecture, and conversion summary in experiment logs.

Do not assume a converted MoCo `fc` head is useful for the target task. Most SSL/TLLib workflows initialize a new classifier head for the target class count.

## Verification boundary

The bundled self-training smoke script does not convert external checkpoints. It verifies the API pieces used after conversion. Conversion should be validated on a small checkpoint dry run before full training.
