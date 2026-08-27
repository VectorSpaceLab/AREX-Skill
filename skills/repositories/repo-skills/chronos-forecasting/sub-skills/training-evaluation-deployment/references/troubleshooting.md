# Training, evaluation, and deployment troubleshooting

Use this when side-effecting Chronos workflows fail or need risk assessment before execution.

## Missing optional extras

Symptoms:

- `ImportError: fev is required`.
- `peft` missing or LoRA falls back to full fine-tuning.
- `boto3` missing for `s3://` model loading.
- maintainer training script cannot import `gluonts`, `typer_config`, `datasets`, or `tensorboard`.

Fix:

- Install the smallest needed extra or package set for the task.
- For high-level LoRA: install `peft`.
- For fev evaluation: install `fev` and `datasets`.
- For S3: install `boto3` and configure credentials.
- For maintainer scripts: use the documented dev dependencies and confirm the runtime budget.

## CPU fine-tuning is too slow

Symptoms:

- Tiny `fit` works but real fine-tuning appears stuck.
- Training step time is far longer than expected.

Fix:

1. Confirm whether the loaded model is on CPU by inspecting the device.
2. Use a GPU-capable environment only when the user has compatible hardware and approved GPU package install.
3. Reduce `batch_size`, `context_length`, `num_steps`, or number of series for smoke runs.
4. Use LoRA with a higher LoRA learning rate such as `1e-5` when appropriate.
5. Set explicit `output_dir` so partial results are easy to inspect or clean.

## CUDA out of memory

Symptoms:

- `CUDA out of memory`.
- Trainer crashes during the first batches.
- Forecasting works for one item but fails for a batch.

Fix:

- Lower `batch_size` first.
- Lower `context_length` if task quality allows.
- Use a smaller model (`autogluon/chronos-2-small` or Bolt variants for inference) when acceptable.
- Prefer LoRA over full fine-tuning.
- Avoid unnecessary multivariate/covariate batching in one call.
- Clear old processes and check GPU memory before relaunching.

## Output directory and checkpoint confusion

Symptoms:

- A fine-tuned checkpoint is missing.
- New run overwrote an old run.
- `from_pretrained` cannot find config/model files.

Fix:

1. Pass an explicit `output_dir` and `finetuned_ckpt_name`.
2. After `fit`, call `save_pretrained` on the returned pipeline when you need a stable final directory.
3. Keep adapter-only LoRA directories distinct from merged/saved Chronos-2 model directories.
4. Do not push to a hub or shared storage without explicit approval.

## Dataset or benchmark download failures

Symptoms:

- Hugging Face dataset errors.
- Network timeout in fev evaluation.
- Dataset config not found.

Fix:

- Confirm dataset path/config and cache availability.
- Run a bounded single-task/single-window evaluation before a sweep.
- If offline, require local datasets or cached Hugging Face assets.
- Record skipped benchmark coverage rather than inventing evaluation results.

## Hugging Face token or push failures

Symptoms:

- 401/403 errors when loading private models or pushing checkpoints.
- `push_to_hub` fails.

Fix:

- Ask the user to provide or configure the required token outside generated artifacts.
- Confirm repository name and permissions.
- Separate local saving (`save_pretrained`) from remote publishing.

## SageMaker/AWS errors

Symptoms:

- missing role/profile/region,
- endpoint creation denied,
- model artifact cannot be pulled,
- endpoint timeout or invocation schema error.

Fix:

1. Confirm IAM role, region, credentials, and cost budget.
2. Validate payload locally through DataFrame and model smoke checks.
3. Convert datetimes/categories to JSON-safe types.
4. Use smaller batch/horizon or a larger/asynchronous endpoint for timeouts.
5. Delete test endpoints when the user does not want them retained.

## `torchrun` launch mistakes

Symptoms:

- all ranks write the same output,
- distributed process hangs,
- environment variables conflict,
- wrong number of GPUs used.

Fix:

- Use `torchrun --nproc-per-node=N` only after confirming visible GPUs and data paths.
- Give each run a unique output directory.
- Start with single-GPU or a tiny local smoke before distributed runs.
- Keep `CUDA_VISIBLE_DEVICES` explicit.
- Capture logs per rank for debugging.

## When to stop

Stop and ask for user input when credentials, private model access, cloud costs, paper-scale benchmark duration, destructive overwrites, or large GPU/package installs are required and not already authorized.
