# Swarming Troubleshooting

This reference covers workflow-specific failures for NuPIC legacy swarming. For package installation, `nupic.bindings`, Python 2.7, `pycapnp`/Cap'n Proto, and broad configuration import failures, also read the root reference [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md). For CSV/header/field metadata problems, route to [`../../data-and-configuration/`](../../data-and-configuration/); for running a generated best model, route to [`../../opf-prediction/`](../../opf-prediction/).

## First triage

1. Run the safe linter before running NuPIC:

   ```bash
   python scripts/swarm_config_lint.py path/to/search_def.json --check-files
   ```

2. Confirm the legacy runtime separately: Python 2.7-compatible NuPIC, `nupic.bindings`, legacy NumPy, and any needed `pycapnp`/Cap'n Proto support.
3. For full `run`, `pickup`, and many `report` operations, confirm MySQL-compatible ClientJobs database access. A full swarm is service-dependent; static JSON linting is not.
4. Keep the first executable swarm tiny: `swarmSize: "small"`, bounded `iterationCount`, `--action=dryRun`, `--maxPermutations=1`, and `--maxWorkers=1`.

## MySQL service or credentials errors

Typical signals:

- Connection refused, authentication denied, unknown database, stale ClientJobs tables, or worker errors before model records are processed.
- A vague `No handlers could be found for logger...` message followed by no model progress.
- `run` workers start, then all models fail with database or ClientJobs errors.

NuPIC legacy's default database properties are equivalent to:

| Property | Default intent |
|---|---|
| `nupic.cluster.database.host` | `localhost` |
| `nupic.cluster.database.user` | `root` |
| `nupic.cluster.database.port` | `3306` |
| `nupic.cluster.database.passwd` | empty password |
| `nupic.cluster.database.nameSuffix` | user-specific suffix |

Override properties with environment variables by replacing dots with underscores after `NTA_CONF_PROP_`:

```bash
export NTA_CONF_PROP_nupic_cluster_database_host=localhost
export NTA_CONF_PROP_nupic_cluster_database_user=root
export NTA_CONF_PROP_nupic_cluster_database_port=3306
export NTA_CONF_PROP_nupic_cluster_database_passwd='your-password'
export NTA_CONF_PROP_nupic_cluster_database_nameSuffix="${USER:-nupic}"
```

Then retry a tiny dry or one-worker run. If `dryRun` still reaches database errors, treat it as runtime/service readiness rather than a JSON schema problem. If the linter passes and the MySQL connection fails, do not keep editing `search_def.json`; fix service/credentials first.

## `file://` source mistakes

Symptoms:

- ExpGenerator or StreamReader cannot open the CSV.
- The linter reports a missing or malformed `streamDef.streams[*].source`.
- A relative path works from one directory but not another.

Rules:

- Every stream `source` should begin with `file://`.
- Relative source example: `file://data/input.csv`.
- Absolute source example: `file:///data/input.csv`.
- Keep `search_def.json` and its `data/` directory together, or use an absolute `file:///...` source.
- Re-run the linter with `--check-files` after moving a search definition.
- If the CSV opens but field errors remain, compare CSV headers, `includedFields`, `aggregation.fields`, and `inferenceArgs.predictedField` through [`../../data-and-configuration/`](../../data-and-configuration/).

## Choosing the right action

| Action | Use when | Common recovery |
|---|---|---|
| `--action=dryRun` | You need a fast runtime check of JSON-to-description/permutations generation and one inline worker. | Add `--maxPermutations=1`, use `swarmSize: "small"`, and keep `iterationCount` small. If it fails before model execution, check runtime/DB/imports. |
| `--action=run` | You are ready for a full search with worker processes. | Confirm MySQL first; reduce `--maxWorkers`; add `--timeout`; use `--maxPermutations` for bounded tests. |
| `--action=report` | You want to regenerate or inspect results for a saved job. | Run from the same working directory/output label so the saved `*_HyperSearchJobID.pkl` can be found. Use `--replaceReport` if the CSV should not append. |
| `--action=pickup` | A previous search was interrupted and the saved job should be resumed. | Use the same working directory/output label and a healthy DB. If the saved job id file is missing, start a new run. |

The legacy help text may mention historical action names such as `choices` or `list`, but the implemented choices are `run`, `pickup`, `report`, and `dryRun`.

## Worker and timeout tuning

- Start with `--maxWorkers=1` until the search definition and DB are healthy.
- Increase `--maxWorkers` only when CPU/memory and MySQL can handle concurrent workers.
- Use `--timeout=MINUTES` to bound long searches; a timeout cancels/exits rather than producing a better model.
- If workers fail immediately, increasing `--maxWorkers` makes noise louder but does not fix JSON, data, import, or DB errors.
- If only some models fail, inspect the first printed completion error and the report CSV for a common parameter/field pattern.

## Generated output files are missing or stale

Expected files for `search_def.json` in a working directory include:

- `description.py`: generated base OPF description.
- `permutations.py`: generated search space.
- `search_def_HyperSearchJobID.pkl` or similarly prefixed saved job id.
- `search_def_Report.csv` or similarly prefixed report.
- `model_0/description.py`, `model_0/params.csv`, and `model_0/model_params.py` when top model descriptions are generated.

Common causes and fixes:

- Existing `description.py` or `permutations.py`: add `--overwrite` only if replacing generated files is intended.
- Report rows append unexpectedly: use `--replaceReport` to replace the CSV instead of appending/backing up.
- `model_0/` missing: confirm the run reached report generation, `--genTopNDescriptions` is greater than zero, and at least one model completed successfully.
- `report` cannot find a job: run from the same working directory/output label used by the original action.
- Best model exists but OPF run fails: route to [`../../opf-prediction/`](../../opf-prediction/) and load `MODEL_PARAMS` from `model_0/model_params.py`.

## `customErrorMetric` escaping

Symptoms:

- JSON parser errors near `customErrorMetric`.
- Generated description errors because a multi-line custom expression lost indentation or quotes.
- Metric code appears as one unescaped raw block in JSON.

Safer pattern:

```python
import json
expr = """if tools.getData('num') is None:
  tools.storeData('num', 0)
tools.getData('num')
"""
print(json.dumps({"customErrorMetric": {"customExpr": expr, "errorWindow": 500}}, indent=2))
```

For a Python 2-only workflow, the historical escaping helper was `expr.encode("string_escape")`. Prefer generating JSON with `json.dumps` so quotes, backslashes, and newlines are escaped consistently. The bundled linter intentionally does not execute `customExpr`; it only checks the value is a string and warns about likely shape problems.

## Inference field mismatches

Symptoms:

- Linter warns that `predictedField` is not in `includedFields`.
- Dry run generates a model but predictions are empty or optimize the wrong column.
- Aggregation errors mention unknown field names.

Check all four locations:

1. CSV first header row field names.
2. `includedFields[*].fieldName`.
3. `streamDef.aggregation.fields[*][0]` if aggregation is present.
4. `inferenceArgs.predictedField`.

For most `MultiStep` prediction swarms, the predicted field should be listed consistently. Classification/anomaly variants have different semantics, so treat linter warnings as a prompt to verify intent rather than blindly adding fields.

## When to stop editing JSON

Stop editing `search_def.json` and switch to runtime/service troubleshooting when:

- `scripts/swarm_config_lint.py` reports no errors.
- `--check-files` confirms stream sources exist.
- The failure mentions MySQL, ClientJobs, worker launch, `nupic.bindings`, package imports, or Python 2/3 syntax.

At that point, use the root [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md) plus this file's MySQL override section.
