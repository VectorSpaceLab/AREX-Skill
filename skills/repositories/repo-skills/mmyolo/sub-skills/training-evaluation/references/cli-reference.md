# MMYOLO training/testing CLI reference

This reference distills MMYOLO's train/test command behavior into package-level OpenMIM commands and bundled helper usage. It is for constructing commands; it is not an instruction to launch expensive jobs.

## Preferred package commands

Use OpenMIM when MMYOLO is installed as a package. This avoids depending on a source checkout script path:

```shell
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR
```

Use `--gpus 0` only after confirming the selected config and operation support CPU execution. Use `--gpus N --launcher pytorch --port PORT` for distributed PyTorch jobs, and Slurm options only on an actual Slurm cluster.

## Training options

MMYOLO's training command accepts these script-level arguments through MIM after the package/config arguments:

| Argument | Meaning | Operating notes |
| --- | --- | --- |
| `CONFIG` | Positional train config file path. | Usually a `.py` MMEngine config. Confirm dataset/model edits before launching. |
| `--work-dir WORK_DIR` | Directory for logs, checkpoints, copied config, and run artifacts. | CLI value overrides `work_dir` in config. If absent and config lacks `work_dir`, MMYOLO derives `./work_dirs/<config-basename>`. |
| `--amp` | Enable automatic mixed precision at runtime. | If config `optim_wrapper.type` is `OptimWrapper`, it is changed to `AmpOptimWrapper` with dynamic loss scale. If already `AmpOptimWrapper`, MMYOLO warns. If another wrapper type is used, MMYOLO asserts. |
| `--resume` | Optional resume flag. | With no value, MMYOLO auto-resumes latest checkpoint from the work directory. With a path, MMYOLO sets `cfg.resume=True` and `cfg.load_from=PATH`. |
| `--cfg-options KEY=VALUE ...` | Merge overrides into the config. | Uses MMEngine `DictAction`; quote list/tuple values, avoid spaces inside values, and use dotted keys for nested fields. |
| `--launcher none\|pytorch\|slurm\|mpi` | Distributed/job launcher selector. | Default script behavior is `none`; MIM also has its own `--launcher` option for package-level launch orchestration. |
| `--local_rank` / `--local-rank` | Local distributed rank. | Normally supplied by launchers; if `LOCAL_RANK` is not already set, MMYOLO sets it from this value. |

Examples:

```shell
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --resume
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --resume CHECKPOINT.pth
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --amp
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --cfg-options randomness.seed=2023 randomness.deterministic=True
```

For safe command construction without launching training, run the bundled helper [`../scripts/mmyolo_train_help.py`](../scripts/mmyolo_train_help.py).

## Testing and evaluation options

MMYOLO's testing command accepts these script-level arguments through MIM:

| Argument | Meaning | Operating notes |
| --- | --- | --- |
| `CONFIG` | Positional test/eval config path. | Must correspond to the checkpoint architecture and dataset/evaluator. |
| `--checkpoint CHECKPOINT` | Checkpoint file path. | MIM uses `--checkpoint`; the underlying MMYOLO test command receives the checkpoint and assigns it to `cfg.load_from`. |
| `--work-dir WORK_DIR` | Directory for evaluation metrics and run artifacts. | CLI value overrides config `work_dir`; otherwise MMYOLO derives a work directory from config basename if needed. |
| `--out RESULT.pkl` | Dump rich prediction results through `DumpResults`. | Must end with `.pkl` or `.pickle`; MMYOLO asserts otherwise. |
| `--json-prefix PREFIX` | Configure evaluator for JSON format-only output. | Pass a prefix without `.json`; MMYOLO sets evaluator `format_only=True` and `outfile_prefix=PREFIX`. Typical output is `PREFIX.bbox.json`. |
| `--tta` | Enable test-time augmentation. | Requires both `tta_model` and `tta_pipeline` in the config. TTA also disables incompatible nested `batch_shapes_cfg` in the test dataset path. |
| `--show` | Show prediction results interactively. | Avoid on headless machines; prefer `--show-dir`. |
| `--deploy` | Append `SwitchToDeployHook` before testing. | This is not ONNX/TensorRT export; route backend deployment to `deployment-conversion`. |
| `--show-dir DIR` | Save painted images. | Results are saved under the resolved work-dir/timestamp structure using this directory name. |
| `--wait-time SECONDS` | Display interval for `--show`. | Default is `2`. Mostly relevant for interactive visualization. |
| `--cfg-options KEY=VALUE ...` | Merge test-time config overrides. | Same quoting rules as training. Useful for score thresholds or evaluator overrides after config review. |
| `--launcher none\|pytorch\|slurm\|mpi` | Distributed/job launcher selector. | Default script behavior is `none`; MIM also has package-level launcher options. |

Examples:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --out predictions.pkl
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --json-prefix outputs/predictions
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --show-dir show_results
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --tta
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --deploy
```

For safe command construction without launching evaluation, run the bundled helper [`../scripts/mmyolo_test_help.py`](../scripts/mmyolo_test_help.py).

## Prediction-output request translation

| User request | Correct option(s) | Validate |
| --- | --- | --- |
| “Save a pickle I can inspect offline.” | `--out predictions.pkl` or `--out predictions.pickle` | File suffix must be `.pkl` or `.pickle`. |
| “Save COCO JSON for server submission.” | `--json-prefix outputs/submission` | Prefix should not include `.json`; expect generated JSON such as `outputs/submission.bbox.json`. |
| “Evaluate and save painted detections.” | `--show-dir show_results` | Prefer over `--show` in non-interactive/headless environments. |
| “Try TTA evaluation.” | `--tta` | Config must define `tta_model` and `tta_pipeline`. |
| “Test deploy-mode modules.” | `--deploy` | This only switches supported modules to deploy mode inside testing; it does not export backend artifacts. |
| “Need both pickle and JSON outputs.” | `--out predictions.pkl --json-prefix outputs/predictions` | Explain that JSON prefix triggers format-only evaluator behavior; verify the user still wants that mode. |

## `--cfg-options` examples

Use dotted keys and shell-safe quoting:

```shell
mim train mmyolo CONFIG.py --gpus 1 --cfg-options randomness.seed=2023 randomness.diff_rank_seed=True randomness.deterministic=True
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --cfg-options model.test_cfg.score_thr=0.25 model.test_cfg.nms.iou_threshold=0.45
mim train mmyolo CONFIG.py --gpus 1 --cfg-options train_cfg.max_epochs=40 default_hooks.checkpoint.interval=10
```

For lists or tuples, quote the whole value and avoid spaces inside it:

```shell
mim train mmyolo CONFIG.py --gpus 1 --cfg-options "train_pipeline.1.scale=(640,640)"
mim train mmyolo CONFIG.py --gpus 1 --cfg-options 'visualizer.vis_backends=[dict(type="LocalVisBackend")]'
```

When the override is more than a small scalar, route to `config-customization` and write a config file instead of relying on complex shell quoting.

## Distributed and Slurm patterns

Prefer MIM launcher options instead of checkout-local shell wrappers:

```shell
CUDA_VISIBLE_DEVICES=0,1,2,3 mim train mmyolo CONFIG.py --gpus 4 --launcher pytorch --port 29500 --work-dir WORK_DIR
CUDA_VISIBLE_DEVICES=0,1,2,3 mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 4 --launcher pytorch --port 29500 --work-dir WORK_DIR
mim train mmyolo CONFIG.py --launcher slurm --gpus 8 --gpus-per-node 8 --partition PARTITION --work-dir WORK_DIR
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --launcher slurm --gpus 8 --gpus-per-node 8 --partition PARTITION --work-dir WORK_DIR
```

Distributed environment knobs:

- `CUDA_VISIBLE_DEVICES` selects visible GPUs.
- `--port` is the PyTorch master port; make it unique for concurrent jobs.
- Multi-node jobs need launcher-specific master address, node rank, and cluster settings.
- Slurm patterns additionally depend on partition/account/GPU resource policy; do not invent those values.

## OpenMIM command discovery

Use these safe package-command discovery checks when the active environment is uncertain:

```shell
mim train mmyolo --help
mim test mmyolo --help
mim run mmyolo --help
```

If MIM cannot find MMYOLO package commands, repair the MMYOLO installation or use a package/version that includes MIM metadata before relying on package-level training/testing guidance.
