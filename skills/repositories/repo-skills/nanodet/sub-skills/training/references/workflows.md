# Training and evaluation workflows

## Training flow

1. Prepare and validate the config in `dataset-config`.
2. Confirm that `cfg.model.arch.head.num_classes == len(cfg.class_names)`.
3. Launch the training script with the desired config.
4. Watch `save_dir` for:
   - `logs-<timestamp>/logs.txt`
   - `logs-<timestamp>/train_cfg.yml`
   - `model_last.ckpt`
   - `model_best/model_best.ckpt`
   - `model_best/nanodet_model_best.pth`
   - `model_best/eval_results.txt`

## Validation / test flow

- The test script loads a checkpoint and runs the evaluator on the val dataset.
- The script accepts `val` or `test` as the task name.
- CPU mode is available when the config uses `device.gpu_ids: -1` or the skill-owned wrapper overrides to CPU.

## Checkpoint flow

| File | Meaning |
| --- | --- |
| `model_last.ckpt` | Most recent checkpoint saved at the end of an epoch |
| `model_best/model_best.ckpt` | Best checkpoint by the evaluator save key |
| `model_best/nanodet_model_best.pth` | Serialized state dict for the best model |
| legacy `.pth` checkpoint | Old-format checkpoint that should be converted before reuse |

## Trainer behavior worth knowing

- `TrainingTask` owns the forward, train, validation, and test hooks.
- `NanoDetLightningLogger` writes TensorBoard and text logs.
- `ExpMovingAverager` is optional and is enabled by the `model.weight_averager` block.
- `build_optimizer` can apply param-wise learning-rate and decay multipliers.
- `set_multi_processing` controls multiprocessing, OpenCV thread count, and `OMP_NUM_THREADS` / `MKL_NUM_THREADS`.

## Practical command pattern

```bash
python sub-skills/training/scripts/train.py --config path/to/config.yml
python sub-skills/training/scripts/test.py --config path/to/config.yml --model path/to/model.ckpt --task val
python sub-skills/training/scripts/convert_old_checkpoint.py --file_path old.pth --out_path new.ckpt
```

## Notes

- The repo's CPU branch is available when `device.gpu_ids` is `-1`.
- Training with a different backbone or head usually means editing only the config, not the trainer code.
- If a model build step unexpectedly downloads a pretrained backbone, cache it or disable pretrained loading when offline.
