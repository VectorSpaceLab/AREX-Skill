# Checkpoint Conversion for Task Adaptation

This reference describes the MoCo-style checkpoint conversion used before TLLib task-adaptation workflows such as Bi-Tuning. It is intentionally a recipe rather than a bundled executable because real checkpoints are large, externally downloaded, and easy to overwrite incorrectly.

## When conversion is needed

Use this recipe when a user has a self-supervised MoCo checkpoint whose state dict keys look like:

```text
module.encoder_q.conv1.weight
module.encoder_q.bn1.weight
module.encoder_q.layer1.0.conv1.weight
module.encoder_q.fc.weight
module.encoder_q.fc.bias
module.encoder_k....
```

TLLib task-adaptation fine-tuning expects a standard PyTorch-style backbone checkpoint and, for some workflows, a separate classifier-head checkpoint. The conversion keeps only `encoder_q`, strips its prefix, and splits `fc.*` keys into a head file.

## Safe preflight

Before converting:

1. Work on a copy of the downloaded checkpoint, not the only copy.
2. Use `map_location="cpu"` for inspection so the conversion does not require CUDA.
3. Inspect top-level keys. Common forms are:
   - `{"state_dict": {...}, ...}`
   - a raw state-dict mapping directly from key strings to tensors
4. Confirm that many keys start with `module.encoder_q.`. If not, stop and inspect the checkpoint family; SimCLR, BYOL, MAE, DINO, and supervised checkpoints use different prefixes.
5. Choose output paths that do not overwrite existing checkpoints.

## Conversion logic

Self-contained conversion algorithm:

```python
import torch

obj = torch.load(input_checkpoint, map_location="cpu")
state = obj["state_dict"] if isinstance(obj, dict) and "state_dict" in obj else obj

backbone = {}
head = {}
for key, value in state.items():
    if not key.startswith("module.encoder_q."):
        continue
    stripped = key.replace("module.encoder_q.", "", 1)
    if stripped.startswith("fc"):
        head[stripped] = value
    else:
        backbone[stripped] = value

torch.save(backbone, output_backbone_checkpoint)
torch.save(head, output_fc_checkpoint)
```

Expected outputs:

- `output_backbone_checkpoint`: keys such as `conv1.weight`, `bn1.weight`, `layer1.0.conv1.weight`, with no `module.encoder_q.` prefix and no `fc.*` keys.
- `output_fc_checkpoint`: only `fc.weight` and `fc.bias` when the source checkpoint has an `fc` layer.

## Post-conversion validation

After saving:

```python
backbone = torch.load(output_backbone_checkpoint, map_location="cpu")
fc = torch.load(output_fc_checkpoint, map_location="cpu")
assert backbone
assert all(not k.startswith("module.encoder_q.") for k in backbone)
assert all(not k.startswith("fc") for k in backbone)
assert all(k.startswith("fc") for k in fc)
```

Also verify by loading into the intended model with strictness appropriate to the workflow:

- Backbone load often uses `strict=False` if the target classifier head is newly initialized.
- Head load requires matching source classifier dimensions. Do not force-load a source `fc` into a target head with a different number of classes.
- Log missing/unexpected keys and decide whether each is expected before training.

## How this connects to TLLib task adaptation

Typical MoCo-pretrained fine-tuning flow:

1. Download or receive a MoCo checkpoint from the user.
2. Convert it into a backbone checkpoint and optional source `fc` checkpoint using the recipe above.
3. Build the target-task model and load the backbone checkpoint.
4. For Bi-Tuning or source-head methods, load/use the source `fc` only when source-class dimensions match the method's expectations.
5. Start the chosen task-adaptation workflow from [task-adaptation workflows](task-adaptation-workflows.md).

## Common key mismatch diagnoses

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No converted keys | Checkpoint is not MoCo `module.encoder_q.*` format | Inspect prefixes and design a new mapping before conversion |
| Every key is unexpected on load | Prefix was not stripped or model family differs | Strip the exact prefix and confirm architecture |
| Missing `fc.*` after conversion | Source checkpoint has no classifier head or uses another head name | Proceed with target head only, or map the actual head key deliberately |
| Shape mismatch in `fc.weight` | Source and target class counts differ | Do not load source FC into target classifier; initialize target head |
| Shape mismatch in residual layers | Backbone architecture differs from converted checkpoint | Use the matching backbone or obtain the correct checkpoint |
| CUDA deserialization error | Checkpoint was loaded without CPU mapping on a CPU-only process | Use `torch.load(path, map_location="cpu")` |

## Safety rules

- Do not run conversion in a script that overwrites inputs by default.
- Do not download external checkpoints automatically from a runtime helper; make the user provide paths explicitly.
- Do not claim MoCo conversion validates downstream accuracy. It only makes checkpoint keys loadable for fine-tuning.
- Keep converted checkpoints outside the runtime skill directory unless the user intentionally stores experiment artifacts there.
