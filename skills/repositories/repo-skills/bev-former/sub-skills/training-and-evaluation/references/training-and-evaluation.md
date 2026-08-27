# Training and evaluation

This sub-skill only composes commands. It does not execute training or evaluation.

## What the repo supports
- `tools/dist_train.sh` wraps `tools/train.py` through `python -m torch.distributed.launch`.
- `tools/dist_test.sh` wraps `tools/test.py` and hard-codes `--eval bbox`.
- `tools/fp16/dist_train.sh` wraps `tools/fp16/train.py`.
- `tools/test.py` rejects non-distributed evaluation (`assert False` in the non-distributed branch).

## Canonical command shapes

### Standard distributed training
```bash
python -m torch.distributed.launch --nproc_per_node=<gpus> --master_port=<port> \
  tools/train.py <config> --launcher pytorch --deterministic \
  [--work-dir <dir>] [--resume-from <ckpt>] [--cfg-options key=value ...]
```

### FP16 training
```bash
python -m torch.distributed.launch --nproc_per_node=<gpus> --master_port=<port> \
  tools/fp16/train.py <fp16-config> --launcher pytorch --deterministic \
  [--work-dir <dir>] [--resume-from <ckpt>] [--cfg-options key=value ...]
```

### Distributed evaluation
```bash
python -m torch.distributed.launch --nproc_per_node=<gpus> --master_port=<port> \
  tools/test.py <config> <checkpoint> --launcher pytorch \
  [--eval bbox ...] [--format-only] [--show] [--show-dir <dir>] \
  [--out <result.pkl>] [--gpu-collect] [--tmpdir <dir>] \
  [--cfg-options key=value ...] [--eval-options key=value ...]
```

## Flag semantics that matter here
- `--work-dir`: CLI value wins over a config file `work_dir`; otherwise the repo falls back to `./work_dirs/<config_basename>`.
- `--resume-from`: only takes effect when the file exists; otherwise it is ignored.
- `load_from`: initializes weights; it is not the same thing as `resume_from` and is not the eval checkpoint.
- `--cfg-options`: merges config overrides; `--options` is deprecated.
- `--gpus`: in the bundled composers, this controls the launcher world size, not `tools/train.py --gpus`.
- `--launcher pytorch`: this is the expected distributed path for BEVFormer commands in this repo.
- `--eval bbox`: the repo shell helper uses bbox by default.
- `--format-only` and `--eval` cannot be combined.
- `--out` must end in `.pkl` or `.pickle`.
- `--show-dir` and `--show` are evaluation-time visualization controls, not training controls.
- `--gpu-collect` and `--tmpdir` only matter for multi-worker result collection during eval.
- `--eval-options` forwards extra kwargs to `dataset.evaluate()`.

## Preconditions and gates
- Use the legacy OpenMMLab stack documented in `docs/install.md`.
- BEVFormer configs expect `plugin=True` and `plugin_dir='projects/mmdet3d_plugin/'`.
- CUDA and NCCL are required for distributed launch.
- nuScenes data and temporal info files are required for real train/eval runs.
- Evaluation needs a real checkpoint from a model zoo release or a finished training run.
- BEVFormerV2 configs may require the extra DD3D/Detectron2 stack described in installation notes.
- If a failure is about missing data layout or conversion output, route it to `dataset-preparation` instead of trying to fix it here.

## FP16 route
- Use the `projects/configs/bevformer_fp16/` family with `tools/fp16/train.py`.
- The fp16 config carries `fp16=dict(loss_scale=512.)` and `EpochBasedRunner_video`.
- Do not pair `--fp16` with a non-fp16 config unless you know the config already defines the same fp16 runner blocks.

## Checkpoint handling
- For training, `load_from` seeds initialization from a model zoo weight.
- For evaluation, pass `--checkpoint`; the composer should never invent a checkpoint path.
- If a checkpoint was fused or republished, recheck the file extension and intended use before composing the command.
- The docs note that 1 GPU eval may sometimes score slightly higher because video is less likely to be truncated, but this repo still expects distributed launch syntax.
