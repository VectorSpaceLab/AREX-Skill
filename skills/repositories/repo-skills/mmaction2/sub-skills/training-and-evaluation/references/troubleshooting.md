# Training, Testing, And Evaluation Troubleshooting

Use this checklist to diagnose MMAction2 train/test/evaluation failures before suggesting a rerun. Prefer a safe command preview, parser help, config inspection, and environment check over launching another expensive job.

## Fast Triage

1. Confirm the user intended to execute a job, not just build a command.
2. Confirm the config and checkpoint paths are valid in the user's workspace. Test requires a checkpoint; train usually does not unless the config uses `load_from`.
3. Confirm device intent: CPU, one GPU, selected GPUs, distributed, or Slurm.
4. Confirm output paths: work directory, dump file, visualization directory, confusion matrix output, or localization detection output.
5. For config overrides, inspect quoting and nested keys before changing code.

## Common Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `mmaction`, `mmengine`, `mmcv`, `decord`, or video backends | The runtime environment is incomplete or optional video dependencies are missing. | Use the root skill's environment check; install the package and compatible MMEngine/MMCV/PyTorch stack. Route decode/backend issues to data/config when they depend on dataset pipeline. |
| `CUDA error`, `No CUDA GPUs are available`, or command uses the wrong GPU | Visible devices do not match the command, or GPU is unavailable. | For CPU, prefix `CUDA_VISIBLE_DEVICES=-1`. For selected GPUs, set `CUDA_VISIBLE_DEVICES=0,1,...` before launching. Do not use Slurm/distributed GPU templates on a CPU-only host. |
| `CUDA out of memory` during train or test | Batch size, clips/crops, frame resolution, workers, or model size exceed memory. | Reduce `train_dataloader.batch_size` or test batch size, lower clips/crops in the test pipeline via config, enable `--amp` for compatible training, use fewer visible GPUs per job only with corresponding batch/LR changes, or choose a smaller model. |
| Training starts from scratch when user expected continuation | Confusion between `load_from` and `--resume`. | Use `load_from` for pretrained initialization; use `--resume` to continue optimizer/scheduler/epoch state from an existing run. Use `--resume` with no path for latest checkpoint in `work_dir`. |
| Test rejects or misloads checkpoint | Checkpoint architecture/head/classes do not match the config, or path/URL is wrong. | Match config and checkpoint family, class count, modality, and head shape. For custom class count, train a matching head or handle expected missing/unexpected keys deliberately. |
| `--amp` assertion about custom optimizer wrapper | Config optimizer wrapper type is not `OptimWrapper` or `AmpOptimWrapper`. | Remove `--amp`, or change the config to a supported AMP optimizer wrapper after confirming numerical and dependency compatibility. |
| `auto_scale_lr` attribute/key error | Config lacks `auto_scale_lr` or `base_batch_size`. | Do not pass `--auto-scale-lr`, or add a valid `auto_scale_lr = dict(enable=False, base_batch_size=...)` section based on the original global batch size. |
| `--cfg-options` parsing error or override ignored | Shell quoting, list syntax, tuple syntax, or nested key is wrong. | Use `KEY=VALUE` tokens with no spaces. Quote lists/tuples, e.g. `key="[a,b]"` or `key="[(a,b),(c,d)]"`. Verify the nested key belongs to the active config. |
| Work directory is not where expected | CLI/config/default priority misunderstood. | Priority is `--work-dir`, then config `work_dir`, then `./work_dirs/<config_basename>`. Check logs and checkpoint hook settings under that directory. |
| No validation metrics during training | `--no-validate` used, missing val loop/evaluator, or `train_cfg.val_interval` too large. | Remove `--no-validate`, restore `val_cfg`, `val_dataloader`, `val_evaluator`, and set an appropriate `val_interval`. |
| Best checkpoint not created | Checkpoint hook `save_best`, metric name, or validation interval is not configured as expected. | Inspect `default_hooks.checkpoint` and evaluator output key. For tiny runs, save every epoch and set a short validation interval. |
| `VisualizationHook is not set` when using `--show` or `--show-dir` | Test CLI requires `default_hooks.visualization` to already exist in the loaded config before CLI config overrides are merged. | Create a small derived config that defines `default_hooks.visualization = dict(type='VisualizationHook')`, then use `--show-dir`; or omit visualization flags. Do not rely on adding the hook solely through `--cfg-options` in the same test command. |
| GUI window hangs or crashes | `--show` used on headless/remote machine. | Use `--show-dir` instead, or disable visualization. |
| `The dump file must be a pkl file` | `--dump` path does not end with `.pkl` or `.pickle`. | Change dump extension and ensure the parent directory is intentional. |
| Offline `eval_metric.py` fails | Dump file is not MMAction2 prediction data samples, config evaluator mismatches the dump, or task annotation files are missing. | Regenerate the dump with the matching config/checkpoint and use compatible evaluator settings; route dataset metadata issues to data/config. |
| Fusion accuracy fails or outputs nonsense | Prediction dumps have different sample order, label spaces, or coefficient counts. | Ensure each stream used the same dataset split/order and that `--coefficients` length equals `--preds` length. Use `--apply-softmax` when fusing logits. |
| Confusion matrix complains about `num_classes` | The tool received labels rather than score vectors and cannot infer class count. | Provide `num_classes` in config/evaluator or use score-containing prediction dumps. |
| Distributed job hangs at startup | Port collision, wrong `MASTER_ADDR`, mismatched `NNODES`/`NODE_RANK`, firewall, or slow network. | Set a unique `PORT`, identical `MASTER_ADDR` on all nodes, correct node ranks, and verify connectivity. Use one job per port. |
| NCCL errors in distributed mode | GPU/NCCL backend mismatch, CPU-only host, driver issue, or process count mismatch. | Prefer single-process CPU for CPU debugging. For GPU distributed, align visible GPUs with `GPUS`, check driver/CUDA/PyTorch compatibility, and avoid oversubscribing devices. |
| Slurm submission allocates wrong resources | `GPUS`, `GPUS_PER_NODE`, `CPUS_PER_TASK`, partition, account, or `SRUN_ARGS` mismatch cluster policy. | Preview the command, ask the user for cluster constraints, and adjust Slurm environment variables before submission. |
| AVA, MultiSports, or ActivityNet metrics cannot find files | Detection/localization evaluators need task-specific annotations, exclude files, label maps, proposals, or ground truth. | Route data paths/schema to data/config, then rerun metrics with explicit file paths. |
| ActivityNet mAP reporting attempts network access | The helper mode expects an auxiliary classification prediction JSON and may fetch it if absent. | Provide the auxiliary file in the working directory or avoid the helper on no-network systems. Ask before allowing downloads or generated output writes. |

## Safe Validation Steps

- Use the bundled command builder to preview command syntax without execution.
- Run parser help only when the user's environment can import the required packages.
- Inspect the final config with a safe config-inspection helper from the data/config sub-skill before launching expensive jobs.
- For test/evaluation, verify checkpoint/config/model family/class count alignment before running.
- For distributed/Slurm, confirm resource variables and output directories with the user before submission.
