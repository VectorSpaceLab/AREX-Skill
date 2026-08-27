# Configuration and data layout

## Purpose

Read this when you need to choose a config file, understand the filelist format, or map repo settings to a training or inference run.

## Config files

| File | Purpose | Key differences |
| --- | --- | --- |
| `configs/ljs_base.json` | LJ Speech single-speaker baseline | `n_speakers = 0`; default stochastic-duration path; cleaned English text |
| `configs/ljs_nosdp.json` | LJ Speech single-speaker variant | `use_sdp = false`; useful when you want the non-stochastic duration predictor path |
| `configs/vctk_base.json` | VCTK multi-speaker baseline | `n_speakers = 109`; `gin_channels = 256`; speaker-conditioned training and inference |

Common fields:

- `train.segment_size = 8192` and `data.hop_length = 256` mean the model segment size is 32 frames in the training/inference code.
- `data.sampling_rate = 22050`.
- `data.filter_length = 1024` so the linear spectrogram has `filter_length // 2 + 1 = 513` bins.
- `data.n_mel_channels = 80` for mel-spectrogram losses and summaries.
- `data.add_blank = true` enables blank token interspersing.
- `data.cleaned_text = true` means the provided cleaned filelists are already phoneme-normalized.

## Filelist formats

- LJ Speech filelists use `wav_path|text`.
- VCTK filelists use `wav_path|speaker_id|text`.
- The repo's cleaned filelists end in `.cleaned` and are produced by the preprocessing helper.

## Dataset layout

- The README expects symlinks or aliases named `DUMMY1` for LJ Speech wavs and `DUMMY2` for VCTK downsampled wavs.
- Training and inference expect audio that matches the config sampling rate.
- The data loaders cache spectrograms as `*.spec.pt` files next to the source wavs.

## Model and training settings

- `train.py` is the single-speaker loop.
- `train_ms.py` is the multi-speaker loop.
- Both scripts use DDP with NCCL and assume CUDA.
- The source training scripts hardcode a bad default `MASTER_PORT`; the bundled launcher uses a valid port instead.
- `use_sdp` controls whether the model uses the stochastic duration predictor or the deterministic duration predictor.

## Text cleaning

- `english_cleaners2` expands abbreviations and uses `phonemizer` with the `espeak` backend.
- `basic_cleaners` and `transliteration_cleaners` do not require `espeak`.
- If you need custom preprocessing, match `text_index` to the filelist shape before writing `.cleaned` outputs.
