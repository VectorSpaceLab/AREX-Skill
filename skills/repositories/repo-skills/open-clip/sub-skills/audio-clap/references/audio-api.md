# Audio Model and Transform API

## Model Families

OpenCLIP audio-text models instantiate `CLAP`, which owns `model.audio`, `model.text`, `logit_scale`, `encode_audio`, `encode_text`, and `get_logits(audio, text)`.

- `CLAP-HTSAT-*` uses an HTSAT audio encoder with CLAP log-mel preprocessing. Valid built-in HTSAT sizes include `tiny`, `base`, and `large`.
- `CLAP-Whisper-*` uses a Whisper-family audio encoder and CLAP text tower variants. Whisper configs usually use `sample_rate=16000`, `mel_bins=80`, `window_size=400`, and `hop_size=160`.
- `naflexclap_*` uses `model_type="naflexvit"`: a variable-duration log-mel patch encoder plugged into the CLAP contrastive task.

`AudioTower` supports `model_type="HTSAT"`, `"whisper"`, and `"naflexvit"`. Other `model_type` values raise `ValueError`.

## Optional Audio Dependencies

Audio APIs are import-light, but real audio transforms and model builds need optional packages.

```python
from open_clip.audio import AUDIO_AVAILABLE, require_audio

print(AUDIO_AVAILABLE)
require_audio()
```

`require_audio()` checks for `torchaudio`, `torchlibrosa`, and `openai-whisper` import modules and raises a message naming missing packages. HF zero-shot dataset loading also needs `datasets[audio]`.

## CLIPAudioCfg Defaults

`CLIPAudioCfg()` defaults are:

| Field | Default | Notes |
| --- | --- | --- |
| `model_type` | `"HTSAT"` | `"HTSAT"`, `"whisper"`, or `"naflexvit"`. |
| `model_name` | `"tiny"` | HTSAT or Whisper size. |
| `audio_length` | `1024` | Legacy/config length field. |
| `clip_samples` | `480000` | Fixed CLAP clip length, 10 seconds at 48 kHz. |
| `sample_rate` | `48000` | Transform resampling target for HTSAT defaults. |
| `mel_bins` | `64` | Log-mel bins. |
| `window_size` | `1024` | STFT FFT/window length. |
| `hop_size` | `480` | STFT hop length. |
| `fmin`, `fmax` | `50`, `14000` | Mel frequency range. |
| `class_num` | `527` | HTSAT pretraining head class count. |
| `enable_fusion` | `False` | Enables 4-view fusion mel path for long clips when requested. |
| `fusion_type` | `"aff_2d"` | HTSAT fusion type. |
| `patch_freq`, `patch_time` | `64`, `4` | NaFlexClap mel patch geometry. |
| `patch_pad_mode` | `"floor"` | NaFlexClap final partial-patch fill. |

Use `scripts/audio_config_report.py --model <name>` to inspect the effective built-in model audio config without building weights.

## AudioAugmentationCfg and Fixed CLAP Transform

`AudioAugmentationCfg` defaults to:

```python
AudioAugmentationCfg(data_trunc="rand_trunc", data_fill="repeatpad", enable_fusion=False, int16_normalize=False)
```

`audio_transform_v2(audio_cfg, is_train, audio_aug_cfg)` returns a picklable `AudioPreprocess` callable for HTSAT/Whisper-style CLAP. It accepts `(waveform, sample_rate)`, resamples to `audio_cfg.sample_rate`, converts multi-channel audio to mono, optionally int16-normalizes, and returns a dict.

Fixed CLAP output shapes:

- `waveform`: `Tensor[clip_samples]` for each sample before collation; collated as `Tensor[B, clip_samples]`.
- `longer`: `bool` per sample; collated as `BoolTensor[B]`.
- `mel_fusion`: optional `Tensor[4, frames, mel_bins]`; collated as `Tensor[B, 4, frames, mel_bins]` where `frames = clip_samples // hop_size + 1`.

Fill and truncation behavior:

- `data_fill="pad"`: zero-pad short clips.
- `data_fill="repeat"`: repeat audio until `clip_samples`.
- `data_fill="repeatpad"`: repeat whole copies then zero-pad the remainder.
- `data_trunc="rand_trunc"`: randomly crops long clips during training.
- `data_trunc="trunc"`: takes the first `clip_samples` samples.
- `data_trunc="fusion"`: creates `mel_fusion` for long clips and keeps the first waveform segment.
- Eval uses deterministic `"trunc"` unless `enable_fusion` forces `"fusion"`.

## NaFlexClap Audio Transform

For `model.audio.cfg.model_type.lower() == "naflexvit"`, use `AudioNaFlexCfg.from_clip_audio_cfg(model.audio.cfg)` and `AudioNaFlexTransformFactory` instead of `audio_transform_v2`.

The NaFlex transform accepts `(waveform, sample_rate)`, resamples, computes log-mel, pads sub-window clips to at least one STFT window, and returns:

```python
{
  "patches": FloatTensor[N, in_chans * patch_freq * patch_time],
  "patch_coord": LongTensor[N, 2],
  "patch_valid": BoolTensor[N],
}
```

`patch_coord` stores `(freq_idx, time_idx)`. If `patch_freq == mel_bins`, the frequency axis is degenerate and the stream is effectively 1-D over time. If `patch_freq < mel_bins`, the transform produces a 2-D `(freq, time)` grid.

NaFlexClap collation pads variable `N` to the batch maximum or a configured cap, preserving whole frequency rows. A `max_seq_len` smaller than `freq_tokens` raises early because it would otherwise drop frequency rows.

## Forward and Task Behavior

`CLAP.forward(audio=..., text=...)` returns normalized `audio_features`, normalized `text_features`, and `logit_scale.exp()` when `output_dict=True`. `CLAP.get_logits(audio, text)` computes symmetric audio/text logits with the model logit scale.

`CLAPTask` is the training task for CLAP and NaFlexClap. It consumes dict batches with keys `"audio"` and `"text"`, maps `audio_features` into the contrastive loss path, and reports audio retrieval metrics during validation.

Use `task.create_dummy_batch()` rather than hand-building dummy data for FSDP or compiled paths. It emits waveform/fusion dicts for fixed CLAP and patch dicts for NaFlexClap.
