---
name: swarming
description: "Author, lint, run, and debug NuPIC legacy swarming search
  definitions and turn swarm outputs into OPF model parameters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NuPIC Legacy Swarming

Use this sub-skill when the task is to create or repair a NuPIC legacy swarm/search definition, explain `run_swarm.py` or `permutations_runner` behavior, run a small dry swarm, diagnose MySQL or worker failures, or use the generated best model from `model_0/` in OPF.

NuPIC legacy swarming is a Python 2.7-era workflow. A full swarm expects a working NuPIC installation with `nupic.bindings`, legacy NumPy compatibility, `pycapnp`/Cap'n Proto support where required by the install, and a MySQL-compatible ClientJobs database for full hypersearch coordination. The bundled linter below is stdlib-only and can be run before those services are available.

## Route requests

- CSV headers, field metadata, `streamDef` data-source conventions, aggregation field names, and model-param schema details: read [`../data-and-configuration/`](../data-and-configuration/).
- Running the generated best model, importing `MODEL_PARAMS` from `model_0/model_params.py`, or debugging OPF inference outputs: read [`../opf-prediction/`](../opf-prediction/).
- Package install/import failures, Python 2.7/bindings/capnp issues, and cross-cutting NuPIC database configuration context: read the root troubleshooting reference at [`../../references/troubleshooting.md`](../../references/troubleshooting.md).
- Direct encoder/SP/TM/classifier behavior that swarming selected automatically belongs to the relevant algorithm or OPF sub-skill, not here.

## Use the bundled materials

- [`references/swarming-workflows.md`](references/swarming-workflows.md): read when authoring `search_def.json`, choosing `run_swarm.py`/`permutations_runner` options, interpreting generated files, or converting best swarm output into OPF parameters.
- [`references/swarm-search-def-template.json`](references/swarm-search-def-template.json): copy as a minimal JSON starting point for a one-step numeric prediction swarm; edit field names, file source, aggregation, and predicted field before running.
- [`scripts/swarm_config_lint.py`](scripts/swarm_config_lint.py): run before any dry or full swarm to catch malformed JSON, missing keys, bad `file://` sources, invalid `swarmSize`, and prediction field mismatches without importing NuPIC.
- [`references/troubleshooting.md`](references/troubleshooting.md): read for MySQL credentials, `NTA_CONF_PROP_*` overrides, `dryRun`/`run`/`report`/`pickup` recovery, timeout/worker tuning, overwrite/report behavior, generated-output lookup, and `customErrorMetric` escaping.

## Minimal operating loop

1. Start from the bundled template or an existing `search_def.json`.
2. Make the CSV and field metadata consistent first; route to [`../data-and-configuration/`](../data-and-configuration/) for NuPIC's three-row CSV headers and aggregation semantics.
3. Lint safely:

   ```bash
   python scripts/swarm_config_lint.py path/to/search_def.json --check-files
   ```

4. For syntax/debugging, prefer a tiny `swarmSize: "small"`, bounded `iterationCount`, and `--action=dryRun --maxPermutations=1 --maxWorkers=1`. Treat a full `--action=run` as service-dependent because it coordinates workers through MySQL.
5. After a successful run, use `model_0/model_params.py` or `model_0/description.py` as the best model artifact; route OPF execution to [`../opf-prediction/`](../opf-prediction/).

## Evidence provenance

This sub-skill distills NuPIC legacy swarming behavior from the public docs and source paths `docs/source/guides/swarming/running.md`, `docs/source/guides/swarming/algorithm.md`, `examples/swarm/simple/search_def.json`, `src/nupic/swarming/`, `src/nupic/swarming/exp_generator/experimentDescriptionSchema.json`, `scripts/run_swarm.py`, and `tests/swarming/`. These paths are provenance only; this runtime skill is self-contained and does not require future agents to reopen them.
