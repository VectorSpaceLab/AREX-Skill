# MMYOLO training/evaluation troubleshooting

Use this reference when command preflight or an actual MMYOLO train/test job fails. Prefer fixing the input/config/launcher issue before rerunning an expensive job.

## Safety first

- The bundled helper scripts only print commands; they do not launch training or evaluation.
- If a user asks to run a real job, restate the expected side effects: GPU/CPU time, dataset reads, checkpoint/log writes, possible network access only if their config or checkpoint path requires it.
- For long runs, confirm work directory, device selection, and resume policy before launching.

## AMP warnings and assertions

The MMYOLO training command's `--amp` handling inspects `cfg.optim_wrapper.type`:

- If it is `OptimWrapper`, MMYOLO changes it to `AmpOptimWrapper` and sets dynamic loss scaling.
- If it is already `AmpOptimWrapper`, MMYOLO prints a warning that AMP is already enabled. This is usually safe; remove `--amp` if the warning is noisy.
- If it is any other wrapper type, MMYOLO raises an assertion: `--amp` is only supported when the optimizer wrapper type is `OptimWrapper`.

Recovery:

1. Inspect the merged config’s `optim_wrapper.type`.
2. If AMP should be config-native, change the config in `config-customization` rather than stacking `--amp` on top of a custom wrapper.
3. If using `--cfg-options optim_wrapper.type=...`, be explicit and re-run the safe command builder before launching.

## Expected quickstart warnings

These warnings can be normal during one-class YOLOv5 fine-tuning:

- `YOLOv5Head` with `num_classes == 1` can report `loss_cls` as zero. This is expected for the YOLOv5 single-class setup and does not by itself imply failed training.
- Loading COCO-pretrained weights into a head with a different number of classes can produce “model and loaded state dict do not match exactly” for head layers. This is expected when fine-tuning from COCO weights onto a different class count.

Escalate only if unrelated layers fail to load, metrics do not move, or the checkpoint/config class counts are inconsistent.

## Config, dataset, and metainfo issues

Symptoms:

- Config file not found or cannot be parsed.
- Training starts but dataset length is zero.
- Evaluation metrics fail because annotation paths or evaluator types do not match.
- Class names or palettes are ignored or inconsistent.

Recovery:

- Route config edits and merged-config inspection to `config-customization`.
- Route annotation/schema/layout validation to `data-tools`.
- Keep custom metainfo fields lowercase. MMYOLO checks custom metainfo casing before runner construction.
- Prefer a small config parse and dataset-path check before launching training.

## Work directory and resume issues

Facts:

- CLI `--work-dir` overrides the config work directory.
- If no work directory is provided and the config lacks one, MMYOLO derives `./work_dirs/<config-basename>`.
- `--resume` with no value sets auto-resume from the latest checkpoint in the resolved work directory.
- `--resume CHECKPOINT.pth` resumes from the explicit checkpoint path.

Common fixes:

- If auto-resume restarts from scratch, verify the work directory is the same one used by the interrupted run and contains a valid latest checkpoint marker/checkpoint.
- If resuming from an explicit checkpoint, verify it exists and is readable before launching.
- Do not confuse `load_from` fine-tuning with `resume`; resume includes optimizer and scheduler state.

## Checkpoint/model mismatch during testing

Symptoms:

- Missing/unexpected keys when loading checkpoint.
- Head shape mismatch.
- Evaluation runs but class metrics are nonsensical.

Recovery:

- Confirm the test config is the same architecture and class count used to train the checkpoint.
- For fine-tuned checkpoints, do not test with an unmodified COCO config unless the head and metainfo still match COCO.
- If a deploy-mode test is requested, `--deploy` only switches supported modules to deploy form; it does not convert a normal checkpoint into ONNX/TensorRT/RKNN artifacts.

## Prediction-output failures

`--out` failure:

- MMYOLO asserts unless the filename ends with `.pkl` or `.pickle`.
- Use the bundled test helper to validate suffixes before launch.

`--json-prefix` confusion:

- Pass a prefix such as `outputs/predictions`, not `outputs/predictions.json`.
- Expected COCO-style output includes names such as `outputs/predictions.bbox.json`.
- JSON prefix mode sets evaluator format-only behavior. If the user needs normal metrics and JSON output, explain this distinction and verify the intended result.

Painted output:

- Prefer `--show-dir DIR` on servers and CI.
- `--show` opens an interactive window and can hang or fail without a display.

## TTA failures

The MMYOLO testing command's `--tta` handling asserts unless both `tta_model` and `tta_pipeline` exist in the config.

Recovery:

- Route TTA config creation/editing to `config-customization`.
- If the config has TTA keys but still fails, inspect nested `test_dataloader.dataset` wrappers; TTA changes the final dataset pipeline and disables incompatible `batch_shapes_cfg` at the innermost dataset level.
- TTA increases evaluation cost because multiple augmented views are evaluated per image.

## Launcher, local-rank, and port problems

Symptoms:

- Distributed job hangs at initialization.
- “Address already in use” or rendezvous failures.
- All workers appear to use GPU 0.
- Slurm rejects the job or resources are not allocated.

Recovery:

- For MIM distributed launches, pass a unique `--port` for each concurrent job.
- Confirm `CUDA_VISIBLE_DEVICES` contains exactly the GPUs intended for the job.
- For multi-node runs, confirm launcher-specific master address, node rank, and shared port across nodes.
- Do not manually set local rank unless diagnosing launcher behavior; PyTorch launchers normally provide it.
- For Slurm, confirm partition, account policy, GPU count, GPUs per node, CPU per task, and any required site-specific `srun` arguments with the cluster owner.

## MIM command failures

Symptoms:

- `mim` command not found.
- MIM cannot locate `mmyolo` train/test entrypoints.
- MIM log-analysis commands fail through cross-library routing.

Recovery:

- Verify OpenMIM and MMYOLO are installed in the same Python environment.
- Run `mim train mmyolo --help`, `mim test mmyolo --help`, or `mim run mmyolo --help` to confirm package command discovery before constructing launch commands.
- For log analysis, verify compatible MMDetection tooling and optional plotting dependencies are installed.
- Do not download or install packages without user approval when the current task is only command construction.

## Visualization backend issues

Local backend:

- Writes artifacts under the work directory timestamp layout. Check disk space and work-dir path.

TensorBoard:

- Requires the TensorBoard package and visualizer backend configuration.
- Use `tensorboard --logdir WORK_DIR` after the run has written event data.

WandB:

- Requires the WandB package, login, network availability, and a configured visualizer backend.
- Warn users not to paste API keys into prompts, logs, command histories, or skill files.
- If offline or private execution is required, prefer Local or TensorBoard backends.

## Scheduler, optimizer, and batch-size surprises

- YOLOv5/YOLOv7 optimizer constructors can scale weight decay based on `batch_size_per_gpu` and world size. If batch size changes, review the optimizer constructor behavior rather than assuming weight decay stayed fixed.
- YOLOv5 scheduler warmup behavior is hook-controlled. If learning-rate or momentum curves look wrong, use the scheduler visualization recipe before launching a long training run.
- If plotting curves from logs, ensure the evaluation interval used for plot comparisons matches the interval used during training.

## Confusion-matrix failures

The confusion-matrix analysis expects a config, a pickle prediction file from `--out`, and matching dataset annotations.

Common fixes:

- Regenerate predictions with `--out predictions.pkl` if only JSON output exists.
- Verify the config’s test dataset order and annotations match the prediction file.
- Adjust `--score-thr`, `--tp-iou-thr`, or `--nms-iou-thr` only after confirming the base predictions load correctly.
- If `mmcv.ops.nms` import fails, the active MMCV build may not match the current PyTorch/CUDA stack.
