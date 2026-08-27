# Source Script Map

## Purpose

This reference explains how repo-maintained scripts and examples were converted into self-contained skill helpers or distilled as safety-bounded recipes. Runtime instructions should use the bundled helper paths named here, not original repository scripts.

## Bundled Helper Ownership

| Workflow | Bundled helper | Owner | Source evidence distilled | Safety behavior |
| --- | --- | --- | --- | --- |
| Import/registry/backend check | `scripts/check_open_clip_env.py` | Root | Package metadata, public imports, registry APIs | Imports only; no downloads or model weight loading. |
| Image/text inference smoke | `sub-skills/model-inference/scripts/inference_smoke.py` | `model-inference` | README inference pattern, factory/tokenizer/transform tests | Defaults to `pretrained=None`, generated image, CPU fp32; download-prone paths require explicit flag. |
| Training parser inspection | `sub-skills/training/scripts/training_arg_report.py` | `training` | Training parser and README command families | Parses args only; no model, data loader, distributed group, checkpoint, or training. |
| CSV/TSV data validation | `sub-skills/training/scripts/validate_csv_dataset.py` | `training` | CSV data tests and loader contracts | Checks columns, caption values, image paths; does not decode images or train. |
| Audio config inspection | `sub-skills/audio-clap/scripts/audio_config_report.py` | `audio-clap` | Audio config/default tests and model configs | Reports audio availability/config fields without weights or datasets. |
| Audio zero-shot argument plan | `sub-skills/audio-clap/scripts/clap_zero_shot_args.py` | `audio-clap` | Audio zero-shot script and tests | Validates flags/templates and prints a plan; no checkpoint loading, dataset download, or evaluation. |
| NaFlex config report | `sub-skills/naflex-generative/scripts/naflex_config_report.py` | `naflex-generative` | NaFlex parser/config tests | Validates patch/sequence/token-budget settings without model construction. |
| GenLIP scoring plan | `sub-skills/naflex-generative/scripts/genlip_scoring_args.py` | `naflex-generative` | GenLIP zero-shot/probe scripts | Reports cost and options; no ImageNet read, checkpoint load, or model forward. |
| Zero-shot classifier smoke | `sub-skills/evaluation-conversion/scripts/zero_shot_classifier_smoke.py` | `evaluation-conversion` | Zero-shot classifier tests | Uses tiny deterministic fake features; no downloads or datasets. |
| Checkpoint key report | `sub-skills/evaluation-conversion/scripts/checkpoint_key_report.py` | `evaluation-conversion` | Task/checkpoint, conversion, and key-prefix tests | CPU state-dict inspection with safe defaults; no mutation or export. |

## Reference-Only Source Families

- Long training shell launchers and script-example launchers were treated as recipe evidence because they assume large datasets, checkpoints, distributed resources, cluster paths, or long training runs.
- Audio zero-shot and GenLIP probe scripts were distilled into argument-planning helpers because the full workflows require checkpoints, Hugging Face/ImageNet data, downloads, GPU, or expensive forwards.
- Notebook-style examples were distilled into references because future agents should not depend on notebook files, Colab state, or original checkout paths at runtime.
- Conversion code is documented through safe key-reporting and API guidance; helpers do not perform irreversible export or upload operations.

## Runtime Rule

When a task needs executable support, start with the bundled helper owned by the nearest sub-skill. Treat original scripts and tests as provenance evidence only, not runtime dependencies.
