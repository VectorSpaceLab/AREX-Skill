# Training/Config/Data API Reference

This reference is compact and self-contained. It lists the installed package surfaces this sub-skill relies on.

## Verified package constraints

| Fact | Value |
| --- | --- |
| Distribution/import | `TTS` / `import TTS` |
| Version inspected | `0.22.0` |
| Supported Python range | `>=3.9,<3.12` |
| Optional phoneme dependencies | Workflows may require `gruut`, `espeak`, or `espeak-ng`. |

## Core config signatures

```text
BaseAudioConfig(... sample_rate=22050, hop_length=256, num_mels=80, signal_norm=True, do_trim_silence=True, trim_db=45, ...)
BaseDatasetConfig(formatter='', dataset_name='', path='', meta_file_train='', ignored_speakers=None, language='', phonemizer='', meta_file_val='', meta_file_attn_mask='')
BaseTrainingConfig(... output_path='output', run_name='run', dashboard_logger='tensorboard', epochs=1000, batch_size=32, eval_batch_size=16, mixed_precision=False, distributed_backend='nccl', ...)
load_tts_samples(datasets, eval_split=True, formatter=None, eval_split_max_size=None, eval_split_size=0.01)
```

## Loading and registration

| Surface | Contract |
| --- | --- |
| `TTS.config.load_config(config_path)` | Loads `.json`, `.yaml`, or `.yml`; JSON with comments has a compatibility fallback; unsupported extensions raise `TypeError`. It extracts `model` or `generator_model`, registers the matching config, and returns a populated Coqpit object. |
| `TTS.config.register_config(model_name)` | Locates config classes across TTS, vocoder, encoder, and voice-conversion config modules. For this sub-skill, use it to validate TTS `model` names before training. Unknown names raise `ModuleNotFoundError`. |
| `config.check_values()` | Many config classes implement value range checks. Run when available, but still separately validate user file paths and dataset metadata. |
| `config.parse_known_args([...], relaxed_parser=True)` | Allows `--coqpit.<field>` style overrides after config load. Useful for safe command construction. |

## Dataset loading

`load_tts_samples()` accepts a single dataset config or a list. It returns `(train_samples, eval_samples)`, where samples are dictionaries with formatter keys plus `language` and `audio_unique_name` added by the loader.

Important behaviors:

- If `formatter` argument is `None`, the dataset's `formatter` string is resolved against installed formatter functions.
- If `meta_file_val` is set, it is loaded as validation metadata.
- Otherwise, the loader creates an eval split controlled by `eval_split_size` and `eval_split_max_size`.
- Very small datasets can fail eval split assertions; use an explicit validation file, a larger split, or `eval_split=False` for path-only checks.

## Text/tokenizer surfaces

| Surface | Use |
| --- | --- |
| `TTSTokenizer.init_from_config(config)` | Initializes cleaner, characters, phonemizer, blank/BOS/EOS behavior from a Coqpit config. |
| `Graphemes`, `IPAPhonemes`, `CharactersConfig` | Character/vocabulary definitions. Use unique-symbol scans before creating custom vocabularies. |
| `get_phonemizer_by_name(name, **kwargs)` | Instantiates named phonemizers such as `espeak`, `gruut`, and language-specific phonemizers. |
| `DEF_LANG_TO_PHONEMIZER` | Maps language codes to default phonemizer names when available. Missing keys mean the language needs explicit handling or extra dependencies. |

## Training parser surface

The installed TTS training parser exposes Trainer flags including:

```text
--config_path
--continue_path
--restore_path
--use_ddp
--use_accelerate
--grad_accum_steps
--small_run
--gpu
```

Use module execution for commands:

```bash
python -m TTS.bin.train_tts --config_path config.json
```

Do not use training as a validation step unless the user explicitly requested a training run.

## Bundled helper scripts

| Script | Source decision | What it does safely |
| --- | --- | --- |
| `../scripts/validate_tts_config.py` | Wraps training/config loading behavior instead of copying the training script. | Loads config, checks registration/config values, validates dataset/audio paths, and can optionally load samples. It does not initialize a model or call Trainer. |
| `../scripts/find_unique_symbols.py` | Adapts unique-character and unique-phoneme utilities into one bounded helper. | Reports character or phoneme inventories from configured datasets with clearer phonemizer errors. |
| `../scripts/compute_speaker_embeddings.py` | Wraps speaker-embedding computation with safer argument gates. | Requires explicit encoder model/config/dataset; dry-runs by default; computes only with `--run`. |

## Reference-only or excluded script decisions

| Utility/workflow | Decision | Reason |
| --- | --- | --- |
| TTS training entry module | Reference/wrap | Training is expensive; validation and command templates are safer than bundling a training launcher. |
| Speaker embedding computation | Wrapped | Useful for d-vectors but can be slow and historically had network-default encoder paths; the bundled wrapper requires explicit paths. |
| Unique chars/phonemes | Adapted | Safe, dataset-preparation-oriented, and useful before changing vocabularies. |
| Attention-mask computation | Reference-only | Requires a compatible trained checkpoint and writes many side-effect files. |
| Teacher-forced spectrogram extraction | Route/reference-only | Requires trained checkpoints and writes feature files; vocoder/audio ownership belongs to [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |
| Encoder training/evaluation | Reference-only | Requires trained encoder artifacts or training-scale setup, outside default config/data validation. |
| Maintainer README sync | Excluded | Mutates package documentation and is not a user operating workflow. |

