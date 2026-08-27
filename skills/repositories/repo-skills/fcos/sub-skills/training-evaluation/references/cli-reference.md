# FCOS Training/Evaluation CLI Reference

## Training entry behavior

The training entry accepts:

- `--config-file FILE`: YAML config to merge into the base `cfg`.
- `--local_rank INT`: GPU index used by distributed launch.
- `--skip-test`: skip final evaluation after training.
- `opts`: remaining tokens are passed to `cfg.merge_from_list`, so use pairs such as `OUTPUT_DIR out MODEL.WEIGHT path/to/model.pth`.

The script reads `WORLD_SIZE` to decide whether distributed mode is active. In distributed mode it sets the CUDA device to `local_rank`, initializes `torch.distributed` with `backend="nccl"`, wraps the model in `DistributedDataParallel`, and synchronizes between evaluation datasets.

## Evaluation entry behavior

The evaluation entry accepts:

- `--config-file FILE`
- `--local_rank INT`
- `opts` pairs for config overrides

It builds the model, loads `cfg.MODEL.WEIGHT`, builds validation data loaders from `cfg.DATASETS.TEST`, and writes inference outputs under `OUTPUT_DIR/inference/<dataset_name>` when `OUTPUT_DIR` is set.

## Important overrides

| Override | Use |
| --- | --- |
| `MODEL.WEIGHT path/to/model.pth` | Select trained/pretrained weights for train resume or eval. |
| `OUTPUT_DIR path/to/output` | Store logs, checkpoints, and inference outputs. |
| `TEST.IMS_PER_BATCH 1` | Reduce evaluation batch size to mitigate OOM. |
| `DATALOADER.NUM_WORKERS 2` | Control loader processes; lower for constrained hosts. |
| `SOLVER.IMS_PER_BATCH 16` | Global training batch size in config; not automatically tied to GPU count. |
| `INPUT.MIN_SIZE_TEST 800` | Evaluation resize short side; lower for ONNX/test OOM triage. |

## Command builders

Generate a command without starting a job:

```bash
python sub-skills/training-evaluation/scripts/build_train_command.py --config-file configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --gpus 8 --output-dir training_dir/fcos_imprv_R_50_FPN_1x --override DATALOADER.NUM_WORKERS 2
```

```bash
python sub-skills/training-evaluation/scripts/build_eval_command.py --config-file configs/fcos/fcos_imprv_R_50_FPN_1x.yaml --weights FCOS_imprv_R_50_FPN_1x.pth --ims-per-batch 1
```
