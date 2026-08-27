---
name: evaluation
description: "Evaluate Spleeter models on MUSDB-style datasets, dependency
  gates, output metrics, fixtures, and evaluation troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Spleeter evaluation router

Use this sub-skill when the task mentions `spleeter evaluate`, MUSDB or MUSDB-like test sets, `musdb`/`museval`, SDR/SAR/SIR/ISR, evaluation output directories, fake evaluation fixtures, or evaluation failures related to model downloads and caches.

Do not use this sub-skill for generic source separation recipes; route those to [separation](../separation/SKILL.md). Do not use it for training CSV/config construction except for a tiny evaluation fixture; route training work to [training](../training/SKILL.md).

## Fast route

| User intent | Go to |
| --- | --- |
| Install or check evaluation prerequisites | [Evaluation workflow](references/evaluation-workflow.md#dependency-gate) and root [installation/runtime](../../references/installation-and-runtime.md) |
| Run `spleeter evaluate` on a MUSDB-style dataset | [Evaluation workflow](references/evaluation-workflow.md#run-evaluation) |
| Understand `mus_dir` layout or distinguish ground truth from estimates | [MUSDB format and metrics](references/musdb-format-and-metrics.md) |
| Interpret SDR/SAR/SIR/ISR metrics or compiled medians | [Metric compilation behavior](references/musdb-format-and-metrics.md#metric-files-and-compilation) |
| Make a tiny deterministic fixture for smoke/layout checks | [`scripts/create_eval_fixture.py`](scripts/create_eval_fixture.py) and [fixture notes](references/musdb-format-and-metrics.md#tiny-fake-fixture) |
| Debug exit code 10, missing stems, cache/network, JSON metrics, or slow runs | [Evaluation troubleshooting](references/troubleshooting.md) |
| Compare evaluation CLI flags with the global CLI catalog | Root [CLI reference](../../references/cli-reference.md) |
| Select model descriptors, local configs, or cache/network policy | Root [models/configuration](../../references/models-and-configuration.md) |

## Core command shape

```bash
spleeter evaluate \
  --mus_dir MUSDB_ROOT \
  --output_path OUTPUT \
  --params_filename spleeter:4stems \
  --adapter spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter \
  --mwf \
  --verbose
```

`python -m spleeter evaluate ...` is equivalent when the console entry point is unavailable. Short forms supported by the CLI include `-o/--output_path`, `-p/--params_filename`, and `-a/--adapter`. `--mus_dir`, `--mwf`, and `--verbose` are long-form options.

## Keep these boundaries clear

- `MUSDB_ROOT/test/<song>/mixture.wav` is the mixture input that Spleeter separates.
- `MUSDB_ROOT/test/<song>/{vocals,drums,bass,other}.wav` are ground-truth source files required by `museval`; they are not Spleeter outputs.
- Evaluation writes Spleeter estimates under `OUTPUT/audio/test/<song>/` and metric JSON files under `OUTPUT/metrics/test/`.
- Base Spleeter installs may not include evaluation dependencies. If `musdb` or `museval` cannot import, Spleeter logs the missing extras and exits with status `10`.
- GPU use is optional acceleration only; the verified runtime path is TensorFlow CPU.

Evidence basis: `spleeter/__main__.py`, `spleeter/options.py`, `tests/test_eval.py`, `pyproject.toml`, `README.md`, and `configs/musdb_config.json`.
