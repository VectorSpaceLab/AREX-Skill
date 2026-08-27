# Audio Tools Reference

Use this reference for safe Coqui TTS audio preprocessing and analysis tasks:
statistics, resampling, VAD trimming, `AudioProcessor` constraints, and feature
extraction preconditions.

## `AudioProcessor` defaults that affect compatibility

`AudioProcessor` is initialized from a Coqui `audio` config. The package default
`BaseAudioConfig` includes:

| Field | Default | Why it matters |
| --- | ---: | --- |
| `sample_rate` | `22050` | waveform rate expected during feature extraction/training |
| `fft_size` | `1024` | linear spectrogram frequency bins |
| `win_length` | `1024` | STFT window length; must not exceed `fft_size` |
| `hop_length` | `256` | frame spacing; usually must equal vocoder upsampling product |
| `num_mels` | `80` | mel channel count expected by the vocoder generator |
| `mel_fmin` | `0.0` | lower mel filterbank frequency |
| `mel_fmax` | `None` | upper mel filterbank frequency; when set, keep below Nyquist |
| `signal_norm` | `True` | enables feature normalization; `stats_path` changes normalization mode |
| `do_trim_silence` | `True` | trims silence when `AudioProcessor.load_wav` loads files |
| `trim_db` | `45` | silence threshold for AudioProcessor trimming |
| `resample` | `False` | runtime loading does not resample unless enabled or explicit `sr` is passed |

Preconditions that should be checked before spectrogram extraction or vocoder
training:

- `win_length <= fft_size`.
- `sample_rate`, `hop_length`, `num_mels`, and mel filter settings match the
  TTS model or feature source.
- If `stats_path` is set, the stats file contains `mel_mean`, `mel_std`,
  `linear_mean`, `linear_std`, and an `audio_config` compatible with the current
  config.
- Audio files are readable by `soundfile`/`librosa`/`torchaudio` and are not
  empty or corrupt.
- Resampling should be done before large training jobs; relying on per-load
  resampling is slower and easier to overlook.

## Computing audio statistics

Use the bundled bounded helper rather than running unbounded dataset statistics
by default:

```bash
python sub-skills/vocoder-and-audio-tools/scripts/compute_audio_stats.py \
  config.json stats.npy \
  --wav-dir data/wavs \
  --max-files 128
```

The helper:

- loads a Coqui config with the installed package;
- disables prior normalization and any previous stats path while computing new
  stats;
- scans a user-provided wav directory, sorted deterministically;
- limits work with `--max-files` unless the user explicitly passes `--max-files 0`;
- writes a `.npy` dictionary compatible with `AudioProcessor.load_stats`.

After computing stats, set `audio.stats_path` in the config to the produced
file and keep the rest of the audio config unchanged. Do not reuse stats across
configs with different mel/FFT/hop/normalization settings.

Source-script decision: the package statistics utility was adapted into the
bounded helper above because the original behavior can scan an entire dataset
from config metadata. The bundled helper requires an explicit wav directory and
file bound.

## Safe recursive resampling

Use the bundled helper for preprocessing copies:

```bash
python sub-skills/vocoder-and-audio-tools/scripts/resample_audio_dir.py \
  --input-dir raw_wavs \
  --output-dir wavs_22050 \
  --output-sr 22050 \
  --file-ext wav
```

Safety defaults:

- A separate `--output-dir` is required unless `--in-place` is explicitly set.
- The helper preserves the relative audio-file tree under the output directory.
- Existing outputs are not overwritten unless `--overwrite` is passed.
- Output sample rates are verified by default; use `--no-verify` only for a
  deliberate speed trade-off.

In-place resampling is intentionally opt-in:

```bash
python sub-skills/vocoder-and-audio-tools/scripts/resample_audio_dir.py \
  --input-dir wavs \
  --output-sr 16000 \
  --in-place \
  --overwrite
```

Use in-place mode only after a backup exists. Resampling rewrites audio content
and may convert files to mono, matching the package utility's TTS-oriented
behavior.

Source-script decision: the package resampling utility allows in-place mutation
when no output directory is provided. The bundled helper reverses that default
so future agents must opt into mutation.

## VAD silence trimming

Use VAD trimming only after the user accepts the model-cache/network behavior.
The bundled wrapper's help is safe:

```bash
python sub-skills/vocoder-and-audio-tools/scripts/trim_silence_vad.py --help
```

A real run requires either an explicit download/cache acknowledgement or a local
Silero VAD source directory:

```bash
python sub-skills/vocoder-and-audio-tools/scripts/trim_silence_vad.py \
  --input-dir wavs \
  --output-dir wavs_trimmed \
  --glob '**/*.wav' \
  --allow-download
```

Use `--trim-all-nonspeech` only when removing interior non-speech is acceptable.
For many TTS datasets, keeping speech timing but removing leading/trailing
non-speech is safer.

Source-script decision: the package VAD utility writes many files and may load a
Silero model through Torch Hub. The bundled wrapper documents the side effect,
requires an explicit output directory by default, and avoids model loading for
`--help` and `--dry-run`.

## Spectrogram extraction preconditions

Teacher-forced TTS spectrogram extraction is reference-only in this sub-skill
because it requires a trained TTS checkpoint, a matching TTS config, a dataset,
and can write many mel/wav/quantized feature files. If a later task requires
this workflow, check:

1. The task truly needs TTS-model-produced spectrograms rather than
   `AudioProcessor.melspectrogram` over ground-truth wavs.
2. The TTS checkpoint and config match.
3. Dataset formatter and speaker/d-vector fields are valid; route formatter
   issues to [../../training-config-data/SKILL.md](../../training-config-data/SKILL.md).
4. Output directories have enough disk space and do not overlap with raw data.
5. The resulting mel feature shape matches the intended vocoder config.

## WaveGrad tuning preconditions

WaveGrad noise-schedule tuning is reference-only because it is checkpoint- and
sample-count-dependent, performs a combinatorial search, and can be expensive.
Require a WaveGrad config/checkpoint, a bounded data directory, a small
`num_samples`, and explicit CPU/GPU runtime expectations before attempting it.
