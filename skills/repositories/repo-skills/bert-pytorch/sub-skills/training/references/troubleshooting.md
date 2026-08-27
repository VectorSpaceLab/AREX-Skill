# Training Troubleshooting

## Model construction fails immediately

Symptoms:

- An assertion fires during `BERT` initialization.
- Training never starts.

Likely cause:

- `hidden` is not divisible by `attn_heads`.

Recovery:

- Choose compatible values, such as `hidden=32` and `attn_heads=4` for a smoke run.
- Re-run `python sub-skills/training/scripts/train_smoke.py` after correcting the values.

## The CLI does not disable CUDA or memory loading the way you expected

Symptoms:

- `--with_cuda False` still behaves like CUDA is on.
- `--on_memory False` does not switch the data loader to streaming mode.

Likely cause:

- The CLI uses `type=bool`, so the string `False` is still truthy.

Recovery:

- Use `python sub-skills/training/scripts/train_smoke.py --device cpu` for an explicit CPU run.
- Use the Python API if you need direct boolean control.

## CUDA is available but the model still lands on CPU

Symptoms:

- Training runs on CPU even though a GPU host is visible.

Likely cause:

- CUDA was not requested, or the installed torch build does not expose CUDA.

Recovery:

- Run `python scripts/check_install.py --check-torch` to confirm the backend.
- Use `--device cuda` only after confirming `torch.cuda.is_available()` is true.

## You hit out-of-memory errors

Symptoms:

- CUDA OOM or slow, memory-heavy CPU training.

Likely cause:

- The smoke configuration is too large for the available memory.

Recovery:

- Reduce `batch_size`, `seq_len`, `hidden`, or `layers`.
- Prefer the bundled smoke defaults before trying a larger configuration.

## The checkpoint file is missing or has the wrong name

Symptoms:

- The output path does not exist after a run.
- The saved file name includes an unexpected suffix.

Likely cause:

- `save()` appends `.ep{epoch}` to the prefix you passed.
- The parent directory did not exist before the save call.

Recovery:

- Treat the save argument as a prefix.
- Create the parent directory before training.
- Use `python sub-skills/training/scripts/train_smoke.py` to let the helper manage the path.

## DataLoader or dataset settings are too noisy for a smoke run

Symptoms:

- The run takes longer than expected or prints noisy worker output.

Likely cause:

- Too many DataLoader workers or a large batch size.

Recovery:

- Use `num_workers=0` and a tiny batch size for smoke checks.
- Keep the smoke corpus tiny and the sequence length short.
