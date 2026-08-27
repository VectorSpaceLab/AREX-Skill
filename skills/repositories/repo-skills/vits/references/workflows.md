# Workflows

## Purpose

Read this when you need the end-to-end command shape for the VITS repository.

## Shared preflight

1. Run `scripts/check_install.py` from a checkout root.
2. If `models` import fails on `monotonic_align`, run `scripts/build_monotonic_align.py`.
3. If you need English text cleaning, make sure `espeak` or `espeak-ng` is installed.
4. Use `scripts/model_smoke.py` for a tiny GPU forward, inference, or voice-conversion check before a long run.

## Data preparation

Use `scripts/preprocess_text.py` when you have custom filelists and want `.cleaned` text outputs that match the repo configs.

Typical steps:

- Prepare the dataset layout.
- Ensure audio matches the expected sampling rate.
- Clean the filelists with the bundled helper.
- Reuse the provided LJ Speech or VCTK cleaned filelists when you do not need custom preprocessing.

## Training

Use `scripts/launch_training.py` when you want the repo's training flow without hand-editing launch details. It defaults to a dry run and accepts `--run` when you are ready to start the job.

Typical choices:

- LJ Speech single-speaker training uses the single-speaker config.
- VCTK multi-speaker training uses the multi-speaker config and speaker ids.
- The launcher should choose a valid `MASTER_PORT` and the correct training module for the selected config.

When you are ready to run the actual training job, use the launcher output to confirm the command and environment, then execute the run on a CUDA-capable machine.

## Inference and voice conversion

Use `scripts/synthesize.py` when you need text-to-speech or voice conversion from a checkpoint.

Typical choices:

- LJ Speech synthesis uses a single-speaker checkpoint and plain text input.
- VCTK synthesis needs a speaker id.
- Voice conversion needs a source audio file plus source and target speaker ids.
- The bundled synthesis helper uses a local STFT compatibility path for source-audio spectrograms under modern PyTorch.

## Smoke checks

Use `scripts/model_smoke.py` to check three common surfaces:

- `forward` — model construction plus a tiny synthetic training-style pass.
- `infer` — text-to-speech generation with random token ids.
- `voice-conversion` — multi-speaker conversion with synthetic spectrograms and speaker ids.

Prefer the smoke helper when you only need to prove the environment and model wiring, not to run a full training or generation job.
