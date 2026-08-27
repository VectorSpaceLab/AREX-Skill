# Vocoder Training Workflows

This reference covers vocoder training preparation and command construction. It
is intentionally not a promise that training has been run; full vocoder training
is expensive and should be authorized separately.

## Minimal workflow

1. **Choose the vocoder family.** For most mel-to-waveform work, start with
   `HifiganConfig` unless the user needs a released registry pairing or an
   existing checkpoint that requires another config class.
2. **Prepare wavs.** Put training wav files under one directory tree. Resample
   first with [`../scripts/resample_audio_dir.py`](../scripts/resample_audio_dir.py)
   if sample rates are mixed or differ from the config.
3. **Create or edit a vocoder config.** Set `model`, `data_path`, `output_path`,
   `audio.sample_rate`, `audio.hop_length`, `audio.num_mels`, `seq_len`, loader
   workers, and batch sizes.
4. **Validate without training.** Run
   [`../scripts/validate_vocoder_config.py`](../scripts/validate_vocoder_config.py)
   and optionally compare against a TTS config with `--tts-config`.
5. **Compute stats only if the config uses mean-variance normalization.** Use
   [`../scripts/compute_audio_stats.py`](../scripts/compute_audio_stats.py) on a
   bounded wav subset first.
6. **Launch training only after cost approval.** Use the installed package
   training module and Trainer flags described below.

## Training module and Trainer flags

The installed package exposes vocoder training as a Python module. Use module
execution rather than a checkout-relative script path:

```bash
python -m TTS.bin.train_vocoder --config_path config.json
```

The inspected help mirrored Trainer-style arguments, including:

| Flag | Use |
| --- | --- |
| `--config_path` | start a run from a vocoder config file |
| `--continue_path` | continue from an existing training output directory containing `config.json` |
| `--restore_path` | restore checkpoint weights into a new run |
| `--use_ddp` | distributed data-parallel training |
| `--use_accelerate` | Hugging Face Accelerate integration when configured |
| `--grad_accum_steps` | gradient accumulation when batch size is memory-limited |
| `--small_run` | Trainer debugging mode; still may instantiate data/model |
| `--gpu` | select GPU behavior according to Trainer support |

Do not use `--continue_path` when the user wants a new fine-tune directory;
continuation resumes the existing run. Use `--restore_path` for a new run that
initializes weights from a checkpoint.

## HifiGAN recipe pattern

A distilled HifiGAN setup usually sets:

- `batch_size` and `eval_batch_size` based on VRAM;
- `num_loader_workers` and `num_eval_loader_workers` based on storage/CPU;
- `epochs`, `run_eval`, `eval_split_size`, and print/eval cadence;
- `seq_len` near a multiple of `audio.hop_length`;
- `pad_short` for clips shorter than `seq_len`;
- `use_noise_augment=True` for some GAN runs;
- `lr_gen` and `lr_disc` together;
- `data_path` to the wav directory and `output_path` to a run directory.

HifiGAN defaults have generator upsampling factors `[8, 8, 2, 2]`; their
product is `256`. Keep this aligned with `audio.hop_length` unless changing the
generator architecture deliberately.

## Raw wavs versus precomputed features

The training module chooses the data loader branch from the config:

- If `feature_path` is set, it loads wav files and `.npy` feature files and
  requires matching counts and matching file stems.
- If `feature_path` is empty, it recursively loads raw wav files from
  `data_path` and computes features through `AudioProcessor`.

For WaveRNN-style workflows, precomputed mel/quantized features may be useful.
For GAN vocoders such as HifiGAN, raw wav loading is usually simpler unless the
user already has verified feature files.

## Dataset and segment caveats

- `data_path` must contain at least one wav; empty directories fail before
  training begins.
- GAN datasets compare feature frames to waveform segments. A typical expected
  shape is `(batch_size, num_mels, seq_len // hop_length + conv_pad * 2)`.
- Very short wavs require `pad_short` or they may not produce usable segments.
- `use_cache=True` can improve speed but may exhaust RAM.
- `use_noise_augment=True` changes waveform/feature equality, so use it for
  training robustness, not for deterministic feature validation.

## Cost and backend expectations

- CPU can validate configs, compute tiny stats, and resample small fixtures, but
  full training on CPU is often too slow for interactive work.
- CUDA is optional for this generated skill, but strongly preferred for full
  vocoder training.
- GPU OOM usually requires lowering `batch_size`, `eval_batch_size`, `seq_len`,
  worker counts, or enabling `--grad_accum_steps` instead of increasing the
  batch.
- Mixed precision can reduce memory but may expose numeric instability in GAN
  losses; change one training variable at a time.

## Native-style candidates for later verification planning

The later verification phase can recreate bounded checks with user-owned tiny
wavs instead of running long training:

1. Compute statistics over a tiny wav directory and assert the `.npy` file has
   mel/linear mean/std keys and the expected `num_mels` length.
2. Resample a copied tiny wav directory and assert every output has the target
   sample rate while the input tree remains unchanged.
3. Treat one-epoch vocoder training as optional/expensive; run only when the
   user authorizes the runtime and backend cost.

## Source-script decisions

| Package utility pattern | Bundled decision |
| --- | --- |
| Vocoder training module | Reference/wrap through config validation; no bundled trainer copy because training is expensive and the installed module remains the public execution surface. |
| Statistics utility | Adapted as [`../scripts/compute_audio_stats.py`](../scripts/compute_audio_stats.py) with explicit wav directory and `--max-files` bound. |
| Resampling utility | Adapted as [`../scripts/resample_audio_dir.py`](../scripts/resample_audio_dir.py) with output-dir-first safety and explicit `--in-place`. |
| VAD silence removal utility | Wrapped as [`../scripts/trim_silence_vad.py`](../scripts/trim_silence_vad.py) with cache/network warning and no model load during help. |
| Teacher-forced spectrogram extraction | Reference-only because it needs a trained TTS checkpoint/config, a formatter-valid dataset, and writes many feature files. |
| WaveGrad tuning | Reference-only because it is checkpoint-specific and can grow combinatorially with the search depth and inference iterations. |
