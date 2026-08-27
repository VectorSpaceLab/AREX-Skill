---
name: evaluation
description: "Evaluate NAVSIM trajectories with cached metrics, one-stage or
  two-stage EPDMS, configured traffic policies, and reproducible CSV outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NAVSIM evaluation

Use this route when a trajectory or agent must be scored with NAVSIM v2 EPDMS,
when metric caches need to be prepared, or when a CSV result needs diagnosis.
This route covers the simulation/scoring contract, not model design or training.
For agent output and sampling contracts, use the sibling `agents` route; for
workspace and split path setup, use `setup-and-data`.

## Route

1. Read [workflows](references/workflows.md) and run the read-only
   [evaluation-config inspector](scripts/inspect_evaluation_config.py) first:
   `python scripts/inspect_evaluation_config.py --help`.
2. Select the exact split and stage. Make the metric-cache split, log/synthetic
   scene roots, and evaluation split agree before any data-backed command.
3. Follow [configuration](references/configuration.md) to choose a worker,
   agent/submission input, proposal sampling, scorer, output directory, and
   traffic policy. Use the command templates; replace placeholders explicitly.
4. If a cache is absent or stale, run the cache command only after checking
   maps, logs, split filters, and storage. Cache and evaluation must use the
   same proposal sampling and scene universe.
5. Run one-stage or two-stage scoring as described in [workflows](references/workflows.md).
   Treat warnings, failed-token counts, and pseudo-closed-loop validity as
   acceptance gates rather than cosmetic log messages.
6. Inspect the CSV using [metrics-reference](references/metrics-reference.md)
   and stop if the expected summary row, stage columns, or valid-scenario
   status is absent. For failures, use [troubleshooting](references/troubleshooting.md).

Do not download data, submit results, or launch a benchmark workload by default.
The bundled inspector is diagnostic only and never opens datasets or caches.
