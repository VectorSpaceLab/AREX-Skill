---
name: pipeline-programming
description: "Build, run, batch, debug, and smoke-check Towhee custom pipelines
  with pipe.input, RuntimePipeline, AutoConfig, and AutoPipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Towhee pipeline programming

Use this sub-skill when the user needs to define or diagnose a Towhee custom pipeline with `pipe.input(...)`, chained node methods, `output(...)`, `RuntimePipeline.__call__`, `batch(...)`, `debug(...)`, or `flush()`. It also covers safe, local-only checks for `AutoConfig` and network-aware guidance for `AutoPipes.pipeline(...)`.

## Fast routing

1. For pipeline node syntax, callable contracts, schemas, `RuntimePipeline`, `batch`, `flush`, `AutoConfig`, and `AutoPipes`, use [Pipeline API](references/pipeline-api.md).
2. For profiler/tracer usage, debug result inspection, include/exclude filtering, and batch debug, use [Debugging and profiling](references/debugging-and-profiling.md).
3. For failures involving schema names, missing output columns, `debug()` flags, Hub/cache/network misses, or optional Hub operator downloads, use [Troubleshooting](references/troubleshooting.md).
4. For a no-network smoke check in the target environment, run [pipeline_smoke.py](scripts/pipeline_smoke.py) with `--verbose` when useful.

## Scope boundaries

- Stay here for custom pipeline construction, local lambda/callable nodes, node semantics, runtime execution, batch/debug/flush, `AutoConfig.*`, and `AutoPipes.pipeline` selection caveats.
- Route operator template creation, Hub operator packaging, `ops` registration patterns, and CLI operator scaffolding to `operator-hub-and-cli`.
- Route HTTP/GRPC services, Docker, Triton server startup, `towhee server`, and deployment packaging to `serving-and-triton`.
- Route `DataCollection` display, entity/type wrappers, serializers, and data loader details to `data-utilities`.
- Route model training, `Trainer`, and `NNOperator.train/setup_trainer` workflows to `training-and-models`.

## Default safe workflow

```bash
python scripts/pipeline_smoke.py --verbose
```

If the smoke check fails at import time, fix the active Python environment before attempting Hub, model, Triton, or deployment workflows. If the smoke check passes, prefer lambda/callable pipelines for quick local diagnosis before introducing Hub operators that may download code, models, or optional dependencies.
