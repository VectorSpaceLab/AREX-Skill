---
name: nupic-legacy
description: "Use NuPIC legacy HTM algorithms, OPF prediction, Network API
  pipelines, swarming search definitions, and data/config validation in Python
  2.7-era runtimes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NuPIC Legacy

Use this repo skill when a task involves NuPIC legacy, Hierarchical Temporal Memory (HTM), streaming anomaly/prediction workflows, `SpatialPooler`, `TemporalMemory`, `SDRClassifier`, OPF `ModelFactory`, Network API regions, `run_swarm`, or NuPIC three-header-row CSV/model-parameter files.

NuPIC legacy is maintenance-mode, Python 2.7-era software. Start by checking the runtime before debugging workflow code.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a checkout or deciding whether to refresh it.
2. Read [references/installation-and-runtime.md](references/installation-and-runtime.md) before installing or preparing a NuPIC legacy environment.
3. Run [scripts/check_nupic_legacy_env.py](scripts/check_nupic_legacy_env.py) inside the candidate Python environment to verify imports and tiny API construction.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when failures mention Python version, `nupic`, `nupic.bindings`, `numpy`, `capnp`/`pycapnp`, dependency conflicts, or broad runtime setup.

Minimal package smoke command from this skill root:

```bash
python scripts/check_nupic_legacy_env.py
```

Expected runtime for execution tasks: Python 2.7, installed `nupic`, compiled `nupic.bindings`, legacy-compatible NumPy, and `pycapnp`/Cap'n Proto where serialization is involved. Do not treat Python 3 import or syntax failures as surprising unless the user is explicitly porting NuPIC.

## Route by task

| User task or signal | Go to | Why |
|---|---|---|
| Direct encoders, `SpatialPooler`, `TemporalMemory`, `SDRClassifier`, anomaly score, anomaly likelihood, active columns/cells | [sub-skills/htm-algorithms/](sub-skills/htm-algorithms/) | Covers direct HTM algorithm APIs, signatures, array shapes, and tiny smoke checks. |
| CSV stream headers, `FileRecordStream`, field metadata, model parameter YAML/JSON, aggregation, configuration overrides | [sub-skills/data-and-configuration/](sub-skills/data-and-configuration/) | Validates and explains input/config artifacts shared by OPF, Network, and swarming. |
| OPF `ModelFactory`, `HTMPredictionModel`, `model.run`, `result.inferences`, experiment directories, checkpoints | [sub-skills/opf-prediction/](sub-skills/opf-prediction/) | Covers high-level prediction workflows, inference keys, experiment runner guidance, and checkpoint use. |
| `Network`, `RecordSensor`, `SPRegion`, `TMRegion`, classifier regions, region links, custom PyRegion | [sub-skills/network-api/](sub-skills/network-api/) | Covers Network API construction, linking, region specs, output extraction, and custom-region skeletons. |
| `run_swarm`, `permutations_runner`, `search_def.json`, generated `model_0`, MySQL/ClientJobs errors | [sub-skills/swarming/](sub-skills/swarming/) | Covers safe search-definition linting, CLI/action options, service requirements, and using generated OPF models. |

## Common workflows

### Direct HTM algorithm pipeline

Use `htm-algorithms` when the user wants to encode values, run SP/TM, classify active cells, or compute anomaly likelihood without OPF. The bundled smoke is:

```bash
python sub-skills/htm-algorithms/scripts/algorithm_smoke.py --mode all --records 20
```

### OPF prediction over a CSV stream

Use `data-and-configuration` first to validate the NuPIC CSV and model parameters, then `opf-prediction` to create the model and extract `multiStepBestPredictions` / `multiStepPredictions`. Useful checks:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv --predicted-field consumption
python sub-skills/opf-prediction/scripts/opf_prediction_smoke.py
```

### Network API graph

Use `network-api` when the user asks for explicit regions and links rather than OPF. Start with:

```bash
python sub-skills/network-api/scripts/network_smoke.py --inspect-region-types
```

### Swarming/search-definition workflow

Use `swarming` for `search_def.json` authoring and hypersearch run planning. Lint before running anything service-backed:

```bash
python sub-skills/swarming/scripts/swarm_config_lint.py search_def.json --summary
```

Full swarming can require MySQL-compatible service configuration and may be expensive; never use it as a first install smoke.

## Boundaries

- This skill teaches using NuPIC legacy as a package. For source-code edits, release engineering, or Python 3 porting, treat the task as repository maintenance and do not use package workflow assumptions blindly.
- This skill does not cover modern deep-learning time-series forecasting unless the task explicitly uses NuPIC/HTM APIs.
- Do not install developer requirements, visualization extras, Docker/Vagrant tooling, profiling scripts, or full benchmark suites unless the user asks for those surfaces.
- Runtime instructions here are self-contained; bundled references/scripts replace the relevant example logic instead of requiring future agents to read or run original checkout files.
