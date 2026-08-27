# Training/Config/Data Troubleshooting

Use this matrix for failures before or during TTS training and fine-tuning. For package installation/import, PyTorch/torchaudio, CUDA installation, cache, and network failures, also check [../../../references/troubleshooting.md](../../../references/troubleshooting.md).

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `JSONDecodeError`, YAML parser error, or unsupported config extension | Invalid config syntax or file type. | Validate JSON/YAML syntax, use `.json`, `.yaml`, or `.yml`, remove trailing commas, and rerun `../scripts/validate_tts_config.py`. |
| `Config for <model> cannot be found` or registration failure | `model` key does not map to a registered config class, or legacy `generator_model` is wrong. | Correct `model` to a known value such as `glow_tts`, `vits`, `tacotron2`, `align_tts`, `fast_pitch`, or `xtts`. Do not train from a partially loaded dict. |
| `KeyError: model`, missing `datasets`, or empty dataset fields | Config is missing required top-level or dataset fields. | Add `model`, `output_path`, and a non-empty `datasets` list with `formatter`, `path`, and `meta_file_train`. |
| Dataset path not found | `BaseDatasetConfig.path` points to the wrong root. | Set `path` to the dataset root containing metadata and audio folders; rerun validation. |
| Metadata file not found | `meta_file_train` is wrong or interpreted relative to the dataset root. | Use the filename relative to `path` for built-in formatters, or the expected path for the custom formatter. |
| Wav files missing under `wavs/` for LJSpeech | Metadata basename does not match audio files or files are not converted to wav. | For `ljspeech`, rows use basename only and the formatter expects `wavs/<basename>.wav`. Convert/rename files or change formatter. |
| Common Voice rows load but audio missing | TSV `path` column points to `.mp3`, while the formatter expects converted `.wav` files under `clips/`. | Convert selected clips to wav or provide a custom formatter that reads the actual audio format. |
| Formatter column assertion or index error | Metadata delimiter/header does not match formatter expectations. | Check [data-formats.md](data-formats.md), fix columns, or write a custom formatter returning `text`, `audio_file`, `speaker_name`, and `root_path`. |
| Eval split assertion on a tiny dataset | `eval_split_size` produces zero eval samples or removes too many samples per speaker. | Provide `meta_file_val`, increase `eval_split_size`, use more samples, or validate paths with `--no-eval-split`. |
| `No phonemizer found`, `Phonemizer ... not found`, or language frontend error | `use_phonemes` is enabled but `phoneme_language`/`phonemizer` is missing or unsupported. | Set `phoneme_language`, choose `phonemizer`, use per-dataset language/phonemizer mapping for multilingual configs, or use graphemes. |
| `No espeak backend found`, `Cannot set backend automatically`, or empty ESpeak language list | System `espeak`/`espeak-ng` executable is missing. | Install `espeak-ng` or `espeak`, then rerun phoneme validation. If unavailable, disable phonemes or use a supported non-espeak phonemizer. |
| Unsupported Python version | Coqui TTS version inspected supports Python `>=3.9,<3.12`. | Use Python 3.9, 3.10, or 3.11 for package work. Do not debug training issues on unsupported Python first. |
| Training is extremely slow on CPU | Full TTS training is compute-heavy. | Use CPU only for validation/tiny smokes. For real training, use GPU, reduce model/batch sizes, or ask the user to approve a bounded run. |
| CUDA OOM during training | Batch, sequence length, audio length, model size, or workers exceed VRAM. | Lower `batch_size`/`eval_batch_size`, set `max_audio_len`/`max_text_len`, reduce loader workers, disable expensive options, use mixed precision when safe, or use `--grad_accum_steps` to preserve effective batch. |
| OOM occurs at the first batch only | Longest samples are too large or `start_by_longest` exposed the worst case. | Inspect clip/text length distribution, remove outliers, lower max lengths, or resample/trim audio through the vocoder/audio sub-skill. |
| Attention does not converge or align diagonally | Noisy/small dataset, too-long samples, too-small batch, bad text normalization, or unsuitable attention model. | Clean dataset, remove outliers, improve text cleaner/phonemes, increase effective batch when possible, monitor attention, or try alignment-friendly models such as AlignTTS/GlowTTS. |
| Tacotron decoder stops at `max_decoder_steps` or stopnet appears broken | Stopnet often fails when attention/dataset/audio trimming is poor. Silence at clip edges is a common contributor. | Check attention first, review `do_trim_silence`/`trim_db`, inspect spectrogram quality, clean clips, and avoid overlong samples. |
| Loss decreases but generated samples are poor | Audio parameters, text normalization, dataset quality, or vocoder pairing may be wrong. | Compare ground-truth and model spectrograms, verify sample rate/mel settings, inspect unique symbols, and route vocoder mismatch checks to [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |
| Checkpoint restore shape mismatch | Fine-tune config changed architecture, vocabulary, speaker/d-vector settings, or audio dimensions incompatible with checkpoint. | Restore compatible fields or choose a checkpoint trained with the desired config. Be cautious changing `characters`, phoneme mode, speaker embedding settings, and mel dimensions. |
| `--continue_path` resumes wrong config | Continue mode loads `config.json` from the previous experiment directory. | Use `--restore_path` plus an edited `--config_path` for fine-tuning with a new dataset; use `--continue_path` only to continue the same run. |
| XTTS fine-tuning tries to download files | XTTS GPT fine-tuning needs tokenizer, model, DVAE, and mel-norm files if not already present. | Ask for network approval or provide all file paths before starting. Validate dataset first. |
| XTTS GPT OOM or ineffective batch | XTTS recipe uses small per-device batch and large gradient accumulation; effective batch matters. | Reduce per-device batch, increase `grad_accum_steps` if quality/recipe target requires it, and prefer GPU. CPU is not a practical performance substitute. |
| Speaker embedding output has missing or duplicated keys | `dataset_name` changed, relative audio paths changed, or old speaker file was appended against a different dataset layout. | Keep `dataset_name` stable, validate `audio_unique_name` keys in dry-run, and append only when old/new keys are intentionally compatible. |

## Quick diagnostic sequence

```bash
python ../scripts/validate_tts_config.py --config-path config.json
python ../scripts/validate_tts_config.py --config-path config.json --load-samples --sample-preview 5
python ../scripts/find_unique_symbols.py --config-path config.json --mode chars
```

If phonemes are enabled:

```bash
python ../scripts/find_unique_symbols.py --config-path config.json --mode phonemes
```

Do not escalate to full training until these checks pass or their warnings are intentionally accepted.

