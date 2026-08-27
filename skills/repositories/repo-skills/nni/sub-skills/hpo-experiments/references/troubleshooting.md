# HPO Troubleshooting

Use this file to diagnose HPO experiment, config, search-space, trial metric, tuner/assessor, and training-service problems without reopening NNI source docs.

## First Triage Questions

- Is the user launching through `nnictl create --config ...` or the Python `Experiment` API?
- Is the failure before experiment launch, during trial scheduling, inside trial code, inside tuner/assessor import, or during metric reporting?
- Can a local `Random` or `TPE` experiment with `trialConcurrency: 1` reach trial execution?
- Does `python scripts/validate_search_space.py search_space.json` pass for the intended search space?
- Are secrets, cloud credentials, or destructive commands involved? If yes, ask before running anything.

## YAML Or Config Fails To Load

Symptoms:

- YAML parser errors.
- Unknown fields or schema validation failures.
- Config works in old examples but not in current `ExperimentConfig`.

Fixes:

- Use current camelCase YAML fields: `searchSpaceFile`, `trialCommand`, `trialCodeDirectory`, `trialConcurrency`, `maxTrialNumber`, `trainingService`.
- Do not mix legacy v1 keys like `searchSpacePath`, `trainingServicePlatform`, and `builtinTunerName` into new configs unless migrating an old experiment intentionally.
- Use exactly one of `searchSpaceFile` or `searchSpace`.
- Remember that YAML relative paths resolve from the YAML file directory, while Python `ExperimentConfig` relative paths resolve from the current working directory.
- Quote duration strings such as `"0.5h"` if YAML parsing is ambiguous.

## JSON Search Space Fails

Symptoms:

- JSON parse errors.
- Search-space validator reports missing `_type` or `_value`.
- NNI accepts the config but tuner crashes or produces surprising samples.

Fixes:

- JSON does not allow comments, trailing commas, or unquoted property names.
- Every parameter spec should be an object with `_type` and `_value`.
- Use recognized common types: `choice`, `randint`, `uniform`, `quniform`, `loguniform`, `qloguniform`, `normal`, `qnormal`, `lognormal`, `qlognormal`.
- Check value arity: two numeric values for `uniform`, `loguniform`, `normal`, `lognormal`, `randint`; three numeric values for quantized variants; non-empty list for `choice`.
- For `loguniform` and `qloguniform`, lower and upper bounds must be positive.
- Scientific notation such as `1e-7` is valid JSON, but YAML 1.1 tooling can be inconsistent. Prefer JSON for HPO search spaces when using scientific notation.
- For nested `choice` options that are dicts, include `_name` in each branch when using built-in tuners.

## Tuner Does Not Support This Space

Symptoms:

- Non-numeric `choice` fails under numerical tuners.
- Nested search spaces work with one tuner but fail with another.
- `randint` ordering assumptions differ between tuners.

Fixes:

- Use `TPE` or `Random` as a compatibility smoke test; both support all common search-space types and nested spaces.
- Use `quniform` with `q: 1` instead of `randint` if ordered integer semantics matter.
- Avoid non-numeric `choice` values with `GP`, `Metis`, and `DNGO`.
- Avoid nested spaces unless using TPE, Random, Grid Search, Anneal, or Evolution.
- Use `Batch` only for fixed configuration lists; it is not a general continuous-space optimizer.

## Trial Metrics Are Missing Or Invalid

Symptoms:

- Trials finish but WebUI shows no metric.
- Tuner receives bad values.
- Assessor stops trials unexpectedly or never stops anything.
- Assertion says `nni.get_next_parameter()` must be called before reporting metrics.

Fixes:

- Call `nni.get_next_parameter()` once before `report_intermediate_result()` or `report_final_result()`.
- Report final result exactly once near normal trial completion.
- Use a numeric metric or a dict with numeric `default`; extra dict keys are for visualization.
- Align `optimize_mode: maximize` or `minimize` with the reported scalar direction.
- For assessors, report intermediate metrics at stable intervals and with the same metric meaning each time.
- If running trial code standalone, remember it does not prove NNI manager metric transport works.

## `nnictl` Fails With `pkg_resources`

Symptom:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

Cause:

- This NNI checkout imports `pkg_resources` in the `nnictl` entry point. Newer setuptools distributions can omit it.

Fixes:

- Install or pin a setuptools release that still provides `pkg_resources` in the environment where `nnictl` runs.
- Verify with `python -c "import pkg_resources"` and then `nnictl --help`.
- Keep this as an environment fix; do not change user experiment configs to work around it.

## Optional Tuner Dependency Fails

Symptoms:

- Import errors for `hyperopt`, `ConfigSpace`, `smac4nni`, `gym`, or `pybnn`.
- `SMAC`, `Anneal`, `BOHB`, `PPOTuner`, or `DNGO` fails before generating parameters.

Fixes:

- Use `Random` or `TPE` to verify config and trial code first.
- Install the narrow NNI extra for the selected tuner: `Anneal`, `SMAC`, `BOHB`, `PPOTuner`, or `DNGO`.
- Avoid installing all extras unless the user explicitly wants a broad HPO environment.
- Re-run `nnictl --help` after changing dependencies to catch environment breakage early.

## Custom Tuner Or Assessor Fails

Symptoms:

- Cannot import custom class.
- `classArgs` validation fails.
- Tuner cannot find bundled data files.
- Assessor signature mismatch.

Fixes:

- For direct config, set `codeDirectory` to the directory containing the module and set `className` to `module.ClassName`.
- For registered algorithms, ensure the package is importable and the meta file has `algoType`, `builtinName`, `className`, and optional `classArgsValidator`.
- Tuner methods should include `update_search_space`, `generate_parameters` or `generate_multiple_parameters`, and `receive_trial_result`.
- Assessor `assess_trial` should accept `trial_job_id` and `trial_history` and return `AssessResult.Good` or `AssessResult.Bad`.
- Resolve data files relative to `__file__`, not the process working directory; NNI runs tuner/assessor processes from the experiment log directory.
- Constructor values in `classArgs` must be YAML-serializable literals.

## Local Training Service Stalls

Symptoms:

- Trials stay waiting.
- GPU allocation looks wrong.
- Multiple experiments compete for the same GPU.

Fixes:

- Set `trainingService.platform: local`.
- If `trialGpuNumber` is greater than zero and desktop or other processes occupy GPUs, set `trainingService.useActiveGpu: true` only if sharing is acceptable.
- Use `trainingService.gpuIndices` to restrict visible GPUs.
- Use `trainingService.maxTrialNumberPerGpu` intentionally; default is one trial per GPU.
- Reduce `trialConcurrency` to one while debugging trial failures.

## Remote Training Service Fails

Symptoms:

- SSH connection errors.
- Trial command not found on remote machines.
- Files fail to upload or remote environment differs.

Fixes:

- Confirm each `machineList` entry has `host`, `user`, optional `port`, and either `sshKeyFile` or `password`.
- Verify remote SSH works outside NNI before changing NNI config.
- Make NNI versions consistent across manager and remote machines.
- Set `pythonPath` only when the remote environment requires it; use user-provided environment paths, not guessed local paths.
- Ensure `trialCommand` works on the remote OS.
- Add `.nniignore` for large `trialCodeDirectory` trees; remote/cloud payloads are limited by file count and size.
- Set `nniManagerIp` explicitly when remote machines cannot reach the manager by the default interface.

## Cloud Or Cluster Service Fails

Symptoms:

- Authentication errors.
- Storage mount errors.
- Docker image or compute target not found.
- Unexpected cost-incurring jobs.

Fixes:

- Ask before launching or cleaning cloud/cluster jobs.
- Redact tokens and access keys in notes and examples.
- Verify platform-specific required fields for `openpai`, `aml`, `dlc`, `kubeflow`, `frameworkcontroller`, or hybrid service.
- Check Docker image availability, storage mount paths, namespace/compute names, and region settings.
- Prefer local-mode reproduction for search-space/trial-code/tuner issues before debugging cloud infrastructure.

## Port Or WebUI Problems

Symptoms:

- `nnictl create` reports port conflicts.
- WebUI URL is unreachable.
- `nnictl stop --port` affects the wrong service.

Fixes:

- Launch with an explicit free port: `nnictl create --config config.yml --port 8088`.
- Use `nnictl webui url` and `nnictl experiment status` to find active endpoints.
- Stop by exact experiment ID when possible, not by ambiguous prefix or guessed port.
- If running remote/cloud, verify firewall and manager IP reachability.
