---
name: benchmarking-and-results
description: "Use this sub-skill when a user needs to run bounded timm
  benchmarks, compare inference/train/profile timing modes, interpret bundled
  result CSVs, or look up ImageNet-1k model metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Benchmarking and Results

Use this sub-skill for safe, reproducible performance checks with timm benchmark tooling and for interpreting bundled result tables.

## Route Here When

- The user asks how to run `benchmark.py` for inference, train-step, profile, or combined timing.
- The user wants a bounded benchmark command for one model, a wildcard subset, or a short model-list file.
- The user asks what benchmark CSV columns mean or how to compare rows across devices, precision, layouts, or PyTorch versions.
- The user needs ImageNet result fields or `model_metadata-in1k` pretraining labels explained.
- The user requests all-model benchmarking and needs safe scoping before launching long bulk work.

## Start Safely

1. Pick the smallest representative scope first: one model, one device, low batch size, and low iteration counts.
2. Use the bundled command builder to create bounded commands instead of hand-assembling broad runs:
   `python scripts/timm_benchmark_command_builder.py --model resnet50 --bench inference --device cuda --batch-size 32 --num-warm-iter 2 --num-bench-iter 5 --amp`
3. Run debug timing before publication-quality timing, then increase `--num-warm-iter`, `--num-bench-iter`, and batch size only after memory and precision choices are stable.
4. Treat bulk or all-model requests as potentially expensive; require an explicit model pattern, model-list file, or `--allow-bulk` acknowledgement.

## References

- `references/benchmarking.md`: benchmark modes, important flags, safe command patterns, and profiling choices.
- `references/results-tables.md`: benchmark, validation, and metadata CSV columns plus interpretation cautions.
- `references/troubleshooting.md`: OOM, timing comparability, warmup, `torch.compile`, optional profiler, AMP/layout, and stale metadata issues.
- `scripts/timm_benchmark_command_builder.py`: guarded command generator for bounded single-model and optional bulk benchmark commands.

## Boundary Notes

- This sub-skill covers benchmark execution and result interpretation only.
- Use the `cli-workflows` sub-skill for full `train.py`, `validate.py`, or dataset-driven CLI workflows.
- Do not present bundled benchmark CSV values as universal hardware truth; they are snapshots from specific accelerators, software versions, precision modes, and layouts.
