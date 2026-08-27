# Eval-Anything Notes

Eval-Anything is bundled under Align-Anything's projects tree, but it has its own package metadata, console script, model backend registry, benchmark registry, configs, and optional VLA dependencies. Treat it as a separate evaluation package surface. Do not assume a base Align-Anything environment can run it.

## Package Surface

| Evidence area | Distilled behavior |
| --- | --- |
| Package metadata | Package name `eval-anything`; Python requirement `>=3.11`; console script `eval-anything-cli = eval_anything.cli:main`. |
| Core dependencies | Includes `vllm >= 0.6.2`, `torch >= 1.13`, `transformers`, `datasets`, `accelerate`, `diffusers`, `peft`, `gradio`, audio/video/image packages, and several evaluation-specific packages. |
| Optional `vla` extra | Adds embodied/VLA stack pieces such as Objaverse tooling, AllenAct-related packages, geometry/scientific packages, and OpenCLIP/CLIP-related dependencies. This is not a lightweight extra. |
| CLI module | `eval_anything/cli.py` implements a Rich-based command dispatcher for `eval`, `version`, and `help`. The usage table also mentions `clean`, but the inspected dispatcher does not handle a `clean` branch. |
| Main module | `eval_anything/__main__.py` accepts `--eval_info` and unknown `--key value` overrides, instantiates `BaseTask`, and calls `iterate_run()`. |
| Configs | YAML files under `eval_anything/configs` hold `eval_cfgs`, `model_cfgs`, and `infer_cfgs`. The default inspected config uses a DoNotAnswer benchmark, `model_type: LM`, `infer_backend: vllm`, GPU ids, and a local model path placeholder. |
| Pipelines | `BaseTask` loads configs, creates the model, iterates benchmarks through `BenchmarkRegistry`, saves per-benchmark details, and optionally launches visualization. `BaseBenchmark` handles dataloading, inference batching, metrics, cache pairing, and benchmark result display. |

## CLI and Main-Module Flow

### Console script

After installing the Eval-Anything package in its own runtime, the intended CLI form is:

```bash
eval-anything-cli eval <config-file>
```

The `eval` subcommand parses:

- positional `config`, defaulting to `configs/evaluate.yaml` in the CLI parser;
- `--gpu`, parsed but not forwarded to the inspected `run_eval()` function;
- `--debug`, which only enables extra exception printing and logs a debug message.

The CLI then changes into the installed `eval_anything` package directory and runs:

```bash
python __main__.py --eval_info <config-file>
```

Implication: if a task needs GPU ids, prefer putting them in the YAML config or pass override keys through the main module rather than relying on the CLI `--gpu` flag.

### Main module

The main module accepts:

```bash
python -m eval_anything --eval_info evaluate.yaml [--nested:key value ...]
```

It parses unknown arguments and applies them as nested config overrides. The helper converts dashes to underscores, splits nested keys on `:`, and converts values such as `True`, `False`, numbers, bracketed lists, and comma-separated lists. Example override shapes to consider:

```bash
python -m eval_anything --eval_info evaluate.yaml \
  --infer-cfgs:num-gpu 1 \
  --infer-cfgs:gpu-ids '[0]' \
  --model-cfgs:model-name-or-path <model-path>
```

Validate the exact key names against the target YAML before relying on overrides.

## Config Anatomy

The inspected default-style config has three main sections:

| Section | Important fields | Notes |
| --- | --- | --- |
| `eval_cfgs` | `output_dir`, `cache_dir`, `task_uid`, `benchmarks`, `n_shot`, `cot`, `visualization` | `benchmarks` maps benchmark names to task lists. Empty task lists can mean "use the benchmark default task list" inside benchmark code. |
| `model_cfgs` | `model_id`, `model_name_or_path`, `model_type`, `chat_template` | `model_type` participates in backend-class key construction. Local model paths in configs must be replaced by user-provided paths. |
| `infer_cfgs` | `infer_backend`, `trust_remote_code`, generation parameters, `num_gpu`, `gpu_ids`, `gpu_utilization` | Backend plus model type selects the model implementation. vLLM settings require compatible GPU resources. |

## Model Backend Selection

`BaseTask.load_model()` builds a key from `{infer_backend}_{model_type}` and uses registries in `models/base_model.py`:

| Key | Module | Class |
| --- | --- | --- |
| `vllm_LM` | `eval_anything.models.vllm_lm` | `vllmLM` |
| `vllm_MM` | `eval_anything.models.vllm_mm` | `vllmMM` |
| `hf_LM` | `eval_anything.models.hf_lm` | `HFLM` |
| `hf_MM` | `eval_anything.models.hf_mm` | `HFMM` |
| `hf_VLA` | `eval_anything.models.hf_vla` | `HFVLA` |
| `api_LM` | `eval_anything.models.api_lm` | `APILM` |
| `api_MM` | `eval_anything.models.api_mm` | `APIMM` |

If a key is missing, fix `infer_backend` or `model_type` in the config rather than editing the registry casually.

## Benchmark and Pipeline Shape

`BaseTask.iterate_run()`:

1. Reads the configured benchmark dictionary from `eval_cfgs.benchmarks`.
2. Retrieves each benchmark evaluator through `BenchmarkRegistry.get_benchmark(benchmark_name)`.
3. Builds inference inputs with the evaluator dataloader.
4. Runs model generation.
5. Calculates metrics and optional overall metrics.
6. Saves per-benchmark details and task-level results.

`BaseBenchmark` maintains a benchmark-to-modality map for many text, multimodal, safety, and VLA benchmarks. It loads benchmark-specific configs from package benchmark folders, calls registered answer extractors and metric calculators, batches inference, and pairs inputs/outputs by UUID for detail files.

Use this as reference evidence for extending benchmarks or debugging config/model mismatch. Treat an actual Eval-Anything run as a separate evaluation task that needs its own runtime and data readiness checks.

## VLA Notes

The README's VLA flow requires:

1. Downloading Objaverse annotations/assets.
2. Downloading Objaverse house assets.
3. Downloading benchmark datasets.
4. Installing `.[vla]` plus specific AI2-THOR and AllenAct packages.
5. Running the VLA shell entrypoint.

This is a heavy, side-effecting runtime. Do not classify VLA as runnable from the base Align-Anything repo skill unless the user has explicitly prepared and approved these assets and dependencies.

## Treat as Reference Unless Prepared

Use Eval-Anything as reference-only when any of the following are unresolved:

- No dedicated Eval-Anything installation or package import proof.
- vLLM/HF/API backend dependencies not installed.
- Model path/API credentials missing.
- Dataset assets or benchmark configs missing.
- GPU allocation incompatible with `num_gpu`, `gpu_ids`, or vLLM memory needs.
- VLA assets/extras absent for embodied tasks.

When prepared, the safest small run is a single lightweight text benchmark with a small local or API model, a temporary output/cache directory, visualization disabled, and explicit GPU/API configuration in the YAML or overrides.
