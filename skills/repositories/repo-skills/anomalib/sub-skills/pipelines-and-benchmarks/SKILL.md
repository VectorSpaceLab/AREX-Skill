---
name: pipelines-and-benchmarks
description: "Use for Anomalib benchmark pipelines, tiled ensemble workflows,
  and advanced pipeline orchestration helpers while keeping experimental
  execution paths explicit."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Pipelines and Benchmarks

Use this sub-skill when the user asks about Anomalib benchmark configs, pipeline runners/jobs/generators, tiled ensemble training or evaluation, or safe preflight checks for pipeline configuration.

## Read first

- For benchmark configs, grid expansion, runner choice, custom pipeline structure, and benchmark-scale caveats, read [references/pipelines-and-benchmarks.md](references/pipelines-and-benchmarks.md).
- For tiled ensemble config, train/eval stages, root directory selection, and cost controls, read [references/tiled-ensemble.md](references/tiled-ensemble.md).
- For failure recovery, CPU/CUDA fallback, missing config sections, and wrong results paths, read [references/troubleshooting.md](references/troubleshooting.md).
- For a lightweight import/config preflight that does not run training, testing, benchmark jobs, or tiled ensemble jobs, use [scripts/pipeline_config_smoke.py](scripts/pipeline_config_smoke.py).

## Safe operating boundary

Prefer read-only parsing and config repair before execution. Pipeline execution can train models, load datasets, spawn processes, create results directories, and run for a long time. Treat these as expensive unless the user explicitly provides dataset paths, runtime budget, and backend/hardware intent.

Route elsewhere when the request is primarily about:

- model or datamodule selection details beyond the pipeline config shell;
- core `Engine.fit`, `Engine.test`, metrics, post-processing, loggers, callbacks, or visualization semantics;
- export formats, inferencers, OpenVINO/Torch deployment, or Studio application code.

## Quick routing

| User need | Do this |
| --- | --- |
| “How do I benchmark several models/categories?” | Explain the benchmark YAML shape, `grid` keys, and CPU/CUDA runner selection from [pipelines-and-benchmarks](references/pipelines-and-benchmarks.md). |
| “Switch a benchmark from CUDA to CPU without losing the grid.” | Change only the top-level `accelerator` to `cpu` or `[cpu]`; keep the `benchmark` tree and all `grid` leaves unchanged. Run the smoke helper before execution. |
| “Create a custom pipeline/job/runner.” | Explain the `Pipeline` → `Runner` → `JobGenerator` → `Job` contract; keep custom code independent of execution strategy. |
| “Use tiled ensemble on high-resolution images.” | Read the tiled ensemble reference, warn that it is experimental, validate the config, and require a results-root decision before evaluation. |
| “Tiled eval cannot find checkpoints/results.” | Check whether `EvalTiledEnsemble(root_dir=...)` points at the exact versioned run directory containing the ensemble weights and stats, not the parent default results directory. |
| “Run the MEBin post-processing benchmark.” | Treat it as benchmark-scale and reference-only by default; require explicit dataset path, output path, model/category budget, and runtime approval. |

## Minimal preflight commands

From a project where Anomalib is importable:

```bash
python sub-skills/pipelines-and-benchmarks/scripts/pipeline_config_smoke.py --import-only
python sub-skills/pipelines-and-benchmarks/scripts/pipeline_config_smoke.py --benchmark-config benchmark.yaml
python sub-skills/pipelines-and-benchmarks/scripts/pipeline_config_smoke.py --tiled-config ensemble.yaml --eval-root results/Padim/MVTecAD/bottle/v0
```

The helper only imports public entrypoints and validates config shape/paths. It does not call `Pipeline.run`, train models, evaluate models, or create result directories.
