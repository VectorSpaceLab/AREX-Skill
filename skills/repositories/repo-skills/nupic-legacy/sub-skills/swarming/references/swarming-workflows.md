# NuPIC Legacy Swarming Workflows

Swarming searches for a good OPF model configuration for a dataset by trying candidate encoders, field subsets, model components, and scalar parameters, then emitting the best discovered model description. Use this reference to write a `search_def.json`, choose CLI/API actions, understand generated files, and hand the best model to OPF.

For CSV header rows, field types, aggregation functions, and model-parameter nesting, cross-check [`../../data-and-configuration/`](../../data-and-configuration/). For running the selected model after swarming, use [`../../opf-prediction/`](../../opf-prediction/).

## What a swarm needs

A practical swarm definition has two inputs:

1. **A NuPIC-formatted CSV stream** with three header rows: field names, field types, and special flags. The stream path in a swarm uses a `file://` source string.
2. **A swarm description JSON object** that tells ExpGenerator which fields to search, which task to optimize, how many records to process, and how exhaustive the search should be.

A full `run` action coordinates workers through NuPIC's ClientJobs database, normally backed by MySQL. A `dryRun` action is the first executable check because it runs one HypersearchWorker inline and is intended to flush out JSON, generated-description, and permutations errors before spending a full run. It still uses the legacy NuPIC runtime, so environment or database-layer errors can appear before the model logic is reached.

## Minimal `search_def.json` shape

Copy [`swarm-search-def-template.json`](swarm-search-def-template.json), then edit the field names and source path. The most important top-level keys are:

| Key | Required for normal swarms | Shape and usage |
|---|---:|---|
| `includedFields` | yes | Non-empty list of objects with `fieldName` and `fieldType`. `fieldType` is typically `datetime`, `float`, `int`, or `string`. A field is not considered as model input unless listed here. Optional per-field controls include `minValue`, `maxValue`, `runDelta`, `space`, and `encoderType`. |
| `streamDef` | yes | Object describing one or more input streams. Each stream should include a `source` string beginning with `file://`; `columns: ["*"]` is common. `aggregation` can define the time bucket and field aggregation functions. |
| `inferenceType` | yes for clarity | One of NuPIC's legacy inference types such as `MultiStep`, `TemporalMultiStep`, `NontemporalMultiStep`, `TemporalNextStep`, `TemporalAnomaly`, `NontemporalAnomaly`, `TemporalClassification`, or `NontemporalClassification`. |
| `inferenceArgs` | yes for prediction | For prediction swarms, include `predictionSteps` as a non-empty list of step sizes and `predictedField` as a field name from the data. Optional `inputPredictedField` may be `auto`, `yes`, or `no`. |
| `iterationCount` | strongly recommended | Maximum number of aggregated records to run. `-1` means all available records. Use a small positive number while debugging. |
| `swarmSize` | strongly recommended | `small`, `medium`, or `large`. `small` is a quick syntax/config check; `medium` is the usual first real search; `large` trades time for more exploration. |

Optional keys commonly seen in advanced workflows include `metricWindow`, `customErrorMetric`, `metrics`, `fixedFields`, `maxModels`, `computeInterval`, `resetPeriod`, `runBaselines`, and `fastSwarmModelParams`.

## Stream and aggregation conventions

A single-stream numeric prediction swarm often uses this pattern:

```json
"streamDef": {
  "info": "my experiment",
  "version": 1,
  "streams": [
    {
      "info": "input.csv",
      "source": "file://data/input.csv",
      "columns": ["*"],
      "last_record": 200
    }
  ],
  "aggregation": {
    "hours": 1,
    "minutes": 0,
    "seconds": 0,
    "milliseconds": 0,
    "microseconds": 0,
    "days": 0,
    "weeks": 0,
    "months": 0,
    "years": 0,
    "fields": [
      ["value", "sum"],
      ["timestamp", "first"]
    ]
  }
}
```

Notes:

- `file://data/input.csv` is a relative file source; `file:///abs/path/input.csv` is an absolute file source.
- The CSV field names, `includedFields[*].fieldName`, `aggregation.fields[*][0]`, and `inferenceArgs.predictedField` must agree.
- `last_record` is a stream-level debugging limiter. `iterationCount` is the model-control limit after aggregation; `-1` runs the available stream.
- If the data is already at the desired interval, omit `aggregation` or set an interval that does not change the intended target semantics.

## Validate before running

Run the bundled linter from this sub-skill directory or with absolute paths:

```bash
python scripts/swarm_config_lint.py path/to/search_def.json --check-files
```

The linter is stdlib-only; it does not import NuPIC and does not run a model. It checks JSON parseability, expected top-level keys, `includedFields`, stream `file://` sources, `inferenceType`, `predictionSteps`, `predictedField`, `iterationCount`, and `swarmSize`. Use `--strict` if warnings should fail CI-like checks.

## `run_swarm.py` action model and options

NuPIC legacy exposes a swarming CLI convention equivalent to:

```bash
run_swarm.py [options] search_def.json
run_swarm.py [options] permutations.py
```

For a JSON file, ExpGenerator first writes `description.py` and `permutations.py` beside the JSON, then the permutations runner starts the requested action. For a `permutations.py` file, a sibling `description.py` is expected.

Important options adapted from the legacy CLI:

| Option | Meaning |
|---|---|
| `--action=run` | Start a new HyperSearch job and worker processes. This is the default action and requires the full legacy runtime plus ClientJobs/MySQL database access. |
| `--action=dryRun` | Run a single HypersearchWorker inline to flush out generated-description and permutations errors. It defaults to one permutation unless `--maxPermutations` is supplied. Use this before full runs. |
| `--action=pickup` | Resume/pick up the latest saved HyperSearch job for the same working directory and output label. |
| `--action=report` | Load the saved job id and regenerate/print a report without launching a new search. |
| `--maxPermutations=N` | Cap the number of searched models for `run` and `dryRun`. Good for smoke checks. |
| `--maxWorkers=N` | Maximum concurrent workers for `run`; start with `1` or a small number until the DB/runtime is healthy. |
| `--timeout=MINUTES` | Cancel/exit after the runner reaches its timeout condition. Use to bound full runs. |
| `--overwrite` | Permit regeneration of existing `description.py` and `permutations.py` beside a JSON description. Without it, existing files are protected. |
| `--replaceReport` | Replace the existing report CSV. Without it, report generation appends/backups according to the runner behavior. |
| `--genTopNDescriptions=N` | Emit `model_0/`, `model_1/`, ... directories for the top N models; default is one top model. |
| `--exports='{"KEY":"VALUE"}'` | Apply environment variable settings before launching worker jobs. Prefer explicit shell `NTA_CONF_PROP_*` variables for NuPIC config when possible. |
| `--useTerminators` | Enable early model terminators in HyperSearch. |
| `-v`, `-vv` | Increase verbosity. |

Typical progression:

```bash
# 1. Safe static lint.
python scripts/swarm_config_lint.py search_def.json --check-files

# 2. Tiny runtime check; choose a bounded iterationCount and swarmSize "small" in JSON.
run_swarm.py --action=dryRun --maxPermutations=1 --maxWorkers=1 --overwrite search_def.json

# 3. Full run only after MySQL and NuPIC runtime are healthy.
run_swarm.py --action=run --maxWorkers=4 --timeout=60 --genTopNDescriptions=1 search_def.json

# 4. Regenerate report or resume the saved job.
run_swarm.py --action=report search_def.json
run_swarm.py --action=pickup --maxWorkers=4 search_def.json
```

## Programmatic API names

Use the API when embedding swarming into a Python 2.7 NuPIC workflow or when constructing the search definition as a dictionary:

```python
from nupic.swarming import permutations_runner

swarm_config = {
    "includedFields": [
        {"fieldName": "timestamp", "fieldType": "datetime"},
        {"fieldName": "value", "fieldType": "float"}
    ],
    "streamDef": {
        "info": "demo",
        "version": 1,
        "streams": [{"info": "input.csv", "source": "file://data/input.csv", "columns": ["*"]}]
    },
    "inferenceType": "MultiStep",
    "inferenceArgs": {"predictionSteps": [1], "predictedField": "value"},
    "iterationCount": 200,
    "swarmSize": "small"
}

options = {
    "action": "dryRun",
    "maxPermutations": 1,
    "maxWorkers": 1,
    "overwrite": True,
    "genTopNDescriptions": 1
}

model_params = permutations_runner.runWithConfig(
    swarm_config,
    options,
    outDir="swarm-output",
    outputLabel="search_def",
    permWorkDir="swarm-output")
```

Related entry points:

- `runWithConfig(swarmConfig, options, outDir=None, outputLabel="default", permWorkDir=None, verbosity=1)`: generate files from a dict and run/report the requested action.
- `runWithJsonFile(expJsonFilePath, options, outputLabel, permWorkDir)`: load a JSON file and delegate to `runWithConfig`.
- `runWithPermutationsScript(permutationsFilePath, options, outputLabel, permWorkDir)`: run from an existing `permutations.py` and sibling `description.py`.

The stable output is the generated files and reports. Depending on action and code path, callers may also receive a model-parameter object after report generation.

## Generated files and how to use them

If the input is `search_def.json`, generated artifacts normally appear in the same working directory:

| Artifact | Meaning |
|---|---|
| `description.py` | Base OPF experiment description generated from the JSON. |
| `permutations.py` | Search-space script used by the permutations runner. Advanced users may edit this for custom parameter ranges or fixed values. |
| `search_def_HyperSearchJobID.pkl` | Saved job id used by `pickup` and `report` actions. The exact prefix follows the output label. |
| `search_def_Report.csv` | CSV report of model parameters and metrics for evaluated models. |
| `model_0/description.py` | OPF description for the best model after applying selected parameter overrides. Additional top-N directories are controlled by `--genTopNDescriptions`. |
| `model_0/params.csv` | Chosen parameter labels for the best model; useful for inspection. |
| `model_0/model_params.py` | Python file defining `MODEL_PARAMS`, suitable for `ModelFactory.create`. |

To use the best model manually in OPF, load `MODEL_PARAMS` and create a model:

```python
import imp
from nupic.frameworks.opf.model_factory import ModelFactory

params_module = imp.load_source("best_swarm_model_params", "model_0/model_params.py")
model = ModelFactory.create(params_module.MODEL_PARAMS)
model.enableInference({"predictedField": "value"})
```

Then feed records and read OPF inference keys as described in [`../../opf-prediction/`](../../opf-prediction/).

## Algorithm intuition for tuning requests

- Swarming first searches field combinations in sprints: single fields, then combinations built from the best contributors.
- Within a mini-swarm it uses particle-swarm-like updates for scalar parameters and weighted choices for enumerated options.
- `swarmSize` controls exploration: `small` creates one particle per mini-swarm, `medium` uses more particles, and `large` explores more thoroughly.
- More `maxWorkers` can reduce wall time only after the database and runtime are healthy. It does not fix malformed JSON, bad data paths, or schema mismatches.
- For prediction/anomaly workflows, the predicted field has a special classifier-input path even if swarming decides not to include it in the normal encoded input path.

## Custom error metrics

`customErrorMetric` lets a JSON search definition override the default rolling error metric. A simple squared-error metric looks like:

```json
"customErrorMetric": {
  "customExpr": "(prediction - groundTruth) ** 2",
  "errorWindow": 500
}
```

For multi-line metric code, JSON requires escaping newlines and quotes. In a Python 2 workflow the legacy docs used `expr.encode("string_escape")`; in modern tooling, generate JSON with `json.dumps({"customExpr": expr, "errorWindow": 500})` instead of hand-escaping. The bundled linter checks only structure and string shape; it intentionally does not execute metric code.
