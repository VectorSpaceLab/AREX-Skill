# Benchmark evaluator configuration

When the user is working in a target Otter checkout or deployment that includes the benchmark modules, the primary benchmark entry point is:

```bash
python -m pipeline.benchmarks.evaluate --config benchmark.yaml
```

`--config` may also be written as `-c`. Some source documentation examples spell it as `--confg`; that spelling is not accepted by the argparse parser and should be corrected before use.

## CLI flags

`pipeline.benchmarks.evaluate` accepts these flags:

| Flag | Meaning | Notes |
|---|---|---|
| `--config`, `-c` | YAML config file containing `models`, `datasets`, and optional top-level `output`. | Preferred for anything with credentials, custom splits, prompts, output paths, or dataset-specific options. |
| `--models` | Comma-separated model registry keys, such as `otter_image,fuyu`. | Only used when `--config` is omitted. |
| `--model_paths` | Comma-separated model paths paired with `--models`. | Count should match `--models`; the evaluator zips names and paths, so mismatches can silently drop entries. |
| `--datasets` | Comma-separated dataset registry keys, such as `mmbench,mme`. | Only used when `--config` is omitted. |
| `--output`, `-o` | Text evaluation report path. | Default is `./logs/evaluation.txt`. Use a path with a directory component, not a bare filename. |
| `--cache_dir` | Hugging Face dataset cache directory. | Only injected in non-config CLI mode. In YAML mode, put `cache_dir` inside each dataset entry. |

Minimal non-config form:

```bash
python -m pipeline.benchmarks.evaluate \
  --models otter_image \
  --model_paths /path/to/otter-image-checkpoint \
  --datasets mmbench,mme \
  --cache_dir /path/to/hf-cache \
  --output ./logs/evaluation.txt
```

Prefer YAML mode for multi-dataset production runs because per-dataset keys such as `api_key`, `gpt_model`, `prompt`, `default_output_path`, `split`, `debug`, and `cache_dir` are passed through to dataset constructors.

## YAML schema

Top-level schema:

```yaml
output: ./logs/evaluation.txt   # optional text report path; default is ./logs/evaluation.txt
models:
  - name: otter_image           # required registry key
    model_path: /path/to/model-or-checkpoint
    load_bit: bf16              # model-specific optional key

datasets:
  - name: mmbench               # required registry key
    split: test                 # dataset-specific optional key
    cache_dir: /path/to/hf-cache
    default_output_path: ./logs/MMBench
```

Rules that matter operationally:

- `models` and `datasets` must be non-empty lists of mappings.
- Every model and dataset entry must contain a string `name` that matches the exact registry key in [model-and-dataset-registry](model-and-dataset-registry.md).
- Extra keys are passed directly into the selected constructor; unknown keys can crash at runtime with `TypeError`.
- In YAML mode, there is no top-level `cache_dir` handling. Set `cache_dir` on each dataset entry that should use a non-default Hugging Face cache.
- `output` controls the evaluator's redirected text report. Dataset classes also write their own JSON/XLSX/CSV artifacts under `default_output_path`.
- Use output paths under a user-controlled run directory such as `./logs/...`; avoid overwriting prior result folders unless intentionally resuming/replacing.

## GPT-judged benchmark example

MagnifierBench, MM-VET, and MathVista perform GPT/API-assisted judging or extraction. Provide credentials explicitly or skip these datasets.

```yaml
output: ./logs/evaluation.txt
models:
  - name: fuyu
    model_path: adept/fuyu-8b
    resolution: 1440

datasets:
  - name: magnifierbench
    split: test
    data_path: Otter-AI/MagnifierBench
    prompt: Answer with the option letter from the given choices directly.
    api_key: ${OPENAI_API_KEY}
    default_output_path: ./logs/MagBench

  - name: mmvet
    split: test
    api_key: ${OPENAI_API_KEY}
    gpt_model: gpt-4-0613
    default_output_path: ./logs/MMVet

  - name: mathvista
    split: test
    api_key: ${OPENAI_API_KEY}
    gpt_model: gpt-4-0613
    default_output_path: ./logs/MathVista
```

Do not paste literal `${OPENAI_API_KEY}` into a final run config unless the surrounding launcher expands it first. The validator treats placeholder strings as missing credentials.

## Low-credential smoke config

A safer first config avoids GPT-judged datasets and still exercises the evaluator, registry, download/cache, and output paths:

```yaml
output: ./logs/evaluation.txt
models:
  - name: otter_image
    model_path: /path/to/otter-image-checkpoint
    load_bit: bf16

datasets:
  - name: mmbench
    split: test
    cache_dir: /path/to/hf-cache
    default_output_path: ./logs/MMBench

  - name: mme
    split: test
    cache_dir: /path/to/hf-cache
    default_output_path: ./logs/MME
```

Validate before launching:

```bash
python ../scripts/validate_benchmark_config.py benchmark.yaml
```

If the validator reports only missing credentials for datasets you intentionally plan to skip, remove those datasets or rerun validation with `--allow-missing-credentials` to produce a skip-oriented report rather than a launch-ready report.
