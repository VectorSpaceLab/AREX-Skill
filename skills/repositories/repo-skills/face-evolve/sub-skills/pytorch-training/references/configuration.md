# PyTorch Configuration Reference

`config.py` contains a `configurations` dictionary. The stable training flow reads `cfg = configurations[1]` and then copies individual values into local variables before building data loaders, models, losses, optimizer, validation, TensorBoard logging, and checkpoints.

## Safe editing rules

- Edit only the active configuration dictionary unless the user asks for multiple presets.
- Replace machine-specific path strings with user-provided project paths. Do not leave placeholder roots in a real training config.
- Ensure `DATA_ROOT`, `MODEL_ROOT`, and `LOG_ROOT` exist or are created by the user's workflow before training.
- Use empty resume paths for scratch training; use actual `.pth` files for both backbone and head when resuming.
- Keep `INPUT_SIZE` square and supported (`[112, 112]` or `[224, 224]`). Most face.evoLVe validation and model-zoo expectations are for 112.
- Keep `EMBEDDING_SIZE=512` unless you are deliberately modifying both backbone output layers and heads.
- For CPU inspection, set `DEVICE` to CPU, `MULTI_GPU=False`, and heads' `device_id` to `None` in any construction code.
- For real multi-GPU training, make `DEVICE`, `MULTI_GPU`, and `GPU_ID` agree with actual CUDA visibility.
- After changing `BACKBONE_NAME`, `HEAD_NAME`, `LOSS_NAME`, `INPUT_SIZE`, or `EMBEDDING_SIZE`, run the bundled component inspector before full training.

## Key table

| Key | Stable meaning | Editing guidance |
| --- | --- | --- |
| `SEED` | Torch random seed for reproducibility. | Keep fixed for reproducible experiments; set explicitly in reports. |
| `DATA_ROOT` | Parent directory for `imgs/` training folder and validation bcolz arrays. | Must contain `imgs/` for training and validation roots if validation remains enabled. |
| `MODEL_ROOT` | Checkpoint output directory. | Create before training; keep separate from data. |
| `LOG_ROOT` | TensorBoardX log directory. | Create before training; use a fresh run directory when comparing experiments. |
| `BACKBONE_RESUME_ROOT` | Backbone checkpoint file path. | Use an actual file to resume. Use an empty value for scratch training. |
| `HEAD_RESUME_ROOT` | Head checkpoint file path. | Must match backbone checkpoint's class count and head type when resuming. |
| `BACKBONE_NAME` | Stable choices: `ResNet_50`, `ResNet_101`, `ResNet_152`, `IR_50`, `IR_101`, `IR_152`, `IR_SE_50`, `IR_SE_101`, `IR_SE_152`. | Prefer `IR_SE_50` or `IR_50` for ArcFace recipes unless the user requests a larger model. |
| `HEAD_NAME` | README choices: `Softmax`, `ArcFace`, `CosFace`, `SphereFace`, `Am_softmax`. | Checked training dictionary omits `Softmax`; add it if selected. Experimental heads need source repair. |
| `LOSS_NAME` | `Focal` or `Softmax`. | Use `Focal` with margin heads for model-zoo-like recipes; `Softmax` means cross entropy, not the `Softmax` head. |
| `INPUT_SIZE` | `[112, 112]` or `[224, 224]`. | Use `[112, 112]` unless all preprocessing and validation expectations are intentionally changed. |
| `RGB_MEAN`, `RGB_STD` | Normalization constants. | Defaults `[0.5, 0.5, 0.5]` map image tensors to roughly `[-1, 1]`; keep aligned with feature extraction. |
| `EMBEDDING_SIZE` | Face embedding dimension. | Stable backbones emit 512; changing requires source edits. |
| `BATCH_SIZE` | Training mini-batch size. | Large for GPU training; at least 2 for BatchNorm training. Tiny data may need `DROP_LAST=False` plus source repairs. |
| `DROP_LAST` | Drop final short training batch. | Keep `True` for large real training; reconsider only for tiny fixtures. |
| `LR` | Initial learning rate after warm-up. | Stable default is `0.1`; tune with batch size and optimizer changes. |
| `NUM_EPOCH` | Total epochs. First `NUM_EPOCH // 25` epochs are warm-up. | Default 125. Tiny tests should not use the full value. |
| `WEIGHT_DECAY` | Weight decay for non-BatchNorm parameters. | Default `5e-4`; training code excludes BatchNorm parameters. |
| `MOMENTUM` | SGD momentum. | Default `0.9`. |
| `STAGES` | Epoch indices where LR is divided by 10. | Default `[35, 65, 95]`; must be less than `NUM_EPOCH`. |
| `DEVICE` | Torch device used by training. | For CUDA training, usually first visible GPU; for CPU checks, CPU. |
| `MULTI_GPU` | Whether to wrap backbone in DataParallel. | Must be `False` for CPU and single-device smoke checks. |
| `GPU_ID` | Device IDs used by DataParallel and model-parallel heads. | Use IDs relative to CUDA visibility. For single visible GPU, use `[0]` or disable multi-GPU. |
| `PIN_MEMORY` | DataLoader pinned-memory flag. | Useful for CUDA; optional for CPU. |
| `NUM_WORKERS` | DataLoader workers. | Increase for real training if storage/CPU permit; keep low for debugging. |

## Common presets

### Model-zoo-like PyTorch recipe

Use when the user asks for `IR_SE_50 + ArcFace + Focal`:

```python
BACKBONE_NAME = 'IR_SE_50'
HEAD_NAME = 'ArcFace'
LOSS_NAME = 'Focal'
INPUT_SIZE = [112, 112]
EMBEDDING_SIZE = 512
RGB_MEAN = [0.5, 0.5, 0.5]
RGB_STD = [0.5, 0.5, 0.5]
```

Then set data, checkpoint, log, and GPU fields from the user's environment.

### CPU component inspection preset

Use for construction/signature/shape checks only, not full training:

```python
BACKBONE_NAME = 'IR_50'
HEAD_NAME = 'ArcFace'
LOSS_NAME = 'Focal'
INPUT_SIZE = [112, 112]
EMBEDDING_SIZE = 512
BATCH_SIZE = 2
DEVICE = torch.device('cpu')
MULTI_GPU = False
GPU_ID = []
PIN_MEMORY = False
NUM_WORKERS = 0
```

Prefer the bundled inspector script rather than editing training code for this case.

### Tiny one-epoch training fixture preset

Only use this when the user explicitly supplies a tiny ImageFolder fixture and wants to test the training loop itself. In addition to config changes, repair these source assumptions first:

- `DISP_FREQ` should be at least 1.
- Top-k accuracy should not request `top5` when `NUM_CLASS < 5`.
- Validation should be disabled or restricted to supplied tiny validation arrays.
- `DROP_LAST` should not drop every batch.
- Known syntax/import issues must be fixed.

Suggested starting values:

```python
NUM_EPOCH = 1
BATCH_SIZE = 2
DROP_LAST = False
LR = 0.01
STAGES = []
MULTI_GPU = False
DEVICE = torch.device('cpu')
```

This is a source-repair/debugging exercise, not a performance benchmark.

## Choosing backbones, heads, and losses

- `IR_SE_*` usually offers stronger accuracy than plain `IR_*` because squeeze-and-excitation blocks recalibrate channels.
- `IR_50` and `IR_SE_50` are the practical first choices; 101/152 variants are heavier.
- `ResNet_*` variants are stable but have different output spatial assumptions and parameter-splitting rules.
- Stable margin heads (`ArcFace`, `CosFace`, `SphereFace`, `Am_softmax`) all produce logits for a separate classification loss.
- `Softmax` can mean either a head class or the config value for cross-entropy loss. Be explicit in code reviews.
- Experimental heads in the source are not production-ready without import/device/return-type repairs.

## Validation configuration implications

Leaving validation enabled means `DATA_ROOT` must hold all seven expected bcolz validation datasets. If the user only wants training loss or has no validation data:

1. Remove or guard the `get_val_data(DATA_ROOT)` call.
2. Remove or guard each `perform_val` and `buffer_val` call.
3. Keep checkpoint saving independent of validation.
4. Document that no LFW/CFP/AgeDB/CALFW/CPLFW/VGGFace2-FP metric was produced.

If the user supplies a subset, create a subset list and loop over only present entries rather than duplicating seven nearly identical blocks.

## Resume and checkpoint compatibility

A valid resume pair must agree on:

- Backbone class and `INPUT_SIZE`.
- Head class and `NUM_CLASS`/training identity count.
- `EMBEDDING_SIZE`.
- Whether state keys include a `module.` prefix. The stable save path stores `BACKBONE.module.state_dict()` when multi-GPU, so the saved backbone usually does not include a `module.` prefix.

Load checkpoints before wrapping the backbone in `DataParallel`, as the stable flow does. If only a backbone checkpoint is available and the user wants fine-tuning with a new head, load only the backbone in a custom repaired flow and initialize a new head for the new class count.
