# Training troubleshooting

## Training fails before the first batch

- **Symptom:** NCCL or process-group initialization errors.
- **Cause:** the source training scripts hardcode an invalid `MASTER_PORT` value.
- **Next step:** use `../../../scripts/launch_training.py`, which selects a valid port and the correct module.

## CPU-only environment

- **Symptom:** `assert torch.cuda.is_available(), "CPU training is not allowed."`
- **Cause:** training is CUDA-only.
- **Next step:** move to a CUDA-capable environment before retrying.

## `models` import fails during launch

- **Symptom:** `ModuleNotFoundError` for `monotonic_align.monotonic_align.core`.
- **Cause:** the compiled extension has not been built into the nested package layout.
- **Next step:** run `../../../scripts/build_monotonic_align.py` first.

## Checkpoint resume fails

- **Symptom:** missing or mismatched keys when the launcher resumes from a checkpoint.
- **Cause:** the checkpoint was created with a different config family, speaker count, or duration-predictor setting.
- **Next step:** resume with the same config family and the matching single- or multi-speaker launcher.

## Out-of-memory or very slow startup

- **Symptom:** CUDA OOM, enormous startup latency, or unstable training batches.
- **Cause:** the model is large and the repo defaults are tuned for multi-GPU runs.
- **Next step:** lower batch size, confirm the GPU count, and use `../../../scripts/model_smoke.py` to separate environment issues from true training load.
