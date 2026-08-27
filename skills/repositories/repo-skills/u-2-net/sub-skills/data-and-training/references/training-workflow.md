# Training Workflow

## Purpose

Use this reference to plan U-2-Net retraining safely. It distills the repository training script without making long training a default action.

## Source defaults

| Setting | Value |
| --- | --- |
| `model_name` | `u2net` by default; can be changed to `u2netp`. |
| Data root | `train_data/` |
| Image directory | `DUTS/DUTS-TR/DUTS-TR/im_aug/` |
| Label directory | `DUTS/DUTS-TR/DUTS-TR/gt_aug/` |
| Image extension | `.jpg` |
| Label extension | `.png` |
| Epoch count | `100000` |
| Train batch size | `12` |
| Transform chain | `RescaleT(320)`, `RandomCrop(288)`, `ToTensorLab(flag=0)` |
| Optimizer | Adam, learning rate `0.001`, betas `(0.9, 0.999)`, eps `1e-08`, no weight decay |
| Loss | BCE loss summed across fused output plus six side outputs |
| Checkpoint frequency | every `2000` iterations |

## Safe preparation sequence

1. Validate dataset stem pairing:

   ```bash
   python scripts/validate_training_layout.py --data-root TRAIN_DATA_ROOT --json
   ```

2. Inspect one representative image/mask pair:

   ```bash
   python scripts/inspect_data_pipeline.py --image IMAGE --label MASK --resize 320 --flag 0
   ```

3. Decide whether the user wants full `u2net` or small `u2netp` training.
4. Bound the first run. Do not start the 100000-epoch loop without a smaller smoke/debug plan and explicit user approval.
5. Confirm checkpoint output directory exists and has enough space.
6. Confirm CPU/GPU expectations. CPU can validate the code path on tiny data but is usually impractical for full training.

## Adapting to `u2netp`

If the user asks for a lightweight model:

- Change `model_name` consistently to `u2netp`.
- Instantiate `U2NETP(3,1)`.
- Save checkpoints under a `u2netp`-specific directory or filename to avoid mixing full and small checkpoints.
- Do not load full `u2net.pth` into the small architecture.

## Multi-side BCE loss

The source loss computes BCE for each of the seven outputs and sums all seven. The logged target loss is the fused output's BCE. If the user changes output handling, preserve this distinction when comparing training logs.

## When to stop and ask

Ask for explicit approval before:

- downloading DUTS or other large datasets;
- downloading pretrained weights;
- running full or long training;
- using all GPUs or a large batch size;
- overwriting checkpoint directories.
