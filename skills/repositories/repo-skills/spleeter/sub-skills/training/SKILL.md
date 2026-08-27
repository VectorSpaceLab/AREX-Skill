---
name: training
description: "Train and validate custom Spleeter source-separation models with
  safe data and config helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Spleeter Training

Use this sub-skill when the task is about custom Spleeter model training: `spleeter train`, training CSVs, custom stems, `model_dir` checkpoints, `DatasetBuilder`, `get_training_dataset`, `get_validation_dataset`, config validation, cache directories, or TensorFlow estimator training behavior.

Do **not** use this sub-skill for pretrained separation or MUSDB metrics:

- Pretrained model separation, `Separator`, output stems, codecs, and filename templates: [separation](../separation/SKILL.md).
- MUSDB evaluation, `spleeter evaluate`, `musdb`/`museval`, and SDR/SAR/SIR/ISR reports: [evaluation](../evaluation/SKILL.md).

## Fast route

1. Confirm runtime prerequisites in [installation and runtime](../../references/installation-and-runtime.md): Python `>=3.8,<3.12`, Spleeter 2.4.2, TensorFlow 2.12.1, and system `ffmpeg`/`ffprobe`. GPU is optional acceleration only; CPU training is supported but slow for real datasets.
2. For the training command and Typer option spellings, see [root CLI reference](../../references/cli-reference.md) and the workflow recipe in [training-workflow.md](references/training-workflow.md).
3. Build or validate the data/config contract before starting TensorFlow:
   - Create a tiny local fixture: [scripts/create_training_fixture.py](scripts/create_training_fixture.py).
   - Validate a Spleeter-style config and CSVs: [scripts/validate_training_config.py](scripts/validate_training_config.py).
   - Schema and compatibility rules: [data-format-and-config.md](references/data-format-and-config.md).
4. For programmatic dataset construction or estimator adaptation, use [api-reference.md](references/api-reference.md).
5. For failures, first check [training troubleshooting](references/troubleshooting.md), then cross-cutting package issues in [root troubleshooting](../../references/troubleshooting.md).

## Command shape

The supported training CLI shape is:

```bash
python -m spleeter train \
  --data DATA_ROOT \
  --params_filename CONFIG.json \
  --adapter spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter \
  --verbose
```

Short aliases are `--data/-d`, `--params_filename/-p`, and `--adapter/-a`. `CONFIG.json` must describe the dataset CSVs, STFT dimensions, source instruments, caches, checkpoint settings, and model function. CSV audio paths are relative to `--data DATA_ROOT`.

## Evidence basis

This sub-skill distills the training surfaces evidenced by `spleeter/__main__.py`, `spleeter/dataset.py`, `spleeter/model/__init__.py`, `spleeter/model/functions/unet.py`, `spleeter/utils/configuration.py`, `spleeter/utils/tensor.py`, `spleeter/resources/*.json`, `configs/musdb_config.json`, `configs/musdb_train.csv`, `configs/musdb_validation.csv`, `tests/test_train.py`, and `pyproject.toml`.
