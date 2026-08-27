# Export and checkpoint utilities

AdelaiDet includes small checkpoint utilities plus a heavier ONNX exporter. Use this file for checkpoint/state-dict tasks; use `onnx-export.md` for graph export.

## FCOS official weight conversion

The source FCOS converter renames ResNet/FPN/proposal-generator keys from official FCOS naming into Detectron2/AdelaiDet naming. Use the skill-owned script on a copy:

```bash
python scripts/convert_fcos_weight.py \
  --model /path/to/fcos_official.pth \
  --output /path/to/fcos_converted.pth
```

Transform examples:

- `module.` prefix removed.
- `body` → `bottom_up`.
- `.layer1` → `.res2`, `.layer2` → `.res3`, `.layer3` → `.res4`, `.layer4` → `.res5`.
- `downsample.0` → `shortcut`; `downsample.1` → `shortcut.norm`.
- `bn1/bn2/bn3` → `conv1.norm/conv2.norm/conv3.norm`.
- `fpn_inner*` and `fpn_layer*` → Detectron2 FPN lateral/output names.
- `rpn` → `proposal_generator`; `head` → `fcos_head`.

The script expects the input checkpoint to contain a top-level `model` state dict unless `--state-dict-key` is changed.

## BlendMask centerness key rename

Some BlendMask weights use `centerness` while the code expects `ctrness`:

```bash
python scripts/rename_blendmask_weights.py \
  --model /path/to/blendmask.pth \
  --output /path/to/blendmask_renamed.pth
```

The script preserves whether the input had a top-level `model` key unless `--save-model-only` is requested.

## Strip optimizer/training state

Use this when a training checkpoint is too large or an inference/demo flow only needs model weights:

```bash
python scripts/strip_checkpoint_optimizer.py \
  --input output/run/model_final.pth \
  --output output/run/model_final_model_only.pth
```

By default it extracts the top-level `model` key. Use `--state-dict-key` if the checkpoint stores weights under a different key.

## Safety notes

- Always write to a new output path; avoid in-place overwrite unless you intentionally pass the same path.
- Run conversion on CPU (`map_location=cpu`) unless you need GPU tensors.
- Check a few keys before and after conversion:

```bash
python - <<'PY'
import torch
ckpt = torch.load('/path/to/file.pth', map_location='cpu')
state = ckpt.get('model', ckpt)
print(list(state)[:20])
PY
```

- If converted weights still mismatch, verify the target YAML model family and architecture before assuming the converter is wrong.
