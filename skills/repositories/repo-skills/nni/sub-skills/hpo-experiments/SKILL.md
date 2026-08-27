---
name: hpo-experiments
description: "Use NNI HPO experiments, nnictl, ExperimentConfig, trial metric
  APIs, search spaces, tuners, assessors, and training-service config triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HPO Experiments

Use this sub-skill when the user is creating, running, debugging, or migrating an NNI hyperparameter-optimization experiment.

## Route Here For

- Creating an NNI local experiment from a YAML config, search-space JSON, and trial script.
- Converting between `nnictl create --config ...` workflows and the Python `Experiment` / `ExperimentConfig` API.
- Writing trial code that calls `nni.get_next_parameter()`, `nni.report_intermediate_result()`, and `nni.report_final_result()` correctly.
- Fixing search-space JSON, tuner/assessor `classArgs`, custom tuner class paths, and local/remote/cloud training-service config problems.
- Inspecting experiments, trials, logs, exported/imported trial data, and registered algorithms with `nnictl`.

## Route Elsewhere

- NAS model spaces, evaluators, strategies, and neural architecture search prompts belong in `../nas/`.
- Compression `config_list`, pruners, quantizers, speedup, and compression evaluators belong in `../model-compression/`.
- Feature-selection utilities and non-HPO helper APIs belong in `../feature-engineering-and-utilities/`.

## Start With These

- `references/workflows.md`: end-to-end local config, Python launch, custom tuner/assessor, and training-service triage recipes.
- `references/api-reference.md`: trial APIs, `ExperimentConfig`, tuner/assessor base APIs, built-in algorithm names, and search-space type rules.
- `references/cli-reference.md`: `nnictl` command families, safe help/config/log commands, and operational cautions.
- `references/troubleshooting.md`: common failures for YAML/JSON, search spaces, metrics, `pkg_resources`, optional extras, ports, credentials, and remote/cloud services.
- `scripts/validate_search_space.py`: standalone JSON search-space validator for common built-in NNI HPO search-space types.

## Default Playbook

1. Identify the route: CLI YAML config (`nnictl`) or Python API (`Experiment`). Prefer CLI YAML for reproducible user projects; use Python API when the user wants programmatic construction.
2. Validate the search space before diagnosing tuners: run `python scripts/validate_search_space.py search_space.json` from this skill directory or copy the script command into the user project with the correct path.
3. Check the config contract: exactly one of `searchSpaceFile` or `searchSpace`, a valid `trialCommand`, a reachable `trialCodeDirectory`, `tuner.name` or custom tuner class fields, and a `trainingService.platform`.
4. Check trial code: call `nni.get_next_parameter()` once, merge parameters into defaults, report intermediate metrics only after parameters are received, and report one final numeric metric or a dict with numeric `default`.
5. For remote/cloud services, verify credentials, network reachability, Python/NNI version consistency, file-size limits, and secret handling before suggesting a launch.
