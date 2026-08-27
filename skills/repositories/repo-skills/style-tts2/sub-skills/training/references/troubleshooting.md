# Training troubleshooting

Use this reference after the command helper reports a failed preflight or a training run exits early. Data schemas and detailed config field definitions are owned by the [data-and-config sub-skill](../../data-and-config/SKILL.md); this file focuses on launch-stage failure recovery.

## CUDA or backend unavailable

Symptoms:

- `torch.cuda.is_available()` is false.
- Errors mention `cuda`, no NVIDIA driver, no CUDA device, or tensors being moved to CUDA.
- `train_second.py` or `train_finetune.py` fails immediately on a CPU-only host.

Recovery:

- Use a CUDA-capable environment with a CUDA-enabled PyTorch build. Training and fine-tuning are GPU workflows; there is no truthful CPU substitute for native StyleTTS2 training behavior.
- Do not try to force second-stage or fine-tuning to CPU: those launchers hard-code CUDA.
- First stage uses Accelerate but still has CUDA-specific tensor movement in the source, so treat it as CUDA-required too.
- Confirm CUDA before `--run`:

  ```bash
  python - <<'PY'
  import torch
  print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())
  PY
  ```

## Out of memory

Symptoms:

- CUDA OOM before or after `joint_epoch`.
- OOM appears only when SLM adversarial training begins.
- Fine-tuning fits initially but fails later in the run.

Recovery:

- Lower `batch_size`.
- Lower `max_len`; the repository training notes define the default hop size as 300 samples at 24 kHz, so one frame is about 0.0125 seconds.
- Lower `slmadv_params.batch_percentage` to use a smaller fraction of the batch during SLM adversarial loss.
- For one-GPU fine-tuning, prefer the helper's `finetune-accelerate` stage, which emits the documented `--mixed_precision fp16 --num_processes 1` command.
- If OOM happens after `joint_epoch`, the SLM adversarial stage is likely the trigger. Setting `loss_params.joint_epoch` larger than the total epoch count skips that stage; this is a memory-saving trade-off and may reduce quality.
- Revisit data/config with the [data-and-config sub-skill](../../data-and-config/SKILL.md) if samples are much longer than expected or if `max_len` and OOD lengths are inconsistent.

## NaN loss

Symptoms:

- Training loss becomes `nan`.
- NaNs appear soon after enabling mixed precision or after increasing batch size.

Recovery:

- First stage: do not use mixed precision by default. The repository notes first-stage mixed precision can cause NaNs on some datasets when batch size is not appropriate.
- First stage: use a sufficiently stable batch size; the repository notes very small/poorly chosen batches can be problematic.
- Second stage: experiment with batch size; higher batch sizes are more likely to produce NaNs, and the public training guidance recommends batch size 16 as a starting point.
- If NaNs follow an OOM recovery edit, revert one change at a time so you know whether `batch_size`, `max_len`, mixed precision, or checkpoint mismatch caused the instability.

## DDP or Accelerate fails on second stage

Symptoms:

- User tries `accelerate launch train_second.py` and distributed training hangs or errors.
- Errors mention unused parameters, DDP synchronization, or missing attributes under distributed wrappers.

Recovery:

- Use the helper stage `second`, which emits `python train_second.py --config_path ...`.
- The repository documents DDP/Accelerate for `train_second.py` as not working; the current source uses DataParallel wrappers instead.
- For fine-tuning on one GPU, use `finetune-accelerate`; do not infer that second-stage DDP is fixed because the fine-tune accelerate variant exists.

## Missing first-stage checkpoint

Symptoms:

- Error resembles `You need to specify the path to the first stage model.`
- The launcher prints that it is loading a first-stage model from `log_dir/<first_stage_path>` and then fails with file not found.
- First stage produced `epoch_1st_*.pth`, but second stage does not find `first_stage.pth`.

Recovery:

- Confirm whether second stage should start from first-stage weights or a full pretrained second-stage checkpoint.
- For first-stage weights, make sure the final first-stage checkpoint exists at `log_dir/<first_stage_path>`. If training ended early before final save, either resume/finish first stage or intentionally point `first_stage_path` at a periodic `epoch_1st_*.pth`.
- Remember that relative `first_stage_path` is joined under `log_dir`, not under the repo root.
- If using a full pretrained second-stage checkpoint, set `pretrained_model` and `second_stage_load_pretrained: true` instead of relying on `first_stage_path`.

## Missing pretrained checkpoint for fine-tuning

Symptoms:

- Fine-tune preflight warns that `pretrained_model` is missing.
- `torch.load` fails for a LibriTTS or other second-stage checkpoint path.
- The model loads partially or quality is poor after accidentally starting from first-stage weights.

Recovery:

- Download or place the intended second-stage pretrained checkpoint before launching fine-tuning.
- Keep `second_stage_load_pretrained: true` for normal fine-tuning from a full second-stage checkpoint.
- Use `load_only_params: true` for adaptation to new speaker data unless intentionally resuming the exact same optimizer state.
- Check that `model_params.multispeaker` matches the checkpoint family; the default fine-tune config expects a multispeaker base.

## Missing `tensorboard` or `pandas`

Symptoms:

- Import error for `torch.utils.tensorboard` or `tensorboard`.
- Import error for `pandas` from the dataset loader.
- `requirements.txt` installation succeeded but training imports still fail.

Recovery:

- Install the documented requirements, then add the hidden runtime imports:

  ```bash
  python -m pip install pandas tensorboard
  ```

- Re-run `python train_first.py --help`, `python train_second.py --help`, `python train_finetune.py --help`, and `python train_finetune_accelerate.py --help` from the checkout to verify imports without starting training.

## WavLM / Transformers download or cache failure

Symptoms:

- Failure in `AutoModel.from_pretrained`.
- Network timeout, authentication/cache error, or offline host error for the configured SLM model.
- Training stalls on first WavLM load.

Recovery:

- The configs use a Transformers model name for WavLM. A real run may download it if it is not already cached.
- On offline or firewalled systems, pre-populate the Hugging Face/Transformers cache or set the usual cache environment variables before launch.
- Confirm that the configured SLM sample rate remains 16 kHz unless the model/loss setup is intentionally changed.
- If the issue appears after moving machines, clear only the broken model cache entry or point the cache variables to a known-good local cache; do not edit training code first.

## Too-short samples or skipped SLM adversarial clips

Symptoms:

- SLM adversarial loss returns no usable batch.
- Logs become unstable after many short examples.
- Errors appear around random clip selection, predicted durations, or batch stacking.

Recovery:

- Ensure training samples and OOD texts are long enough for the configured `min_length`, `slmadv_params.min_len`, and `slmadv_params.max_len`.
- The SLM adversarial code skips examples whose ground-truth or predicted mel length is too short and returns `None` if too few clips remain.
- Use the [data-and-config sub-skill](../../data-and-config/SKILL.md) to validate list rows and adjust OOD/min-length settings. Do not mask this by increasing batch size until data length is known.

## Config/data path mismatch

Symptoms:

- The helper finds the config but warns about missing train/val/OOD paths or assets.
- Training starts but fails opening audio files.
- A copied config in `log_dir` shows stale data paths.

Recovery:

- Edit config paths before launch and re-run the helper dry-run.
- Remember that with the bundled helper, relative config paths are evaluated from the repo root.
- Data list rows are joined with `data_params.root_path` by the dataset loader; if `root_path` is empty, rows must still resolve from the training process working directory or be absolute.
- Use the [data-and-config sub-skill](../../data-and-config/SKILL.md) for schema-level validation and config-field interpretation.
