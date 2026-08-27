---
name: separation
description: "Guides Spleeter pretrained music source separation with CLI and
  Python APIs for vocals, accompaniment, and 2/4/5-stem outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Spleeter separation

Use this sub-skill when the task is to split local music/audio into pretrained Spleeter stems: vocals/accompaniment, 4-stem vocals/drums/bass/other, 5-stem vocals/drums/bass/piano/other, CLI `spleeter separate`, Python `Separator`, `AudioAdapter`, ffmpeg load/save, filename templates, MWF, or model first-run download/cache failures.

## Route first

| User need | Go to |
| --- | --- |
| Build or run separation commands, choose 2/4/5 stems, slice audio, batch files, choose output names/codecs, or validate stem outputs | [workflow recipes](references/workflows.md) |
| Use `Separator`, `separate`, `separate_to_file`, `save_to_file`, `AudioAdapter`, `FFMPEGProcessAudioAdapter`, or `Codec` in Python | [API reference](references/api-reference.md) |
| Diagnose ffmpeg, bad audio paths, deprecated `-i`, output conflicts, model download/cache, TensorFlow warnings, Windows, or Apple Silicon issues | [separation troubleshooting](references/troubleshooting.md) |
| Safely assemble and dry-run a public CLI call from installed Spleeter | [scripts/separate_file.py](scripts/separate_file.py) |
| Install/runtime prerequisites, Python/TensorFlow constraints, ffmpeg checks, optional GPU note | [root installation reference](../../references/installation-and-runtime.md) |
| Full CLI option catalog for `separate`, `train`, and `evaluate` | [root CLI reference](../../references/cli-reference.md) |
| Embedded descriptors, model cache/download variables, local JSON configs | [root models/configuration reference](../../references/models-and-configuration.md) |

## Separation boundaries

- Include `spleeter separate FILES...` with `--output_path/-o`, `--params_filename/-p`, `--filename_format/-f`, `--codec/-c`, `--bitrate/-b`, `--offset/-s`, `--duration/-d`, `--mwf`, `--adapter/-a`, and `--verbose`.
- Do **not** use deprecated `-i` or `--inputs`; Spleeter 2.4.2 exits with code 20 for that form. Pass audio files as positional arguments.
- Use model descriptors such as `spleeter:2stems`, `spleeter:4stems`, `spleeter:5stems`, and their `-16kHz` variants at a high level; read the root models/configuration reference for cache and custom descriptor details.
- Route custom model training, training CSVs, and Spleeter training configs to [training](../training/SKILL.md).
- Route MUSDB evaluation, `spleeter evaluate`, `musdb`, `museval`, and metrics interpretation to [evaluation](../evaluation/SKILL.md).

## Minimal operating plan

1. Confirm runtime basics: `python -m spleeter --version`, `python -m spleeter separate --help`, and system `ffmpeg`/`ffprobe` availability.
2. Choose a model descriptor: `spleeter:2stems` for vocals/accompaniment, `spleeter:4stems` for vocals/drums/bass/other, or `spleeter:5stems` when piano should be separated too.
3. Prefer a short `--duration` smoke run before a long batch. The first run for a descriptor may download and checksum pretrained model files.
4. Keep filename templates collision-safe: include `{instrument}` and, for multi-file jobs, usually `{filename}` or `{foldername}`.
5. Validate the expected stem files are present, non-empty, and decodable before using them downstream.
