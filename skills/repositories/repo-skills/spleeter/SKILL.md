---
name: spleeter
description: "Route Spleeter source-separation CLI, Python API, training, and
  MUSDB evaluation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Spleeter repo skill

Use this skill when the task names **Spleeter**, `spleeter separate`, `spleeter train`, `spleeter evaluate`, Deezer source separation, pretrained 2/4/5-stem music demixing, `Separator`, `AudioAdapter`, Spleeter JSON configs, MUSDB evaluation, or Spleeter-specific TensorFlow/ffmpeg/model-cache failures.

Spleeter 2.4.2 is a Python package for audio/music source separation using TensorFlow. It offers pretrained vocal/accompaniment and multi-stem models, a Typer CLI, a Python `Separator` API, training utilities for custom source-separation models, and MUSDB-style evaluation with optional extras.

## Start here

1. Confirm runtime basics with [scripts/check_install.py](scripts/check_install.py) or these minimal checks:

   ```bash
   python -m spleeter --version
   python -m spleeter --help
   ffmpeg -version
   ffprobe -version
   ```

2. Read [installation and runtime](references/installation-and-runtime.md) when setup, Python/TensorFlow versions, optional dependencies, ffmpeg, Windows, Apple Silicon, or GPU expectations matter.
3. Read [CLI reference](references/cli-reference.md) before constructing command-line calls.
4. Read [models and configuration](references/models-and-configuration.md) for `spleeter:` descriptors, model cache/download behavior, and custom JSON config loading.
5. For failures that are not clearly owned by one workflow, start with [root troubleshooting](references/troubleshooting.md), then route to the nearest sub-skill troubleshooting page.

## Workflow routes

| Task family | Read |
| --- | --- |
| Split local audio into vocals/accompaniment or 4/5 stems; choose pretrained descriptor; build `spleeter separate` commands; use `Separator`/`AudioAdapter`; handle filename templates, codecs, MWF, and output validation | [separation](sub-skills/separation/SKILL.md) |
| Prepare custom training CSVs/configs; validate data layout and STFT dimensions; generate tiny training fixtures; run or adapt `spleeter train`; troubleshoot caches/checkpoints/TensorFlow training | [training](sub-skills/training/SKILL.md) |
| Evaluate a Spleeter model on MUSDB-style `test/<song>/` data; install `spleeter[evaluation]`; interpret SDR/SAR/SIR/ISR; generate a tiny evaluation fixture; troubleshoot exit code 10, missing sources, and metrics output | [evaluation](sub-skills/evaluation/SKILL.md) |

## Capability boundaries

- Use this skill for **operating Spleeter as a package**, not for general audio DSP, generic TensorFlow training, unrelated source-separation libraries, or repository release engineering.
- The verified baseline is a CPU TensorFlow runtime with system `ffmpeg`/`ffprobe`. GPU acceleration can improve speed but is optional and must be verified in the user's active TensorFlow environment before promising GPU execution.
- Pretrained separation and evaluation may download model artifacts on first use. Treat first-run network/cache policy as part of the task plan.
- Spleeter's `-i/--inputs` style is deprecated in this version. Pass audio files as positional arguments to `spleeter separate`.
- Evaluation dependencies are optional: base Spleeter can import and run separation/training help, but `spleeter evaluate` requires `musdb` and `museval` from `spleeter[evaluation]`.

## Common entry points

| Surface | Use |
| --- | --- |
| `python -m spleeter separate -p spleeter:2stems -o separated song.wav` | Basic vocal/accompaniment split; see [separation workflows](sub-skills/separation/references/workflows.md). |
| `from spleeter.separator import Separator` | Python API for in-memory waveforms and file outputs; see [separation API](sub-skills/separation/references/api-reference.md). |
| `python -m spleeter train -d DATA_ROOT -p CONFIG.json` | Custom model training; validate first with [training scripts](sub-skills/training/SKILL.md). |
| `python -m spleeter evaluate --mus_dir MUSDB_ROOT -o OUTPUT -p spleeter:4stems` | MUSDB-style metrics; see [evaluation workflow](sub-skills/evaluation/references/evaluation-workflow.md). |
| `spleeter:2stems`, `spleeter:4stems`, `spleeter:5stems` | Embedded pretrained descriptors; see [models and configuration](references/models-and-configuration.md). |

## Evidence and provenance

This skill was distilled from Spleeter 2.4.2 source, package metadata, public README/CHANGELOG/notebook examples, embedded resource configs, and native tests. See [repo provenance](references/repo-provenance.md) for the source commit and evidence paths, and [repo routing metadata](references/repo-routing-metadata.json) for managed router placement.
