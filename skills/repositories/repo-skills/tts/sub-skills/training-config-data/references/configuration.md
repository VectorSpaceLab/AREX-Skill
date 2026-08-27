# Coqui TTS Configuration Guide

Coqui TTS uses Coqpit dataclass configurations. A TTS training config combines model architecture, dataset definitions, audio processing parameters, tokenizer/phonemizer settings, and Trainer options in one serializable JSON/YAML object.

## Configuration hierarchy

| Layer | Primary classes/functions | What it controls |
| --- | --- | --- |
| Loader/registration | `TTS.config.load_config`, `TTS.config.register_config` | Reads JSON/YAML, extracts `model` or legacy `generator_model`, locates the matching config class, and populates a Coqpit object. |
| Training base | `BaseTrainingConfig` | Shared Trainer fields such as `output_path`, `run_name`, `epochs`, `batch_size`, `eval_batch_size`, logger, distributed backend, precision, and loader worker counts. |
| Audio base | `BaseAudioConfig` | Feature extraction settings used by the dataloader/loggers: `sample_rate`, `hop_length`, `win_length`, `num_mels`, normalization, trimming, mel bounds, stats path. |
| Dataset base | `BaseDatasetConfig` | Dataset formatter name, root path, metadata files, dataset name, ignored speakers, language, dataset-level phonemizer, and attention-mask metadata. |
| TTS base | `BaseTTSConfig` | TTS-specific fields: `audio`, `datasets`, `text_cleaner`, `use_phonemes`, `phoneme_language`, `characters`, eval split settings, length filters, sampler options, optimizer/lr scheduler fields. |
| Model config | `GlowTTSConfig`, `VitsConfig`, `TacotronConfig`, `Tacotron2Config`, `AlignTTSConfig`, `FastPitchConfig`, `Fastspeech2Config`, `XttsConfig`, and other TTS config classes | Model-specific architecture and training defaults. |

## Model registration names

`load_config()` needs a model name that maps to a registered config class. Common TTS values include:

| `model` value | Typical config class | Notes |
| --- | --- | --- |
| `glow_tts` | `GlowTTSConfig` | Good recipe-style starting point; flow/duration model. |
| `vits` | `VitsConfig` | End-to-end TTS with integrated neural vocoder behavior; keep vocoder-specific routing separate when training standalone vocoders. |
| `tacotron`, `tacotron2` | `TacotronConfig`, `Tacotron2Config` | Attention-based; monitor attention and stopnet closely. |
| `align_tts` | `AlignTTSConfig` | Useful when attention alignment is a concern. |
| `fast_pitch`, `fast_speech`, `fastspeech2`, `speedy_speech` | Forward-TTS-style configs | May need alignments/durations depending on workflow. |
| `xtts` | `XttsConfig` or XTTS trainer configs | Released XTTS inference and GPT fine-tuning have special checkpoint/download caveats; see [fine-tuning.md](fine-tuning.md). |
| `bark`, `tortoise` | `BarkConfig`, `TortoiseConfig` | More specialized workflows; avoid assuming ordinary `train_tts` behavior. |

If `load_config()` raises a registration error, fix the `model` key first. Do not work around it by starting training from a partially parsed dict.

## Minimum config skeleton

This skeleton is intentionally small. Model defaults fill many fields, but dataset and audio fields must match the user's data.

```json
{
  "model": "glow_tts",
  "run_name": "my-glowtts-run",
  "output_path": "runs/tts",
  "batch_size": 32,
  "eval_batch_size": 16,
  "epochs": 1000,
  "text_cleaner": "phoneme_cleaners",
  "use_phonemes": true,
  "phoneme_language": "en-us",
  "phoneme_cache_path": "runs/phoneme-cache",
  "audio": {
    "sample_rate": 22050,
    "hop_length": 256,
    "win_length": 1024,
    "num_mels": 80,
    "do_trim_silence": true,
    "trim_db": 45
  },
  "datasets": [
    {
      "formatter": "ljspeech",
      "dataset_name": "my_ljspeech_style_data",
      "path": "data/my_dataset",
      "meta_file_train": "metadata.csv",
      "language": "en-us"
    }
  ]
}
```

## Dataset config fields to check

| Field | Required? | Expected value |
| --- | --- | --- |
| `formatter` | Yes | Built-in formatter name such as `ljspeech`, `common_voice`, `coqui`, `vctk`, or a custom formatter passed to `load_tts_samples()`. |
| `dataset_name` | Strongly recommended | Stable unique name; used in generated `audio_unique_name` keys and multi-dataset logs. |
| `path` | Yes | Dataset root directory. Keep it outside the skill tree. |
| `meta_file_train` | Yes for most formatters | Metadata filename or path interpreted by the selected formatter. |
| `meta_file_val` | Optional | Explicit validation metadata; otherwise eval split is derived from train metadata. |
| `ignored_speakers` | Optional | List of speaker ids to skip for multi-speaker formatters. |
| `language` | Recommended; required for some multi-lingual or phoneme workflows | Language code attached to every sample; dataset-level language can override global assumptions. |
| `phonemizer` | Optional | Dataset-level phonemizer name; required for `multi_phonemizer` setups. |
| `meta_file_attn_mask` | Specialized | Attention-mask metadata for duration-predictor workflows; do not set unless those masks were computed intentionally. |

## Audio fields that affect data compatibility

| Field | Why it matters |
| --- | --- |
| `sample_rate` | Must match, or intentionally resample, the dataset audio. Mismatches affect training speed and quality. |
| `num_mels`, `fft_size`, `win_length`, `hop_length` | Must stay compatible with any checkpoint/vocoder pairing used later. For vocoder-specific details route to [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |
| `do_trim_silence`, `trim_db` | Silence handling affects attention and stopnet behavior. Too aggressive or too weak trimming can break convergence. |
| `mel_fmin`, `mel_fmax` | Tune for speaker pitch range and dataset; wrong values can degrade spectrogram quality. |
| `stats_path` | Points to computed normalization stats; validate existence if set. Audio-stat generation is owned by [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |

## Tokenizer and phonemizer fields

| Field | Typical use |
| --- | --- |
| `text_cleaner` | Text normalization such as number/abbreviation expansion. `basic_cleaners` is a low-assumption fallback; language-specific cleaners may be better. |
| `use_phonemes` | When true, text is converted through a phonemizer before tokenization. |
| `phoneme_language` | Global language code used to choose a default phonemizer. Must be set for phoneme mode unless a multi-phonemizer dataset mapping is used. |
| `phonemizer` | Explicit phonemizer name such as `espeak`, `gruut`, or `multi_phonemizer`. |
| `phoneme_cache_path` | Cache directory for computed phonemes; useful for faster dataloading after the first pass. |
| `characters` | Explicit grapheme/phoneme vocabulary. Use `scripts/find_unique_symbols.py` before hard-coding a new alphabet. |
| `add_blank`, `enable_eos_bos_chars` | Token sequence decorations used by some architectures; keep compatible with the selected model/config. |

## Safe validation procedure

From this sub-skill directory, validate before any training command:

```bash
python scripts/validate_tts_config.py --config-path config.json
```

For a data-loader dry-run, add:

```bash
python scripts/validate_tts_config.py --config-path config.json --load-samples --sample-preview 5
```

For a tiny dataset that cannot form an eval split yet, add `--no-eval-split`.

Then inspect text coverage:

```bash
python scripts/find_unique_symbols.py --config-path config.json --mode chars
```

Use phoneme mode only after accepting optional language frontend requirements:

```bash
python scripts/find_unique_symbols.py --config-path config.json --mode phonemes
```

