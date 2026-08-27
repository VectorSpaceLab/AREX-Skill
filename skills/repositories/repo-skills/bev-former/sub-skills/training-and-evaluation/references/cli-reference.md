# CLI reference

The bundled scripts only print commands.

## `scripts/bevformer_train_command.py`

Usage:
```bash
python scripts/bevformer_train_command.py --config <config.py> [options]
```

Flags:
- `--config` required. BEVFormer config path.
- `--gpus` launcher world size; defaults to 1.
- `--work-dir` overrides the config work directory.
- `--port` master port for distributed launch. Defaults to 28509 for standard training and 28508 when `--fp16` is set.
- `--fp16` switches the entrypoint to `tools/fp16/train.py`.
- `--resume-from` adds a resume checkpoint if you want to continue a run.
- `--seed` forwards a seed to `tools/train.py` or `tools/fp16/train.py`.
- `--no-validate` skips validation during training.
- `--autoscale-lr` forwards the linear LR scaling flag.
- `--cfg-options` appends OpenMMLab config overrides as `KEY=VALUE` tokens.

Default command shape:
```bash
python -m torch.distributed.launch --nproc_per_node=<gpus> --master_port=<port> \
  tools/train.py <config> --launcher pytorch --deterministic ...
```

When `--fp16` is set, the script swaps in `tools/fp16/train.py`.

## `scripts/bevformer_eval_command.py`

Usage:
```bash
python scripts/bevformer_eval_command.py --config <config.py> --checkpoint <ckpt.pth> [options]
```

Flags:
- `--config` required. BEVFormer config path.
- `--checkpoint` required. Evaluation checkpoint path.
- `--gpus` launcher world size; defaults to 1.
- `--port` master port for distributed launch. Defaults to 29503.
- `--eval` explicit evaluation metrics, such as `bbox`.
- `--format-only` formats results without evaluation.
- `--show` requests visual output.
- `--show-dir` writes visual output to a directory.
- `--out` saves raw outputs to a pickle file.
- `--gpu-collect` switches result gathering to GPU collection.
- `--tmpdir` sets the temporary directory for CPU collection.
- `--cfg-options` appends config overrides.
- `--eval-options` forwards extra kwargs to `dataset.evaluate()`.

Default command shape:
```bash
python -m torch.distributed.launch --nproc_per_node=<gpus> --master_port=<port> \
  tools/test.py <config> <checkpoint> --launcher pytorch --eval bbox ...
```

If no operation flag is supplied, the composer falls back to `--eval bbox` to mirror the repo shell helper. Collection flags such as `--gpu-collect` and `--tmpdir` do not count as operations.

## `--cfg-options` examples
- `data.samples_per_gpu=1`
- `work_dir=work_dirs/bevformer_tiny`
- `model.pts_bbox_head.transformer.encoder.num_layers=3`

## Important differences from the source shell scripts
- The bundled scripts print one deterministic command string and do not execute it.
- The repo shell scripts hard-code `--eval bbox` for testing; the eval composer only defaults to that when no other operation flag is provided.
- The repo shell scripts use `torch.distributed.launch`; the bundled scripts preserve that launcher shape.
