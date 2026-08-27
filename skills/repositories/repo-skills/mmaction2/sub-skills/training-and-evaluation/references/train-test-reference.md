# Train/Test Reference

This reference distills MMAction2 1.x train/test behavior into safe command-planning decisions. It does not vendor MMAction2's full training runner. Use the bundled command builder to preview the documented command shape for a user workspace that provides MMAction2-compatible train/test entrypoints, configs, data, checkpoints, and compute.

## Minimal decision checklist

Before constructing a command, determine:

- workflow: train, test, distributed train/test, or Slurm train/test;
- config file to use and whether dataset/model/class-count edits are already present;
- checkpoint path: required for test, optional for train initialization via config `load_from`, and different from train resume;
- work directory for logs, checkpoints, metrics, dumps, and visualizations;
- device: CPU (`CUDA_VISIBLE_DEVICES=-1`), one GPU, selected visible GPUs, multi-node, or Slurm;
- optional flags: `--amp`, `--resume`, `--auto-scale-lr`, `--no-validate`, `--dump`, `--show-dir`, and `--cfg-options`.

Use [`../scripts/mmaction2_train_test_command_builder.py`](../scripts/mmaction2_train_test_command_builder.py) to preview a command string safely. The helper prints a command template only; it does not launch training, testing, downloads, or cluster jobs.

## Single-machine training

MMAction2's training entrypoint accepts a config path plus train arguments. Preview the command with:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --work-dir work_dirs/my_experiment
```

For CPU-only smoke/debug planning:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --cpu --work-dir work_dirs/cpu_smoke --cfg-option train_dataloader.batch_size=1 --cfg-option train_cfg.max_epochs=1
```

MMAction2 prefers an available GPU by default. Use CPU only for parser checks, tiny smoke runs, or when the model/pipeline is small enough; video pipelines and multi-view testing are commonly too slow or memory-heavy on CPU.

### Train flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| positional config | Train config file. | Must define dataloaders, model, loops, evaluator, optimizer wrapper, and runtime hooks. |
| `--work-dir WORK_DIR` | Directory for logs and checkpoints. | CLI value has priority; otherwise config `work_dir`; otherwise `work_dirs/<config_basename>`. |
| `--resume [RESUME]` | Resume training state. | With no value, auto-resume latest checkpoint in `work_dir`; with a path, resume from that checkpoint and set `load_from` to that path. |
| `--amp` | Enable automatic mixed precision. | Only supported when `optim_wrapper.type` is `OptimWrapper` or `AmpOptimWrapper`; it changes the wrapper to `AmpOptimWrapper` with dynamic loss scale. |
| `--no-validate` | Disable validation during training. | Not recommended unless the user explicitly wants no checkpoint evaluation. |
| `--auto-scale-lr` | Enable `cfg.auto_scale_lr.enable`. | Config must contain a valid `auto_scale_lr` section with a meaningful `base_batch_size`. |
| `--seed SEED` | Set random seed. | Used only when config does not already define `randomness`. |
| `--diff-rank-seed` | Use different seeds per distributed rank. | Relevant for distributed training. |
| `--deterministic` | Request deterministic CUDNN behavior. | Can reduce speed; not all operations are deterministic. |
| `--cfg-options KEY=VALUE ...` | Merge config overrides. | Quote lists/tuples and avoid spaces, e.g. `key="[a,b]"` or `key="[(a,b),(c,d)]"`. |
| `--launcher {none,pytorch,slurm,mpi}` | Distributed launcher. | Single-process commands use `none`; distributed wrappers set this automatically. |
| `--local-rank` / `--local_rank` | Rank injected by launcher. | Usually not set manually. |

### Common training recipes

Preview single GPU/default-device training:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --work-dir work_dirs/my_experiment
```

Preview AMP plus auto-scaled learning rate:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --amp --auto-scale-lr --work-dir work_dirs/amp_scaled
```

Preview latest-checkpoint resume in a work directory:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --work-dir work_dirs/my_experiment --resume
```

Preview a small/custom classification run:

```bash
python scripts/mmaction2_train_test_command_builder.py train --config CONFIG.py --work-dir work_dirs/tiny_custom \
  --cfg-option train_dataloader.batch_size=4 \
  --cfg-option train_cfg.max_epochs=10 \
  --cfg-option train_cfg.val_interval=1 \
  --cfg-option default_hooks.checkpoint.interval=1 \
  --cfg-option default_hooks.checkpoint.max_keep_ckpts=1 \
  --cfg-option model.cls_head.num_classes=2
```

Dataset-specific roots, annotation files, and prefix keys differ by dataset class (`video`, `img`, feature roots, AVA proposals, pose pickle, etc.). Route those details to the data/config sub-skill before finalizing overrides.

## Checkpoints, `load_from`, and resume

- `load_from` initializes weights before training or supplies the test checkpoint when the test entrypoint assigns `cfg.load_from`.
- `--resume` resumes the full training state: model weights, optimizer, scheduler, epoch/iteration counters, and runner metadata when present.
- Use `load_from` in the config for pretrained initialization on a new run; use `--resume` only when continuing the same run.
- Test commands always require a checkpoint argument. A remote checkpoint URL may be accepted by the runner, but it requires network access and should not be assumed available.

## Work directory outputs

For training, expect:

- a resolved `work_dir` from CLI, config, or `work_dirs/<config_basename>`;
- timestamped log subdirectories;
- periodic checkpoints such as `epoch_*.pth`;
- best-checkpoint folders or filenames keyed by evaluator output when checkpoint hooks save best metrics;
- validation metric lines during training if validation is enabled.

For testing, expect metric logs and optional artifacts under the selected work directory plus any explicit dump or visualization paths.

## Single-machine testing

Preview a test command with checkpoint:

```bash
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --work-dir work_dirs/eval_run
```

CPU-only preview:

```bash
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --cpu
```

### Test flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| positional config | Test config file. | Must match the checkpoint architecture/head and dataset/evaluator. |
| positional checkpoint | Checkpoint file or URL. | Required; sets `cfg.load_from`. |
| `--work-dir WORK_DIR` | Directory for evaluation metric files and logs. | Same priority rule as training. |
| `--dump DUMP` | Dump predictions for offline evaluation. | File must end in `.pkl` or `.pickle`; creates a `DumpResults` evaluator alongside the config evaluator. |
| `--cfg-options KEY=VALUE ...` | Merge config overrides. | Same quoting rules as training. |
| `--show-dir SHOW_DIR` | Save visualization images. | Requires `default_hooks.visualization` to exist in the config. |
| `--show` | Display predictions in a GUI window. | Avoid on headless servers; prefer `--show-dir`. |
| `--interval INTERVAL` | Visualize every N samples. | Defaults to 1 in the CLI. |
| `--wait-time WAIT_TIME` | GUI display time per sample. | Defaults to 2 seconds. |
| `--launcher {none,pytorch,slurm,mpi}` | Distributed launcher. | Single-process commands use `none`; distributed wrappers set this automatically. |

Preview test plus prediction dump:

```bash
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --work-dir work_dirs/eval_run --dump work_dirs/eval_run/predictions.pkl
```

Preview saved visualization every tenth sample:

```bash
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --show-dir work_dirs/eval_run/vis --interval 10
```

If the config lacks the visualization hook, create a small derived config that defines `default_hooks.visualization = dict(type='VisualizationHook')` before running, or omit visualization flags. In this version, the test entrypoint checks for the hook before merging `--cfg-options`, so adding the hook solely with `--cfg-options` in the same command will not satisfy the assertion. Avoid GUI `--show` on non-interactive machines.

## Quick tiny-dataset recipe caveats

A common quick run trains a TSN/ResNet-style Kinetics RGB config on a tiny Kinetics-like two-class dataset. Treat it as a smoke/debug exercise:

- It may depend on externally downloaded videos and optional pretrained checkpoints; do not require downloads unless the user approves network access.
- Update dataset roots and annotation files to point at user-provided tiny data.
- Reduce `train_dataloader.batch_size`, `train_cfg.max_epochs`, validation interval, checkpoint interval, and kept checkpoint count.
- Set the classifier head `num_classes` to the tiny/custom class count.
- If using pretrained weights, put them in `load_from`; do not use `--resume` for first-time fine-tuning.
- High validation/test scores on tiny data are not benchmark evidence and can reflect pretrained features, tiny validation sets, or augmented test pipelines.

## Distributed and Slurm planning

Preview single-machine multi-GPU training:

```bash
python scripts/mmaction2_train_test_command_builder.py dist-train --config CONFIG.py --gpus 4 --port 29500
```

Preview single-machine multi-GPU testing:

```bash
python scripts/mmaction2_train_test_command_builder.py dist-test --config CONFIG.py --checkpoint CHECKPOINT.pth --gpus 4 --port 29500
```

Use distinct ports and visible-device sets when launching multiple jobs on the same host. Multi-node distributed jobs need matching `NNODES`, `NODE_RANK`, `MASTER_ADDR`, and `PORT` on each node. Distributed runs usually require GPUs because many configs use an NCCL distributed backend. For CPU-only debugging, prefer a single-process CPU command.

Preview Slurm training:

```bash
python scripts/mmaction2_train_test_command_builder.py slurm-train --partition PARTITION --job-name JOB --config CONFIG.py --gpus 8 --gpus-per-node 8 --cpus-per-task 5
```

Preview Slurm testing:

```bash
python scripts/mmaction2_train_test_command_builder.py slurm-test --partition PARTITION --job-name JOB --config CONFIG.py --checkpoint CHECKPOINT.pth --gpus 8 --gpus-per-node 8 --cpus-per-task 5
```

Slurm environment variables:

| Variable | Meaning |
| --- | --- |
| `GPUS` | Total GPU tasks to allocate. |
| `GPUS_PER_NODE` | GPU tasks per node. |
| `CPUS_PER_TASK` | CPU cores per task. |
| `SRUN_ARGS` | Additional `srun` options, quoted as one shell value. |

Match `GPUS`, `GPUS_PER_NODE`, partition policy, account constraints, and `SRUN_ARGS` to the target cluster. Slurm commands are environment-specific; preview the command and ask the user before submitting jobs.
