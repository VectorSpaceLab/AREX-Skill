# FCOS Checkpoints and Solver State

## Loading weights

Training and evaluation use `DetectronCheckpointer` with `cfg.MODEL.WEIGHT`. The value may point to a local checkpoint, a model-catalog URL, or a pretrained FCOS weight. Make the weight path explicit in commands when reproducibility matters.

## Output directory

`OUTPUT_DIR` controls logs and checkpoint output. During evaluation, inference outputs are placed under `OUTPUT_DIR/inference/<dataset_name>`.

## Removing solver state

FCOS includes a small utility that removes `optimizer`, `scheduler`, and `iteration` keys from a checkpoint. Use the bundled safer adaptation:

```bash
python sub-skills/training-evaluation/scripts/remove_solver_states.py model.pth --output model_wo_solver_states.pth
```

By default the helper requires all three solver keys to exist; pass `--ignore-missing` for checkpoint formats that omit one of them.

## Publishing or sharing checkpoints

- Strip optimizer/scheduler state when the user only needs inference weights.
- Preserve the original checkpoint before writing derived files.
- Do not bundle large checkpoints in the skill.
