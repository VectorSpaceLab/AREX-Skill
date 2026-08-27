# Troubleshooting

## `train.py` fails on import or startup

**Symptoms:**

- `ModuleNotFoundError` for `torch`, `accelerate`, `timm`, `scipy`, `skimage`, or related packages.
- Compile or distributed initialization fails before the first batch.

**Fix:**

- Install the repo dependencies first.
- For `--use_accelerate`, make sure the `accelerate` package and a compatible GPU backend are available.
- If `torch.compile` is the trigger, diagnose with a simpler PyTorch build or temporarily disable compile in the config.

## `--resume` does not continue where expected

**Symptoms:**

- Training restarts at epoch 1.
- The checkpoint loads but the run length does not match the intended fine-tuning span.

**Causes and fixes:**

- The checkpoint path does not exist, so the script logs a missing file and starts fresh.
- The filename does not end with `epoch_<N>.pth`, so the epoch parser cannot recover `N` reliably.
- Remember that `--epochs` is the final absolute epoch number. If you resume from `epoch_244.pth` and want 50 more epochs, set `--epochs 294`.

## DDP or Accelerate backend errors

**Symptoms:**

- NCCL timeout or rendezvous errors.
- `torchrun` complains about the process group or visible devices.
- Accelerate reports a GPU/backend mismatch.

**Fix:**

- Verify the GPU IDs you pass to the shell launcher.
- Use `--dist True` only when a native multi-GPU DDP launch is intended.
- Use `--use_accelerate` only when the environment supports the selected mixed-precision mode.
- For a simple fallback, run a single GPU first.

## Checkpoints are not written where expected

**Symptoms:**

- No `epoch_*.pth` files appear.
- Only the log file is present in the checkpoint directory.

**Causes and fixes:**

- The run ended before the checkpoint save window opened.
- `config.save_last` and `config.save_step` do not match the current task schedule.
- The `--ckpt_dir` path points somewhere other than the directory you are inspecting.

## Relative-path surprises

**Symptoms:**

- `train.sh`, `test.sh`, or `gen_best_ep.py` appear to use the wrong files.
- `e_preds`, `e_results`, or `ckpts` show up in an unexpected directory.

**Cause:**

- The launchers use relative defaults and assume a repo-root-style working directory.

**Fix:**

- `cd` into the BiRefNet checkout before running the shell scripts, or pass explicit absolute paths to `--ckpt_dir`, `--pred_root`, and `--save_dir`.

## Evaluation skips a dataset

**Symptoms:**

- `eval_existingOnes.py` prints `Skip dataset ...`.
- The pretty table has fewer rows than expected.

**Causes and fixes:**

- The prediction tree does not contain `<pred_root>/<model>/<dataset>/`.
- The dataset name in `--data_lst` does not match the folder name under the GT root.
- The checkpoint folder names do not include the expected `epoch_<N>` fragment, so model sorting becomes less useful.

## Metric files look empty or malformed

**Symptoms:**

- `gen_best_ep.py` finds no usable lines.
- The result tables are missing numeric rows.

**Causes and fixes:**

- `eval_existingOnes.py` was not run first.
- `e_results` was deleted or you are running from the wrong directory.
- The evaluation text files do not follow the standard table layout.

## HCE confusion

**Symptoms:**

- Human-correction-effort values are missing or not meaningful for the task.

**Cause:**

- HCE is mainly useful for DIS-style evaluation. Other tasks should usually focus on `S` and `wF` instead.

**Fix:**

- For non-DIS tasks, use the standard segmentation metrics in the table and treat HCE as optional.

## Memory or precision trouble during training

**Symptoms:**

- CUDA OOM.
- Extremely slow training after a config or precision change.

**Fix:**

- Reduce batch size, use more GPUs, or simplify the precision/compile settings.
- The default configuration is tuned for heavy training hardware, not a minimal CPU box.

## `check_state_dict` is still needed after a resume load

**Symptoms:**

- Keys start with `module.` or `_orig_mod.` after distributed or compiled training.

**Fix:**

- Keep the prefix cleanup step before `load_state_dict`.
- If the cleaned keys still do not match, suspect an architecture mismatch rather than a wrapper prefix problem.
