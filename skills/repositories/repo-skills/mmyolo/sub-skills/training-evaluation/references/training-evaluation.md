# MMYOLO training and evaluation workflows

This reference gives side-effect-aware OpenMIM command recipes for MMYOLO training and testing. The commands below are **launch commands**; review them with the bundled helpers first when possible.

## Preflight checklist before any train/test launch

- Confirm the config is the final, merged configuration for the intended dataset and model family.
- Confirm dataset files referenced by the config exist and match the evaluator type.
- For training, choose a work directory that is unique for the run and has enough disk space for logs/checkpoints.
- For testing, confirm the checkpoint matches the model head/classes in the config.
- Decide CPU/GPU visibility before command construction. Use `--gpus 0` only for CPU-capable dry or evaluation paths; use `--gpus N` plus a selected `CUDA_VISIBLE_DEVICES` list for GPUs.
- For distributed jobs, choose a unique `--port`/master port for each concurrent job.
- For TTA, ensure the config defines both `tta_model` and `tta_pipeline`.
- For prediction dumps, decide whether the user needs a rich pickle file (`--out`) or COCO-style JSON prefix output (`--json-prefix`).
- Prefer output-to-directory options such as `--show-dir` on headless machines.

## Safe command builders

The bundled helpers print reviewed package-level commands and perform lightweight path/suffix checks. They never import MMYOLO and never call training or evaluation.

```shell
python scripts/mmyolo_train_help.py CONFIG.py --work-dir WORK_DIR --amp --resume
python scripts/mmyolo_test_help.py CONFIG.py CHECKPOINT.pth --out predictions.pkl --json-prefix outputs/predictions
```

Use `--skip-exists-check` only when drafting a template for paths that do not exist yet.

## Single-node training recipes

Preferred installed-package/OpenMIM style:

```shell
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --resume
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --resume CHECKPOINT.pth
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --amp
mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR --cfg-options randomness.seed=2023 randomness.deterministic=True
```

Notes:

- `--resume` without a value means auto-resume from the latest checkpoint in the resolved work directory.
- `--resume CHECKPOINT.pth` means resume optimizer/scheduler/model state from that explicit checkpoint.
- `--amp` rewrites an `OptimWrapper` config to `AmpOptimWrapper` at runtime. It warns if AMP is already enabled and asserts if the wrapper is neither `OptimWrapper` nor `AmpOptimWrapper`.
- Randomness can be overridden with `--cfg-options randomness.seed=... randomness.diff_rank_seed=True randomness.deterministic=True`.
- Config edits themselves are outside this sub-skill; route them to `config-customization`.

## Device and launcher patterns

Single selected GPU:

```shell
CUDA_VISIBLE_DEVICES=0 mim train mmyolo CONFIG.py --gpus 1 --work-dir WORK_DIR
CUDA_VISIBLE_DEVICES=0 mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR
```

CPU-only planning or CPU evaluation attempt:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 0 --work-dir WORK_DIR
```

CPU can handle parsing and many small checks. Full MMYOLO training/evaluation is normally GPU-oriented and may be impractically slow on CPU.

## Distributed launcher recipes

Prefer MIM launcher options; do not depend on checkout-local shell wrappers.

Single machine, multiple GPUs:

```shell
CUDA_VISIBLE_DEVICES=0,1,2,3 mim train mmyolo CONFIG.py --gpus 4 --launcher pytorch --port 29500 --work-dir WORK_DIR
CUDA_VISIBLE_DEVICES=0,1,2,3 mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 4 --launcher pytorch --port 29500 --work-dir WORK_DIR
```

Multi-node pattern:

```shell
# Node-specific variables such as master address and node rank depend on the launcher environment.
CUDA_VISIBLE_DEVICES=0,1,2,3 mim train mmyolo CONFIG.py --gpus 4 --launcher pytorch --port 29500 --work-dir WORK_DIR
```

Operating notes:

- MIM passes launcher settings to the MMYOLO train/test implementation.
- Select `CUDA_VISIBLE_DEVICES` before launch rather than relying on implicit device order.
- Use a different `--port` for each concurrent distributed job.
- Multi-node jobs need launcher-specific master address, node rank, and cluster settings; do not invent them.

## Slurm recipes

Slurm commands are site-specific because partition names, accounts, resource limits, `srun` flags, and GPU scheduling differ by cluster.

```shell
mim train mmyolo CONFIG.py --launcher slurm --partition PARTITION --gpus 8 --gpus-per-node 8 --cpus-per-task 5 --work-dir WORK_DIR
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --launcher slurm --partition PARTITION --gpus 8 --gpus-per-node 8 --cpus-per-task 5 --work-dir WORK_DIR
```

Do not claim a Slurm command is runnable until the user confirms partition/account/resource policy.

## Testing, metrics, prediction dumps, and painted outputs

Basic evaluation:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR
```

Save detailed pickle predictions while evaluating:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR --out predictions.pkl
```

Save COCO-style JSON output for external/server evaluation:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --json-prefix outputs/predictions
```

`--json-prefix outputs/predictions` writes files such as `outputs/predictions.bbox.json`. Pass a prefix, not a complete `.json` file name.

Save painted result images:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR --show-dir show_results
```

Use TTA only when the config has TTA definitions:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR --tta
```

Switch a model to deployment mode for testing its deploy-form modules, not for ONNX/TensorRT export:

```shell
mim test mmyolo CONFIG.py --checkpoint CHECKPOINT.pth --gpus 1 --work-dir WORK_DIR --deploy
```

For ONNX/TensorRT/RKNN export or backend inference, route to `deployment-conversion`.

## Visualization backends during training

MMYOLO uses MMEngine visualization backends. Treat backend configuration as a config-customization task, but keep these operating facts in mind:

- Local visualization is the default backend and writes visual/log artifacts under the work directory timestamp structure.
- TensorBoard needs the TensorBoard package and a config visualizer backend such as `TensorboardVisBackend`; view runs with `tensorboard --logdir WORK_DIR`.
- WandB needs the WandB package, a configured `WandbVisBackend`, and account/API-key login. Never paste credentials into shared prompts, logs, or skill files.
- Training metrics commonly include loss, learning rate, and validation metrics such as COCO bbox mAP when validation is configured.

## Log, scheduler, and confusion-matrix support

Loss/mAP curves through MMDetection analysis tooling, when the compatible package command exists:

```shell
mim run mmdet analyze_logs plot_curve LOG.json --keys loss_cls loss_bbox --legend loss_cls loss_bbox --out losses.pdf
mim run mmdet analyze_logs plot_curve LOG_A.json LOG_B.json --keys bbox_mAP --legend run_a run_b --eval-interval EVAL_INTERVAL
```

Average training speed:

```shell
mim run mmdet analyze_logs cal_train_time LOG.json
```

Scheduler visualization through MMYOLO's packaged MIM command, reference-only because it parses a full config and writes plots:

```shell
mim run mmyolo analysis_tools:vis_scheduler CONFIG.py --dataset-size NUM_IMAGES --ngpus NUM_GPUS --out-dir scheduler_plots --parameter lr --not-show
```

Confusion matrix from a pickle prediction file, reference-only because it needs matching config/data/prediction artifacts:

```shell
mim run mmyolo analysis_tools:confusion_matrix CONFIG.py predictions.pkl confusion_matrix_dir --score-thr 0.3 --tp-iou-thr 0.5
```

If log-analysis commands fail through MIM, verify installed command support and optional plotting dependencies before rerunning.
