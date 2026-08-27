# Benchmarking timm Models

`timm` includes a benchmark entry point for synthetic-input performance checks. It builds a model with `timm.create_model`, resolves the model data config, creates random inputs, runs warmup iterations, then reports timing and optional profiler-derived counts.

## Benchmark Modes

| Mode | `--bench` value | What it runs | Main output fields |
| --- | --- | --- | --- |
| Inference | `inference` | Forward pass in eval mode | `infer_samples_per_sec`, `infer_step_time`, `infer_batch_size`, `infer_img_size`, optional `infer_gmacs`, optional `infer_macts` |
| Train step | `train` | Forward, loss, backward, optimizer step on synthetic labels | `train_samples_per_sec`, `train_step_time`, `train_batch_size`, `train_img_size`; with `--detail`, also `train_fwd_time`, `train_bwd_time`, `train_opt_time` |
| Combined | `both` | Inference followed by train step | Inference and train-prefixed fields plus shared `param_count` |
| Profile | `profile`, `profile_deepspeed`, `profile_fvcore` | FLOP/activation profile instead of timing loop | `infer_gmacs`, optional `infer_macts`, `infer_batch_size`, `infer_img_size`, `param_count` |

The parser help says the default benchmark mode is `both`. For quick checks, prefer `--bench inference` unless the user explicitly needs train-step cost.

## Important Flags

| Flag | Purpose | Safe default guidance |
| --- | --- | --- |
| `--model` / `-m` | Model architecture or wildcard-like model filter | Use one exact model first, such as `resnet50` or a fully qualified pretrained-weight model name. |
| `--model-list` | Text file containing models, one per line | Use only for a reviewed, short list; it can run many models. |
| `--bench` | Selects `inference`, `train`, `both`, or `profile*` | Use `inference` for fast smoke checks; use `both` only when training memory fits. |
| `--device` | Device string such as `cuda`, `cuda:0`, `cpu`, or backend-specific values supported by PyTorch | Do not compare CPU and GPU rows as if they measure the same system. |
| `--batch-size` / `-b` | Synthetic mini-batch size | Start low, increase only after memory is stable. Benchmark has retry logic unless `--no-retry` is set. |
| `--num-warm-iter` | Warmup iterations before timing | Use 1-3 for debug, 10+ for more stable GPU runs. |
| `--num-bench-iter` | Timed iterations | Use 3-5 for debug, 40+ for steadier reporting when cost is acceptable. |
| `--precision` | Numeric mode: `float32`, `float16`, `bfloat16`, `amp`, or `amp_bfloat16` | Prefer `float32` for CPU and baseline checks; use AMP modes only when supported by hardware. |
| `--amp` and `--amp-dtype` | Convenience AMP switch; overrides `--precision` | `--amp --amp-dtype float16` maps to AMP fp16; `--amp --amp-dtype bfloat16` maps to AMP bf16. |
| `--channels-last` | NHWC memory layout | Compare only with other NHWC runs on similar hardware/software. |
| `--torchcompile [BACKEND]` | Enables `torch.compile`, default backend `inductor` | Expect first-run compile overhead and potential unsupported-model failures. |
| `--torchcompile-mode` | Optional compile mode | Keep unset unless the user is deliberately tuning compile behavior. |
| `--img-size`, `--input-size`, `--use-train-size` | Override input dimensions | Record the chosen size; result CSVs include image size because resolution changes cost. |
| `--results-file`, `--results-format` | Writes CSV or JSON results | Use a run-specific filename that encodes mode/device/precision/layout. |
| `--detail` | Adds train fwd/bwd/optimizer breakdown | Useful for train-step diagnosis; not meaningful for inference-only mode. |
| `--no-retry` | Disables batch-size decay retry on errors | Leave off for exploratory GPU runs; enable only when fixed-batch failure is the desired signal. |

## Bounded Command Patterns

Single-model debug inference:

```bash
python benchmark.py --model resnet50 --bench inference --device cuda --batch-size 32 --num-warm-iter 2 --num-bench-iter 5 --amp
```

More stable single-model inference with output file:

```bash
python benchmark.py --model resnet50 --bench inference --device cuda --batch-size 128 --num-warm-iter 10 --num-bench-iter 40 --amp --results-file benchmark-resnet50-infer-amp.csv
```

Train-step timing with details:

```bash
python benchmark.py --model resnet50 --bench train --device cuda --batch-size 32 --num-warm-iter 5 --num-bench-iter 20 --amp --detail
```

Profile with optional profiler packages:

```bash
python benchmark.py --model resnet50 --bench profile_fvcore --device cuda --batch-size 1
```

CPU smoke check:

```bash
python benchmark.py --model resnet50 --bench inference --device cpu --batch-size 1 --num-warm-iter 1 --num-bench-iter 3 --precision float32
```

## Bulk and Wildcard Runs

`benchmark.py` accepts `--model all`, wildcard-style model names, and `--model-list`. These can expand to many models inside one process. `bulk_runner.py` can launch a separate subprocess per model and merge results. Treat both as high-cost operations.

Safe handling for all-model or pretrained benchmark requests:

1. Ask the user for the target model family, exact model-list file, device, precision, and maximum number of models.
2. Produce a dry-run or reviewable command first.
3. Use low iterations and small batch size for the first pass.
4. Add `--delay` when using per-model subprocess launching to reduce thermal and memory pressure.
5. Save results to a run-specific CSV and include sort key expectations.

`bulk_runner.py` is reference-only for this skill because it launches many subprocesses. Prefer direct `benchmark.py` commands for one model or a short reviewed list unless the user explicitly accepts the cost and risk.

## Reproducibility Checklist

Record these with every benchmark comparison:

- Model name, input size, batch size, and benchmark mode.
- Device model and backend, including CPU versus GPU.
- PyTorch, CUDA/accelerator runtime, and timm versions.
- Precision, AMP dtype, memory layout, and `torch.compile` backend/mode.
- Warmup iterations, timed iterations, and whether batch-size retry changed the batch.
- Whether optional FLOP profilers were installed and which one produced counts.
