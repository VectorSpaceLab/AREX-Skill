# Model Params, Aggregation, and Configuration

Evidence provenance: distilled from `docs/source/quick-start/example-model-params.rst`, `docs/examples/params/model.yaml`, `src/nupic/frameworks/opf/exp_description_api.py`, `src/nupic/support/nupic-default.xml`, and `src/nupic/support/configuration_base.py`.

## Where this fits

NuPIC legacy prediction workflows commonly flow through these artifacts:

1. A CSV stream with three metadata header rows; see [data-formats.md](data-formats.md).
2. A model params dictionary or YAML/JSON file with `model`, `version`, and `modelParams` keys.
3. An OPF model created by `ModelFactory.create(modelConfig, logLevel=40)` and enabled with `model.enableInference({'predictedField': '<field>'})`; use [../../opf-prediction/](../../opf-prediction/) for the run loop.
4. Optional swarming search definitions that generate model params; use [../../swarming/](../../swarming/) for search definition JSON and hypersearch actions.

This reference covers steps 1-2 and shared configuration values only.

## Minimal model params layout

A compact `HTMPrediction` model config has this shape:

```yaml
model: HTMPrediction
version: 1
aggregationInfo: null
predictAheadTime: null
modelParams:
  inferenceType: TemporalMultiStep
  predictedField: consumption      # optional in some generated configs; enableInference still matters
  sensorParams:
    verbosity: 0
    encoders:
      consumption:
        fieldname: consumption
        name: consumption
        type: RandomDistributedScalarEncoder
        resolution: 0.88
        seed: 1
      timestamp_timeOfDay:
        fieldname: timestamp
        name: timestamp_timeOfDay
        type: DateEncoder
        timeOfDay: [21, 1]
      timestamp_weekend:
        fieldname: timestamp
        name: timestamp_weekend
        type: DateEncoder
        weekend: 21
    sensorAutoReset: null
  spEnable: true
  spParams:
    inputWidth: 946
    columnCount: 2048
    spVerbosity: 0
    spatialImp: cpp
    globalInhibition: 1
    localAreaDensity: -1.0
    numActiveColumnsPerInhArea: 40
    seed: 1956
    potentialPct: 0.85
    synPermConnected: 0.1
    synPermActiveInc: 0.04
    synPermInactiveDec: 0.005
    boostStrength: 3.0
  tmEnable: true
  tmParams:
    verbosity: 0
    columnCount: 2048
    cellsPerColumn: 32
    inputWidth: 2048
    seed: 1960
    temporalImp: cpp
    newSynapseCount: 20
    initialPerm: 0.21
    permanenceInc: 0.1
    permanenceDec: 0.1
    maxAge: 0
    globalDecay: 0.0
    maxSynapsesPerSegment: 32
    maxSegmentsPerCell: 128
    minThreshold: 12
    activationThreshold: 16
    outputType: normal
    pamLength: 1
  clParams:
    verbosity: 0
    regionName: SDRClassifierRegion
    alpha: 0.1
    steps: '1,5'
    maxCategoryCount: 1000
    implementation: cpp
  trainSPNetOnlyIfRequested: false
```

Keep model params as a dictionary by the time they reach `ModelFactory.create`. YAML is convenient for humans, but a Python run script usually loads it into a dict before creating a model. JSON is easier to parse with only stdlib tools.

## Encoder-to-CSV consistency rules

For `modelParams.sensorParams.encoders`:

- The **encoder dictionary key** is an internal name and does not have to equal a CSV field. Example: `timestamp_timeOfDay` and `timestamp_weekend` can both point at `fieldname: timestamp`.
- Each active encoder config should include `fieldname: <csv-column-name>` unless it is a special encoder that intentionally does not consume a raw field.
- Every `fieldname` that consumes CSV data must appear in the CSV first header row exactly, including case and punctuation.
- The `name` inside the encoder config is usually a unique encoder/output name. Keep it unique across encoders to make logs and region outputs readable.
- If a predicted field is changed, update all places that refer to it: CSV header, encoder `fieldname`, optional `modelParams.predictedField`, OPF `enableInference({'predictedField': ...})`, and any swarm `inferenceArgs.predictedField`.

Validation command:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv \
  --model-params model_params.json \
  --predicted-field consumption
```

If the model params are YAML, the validator attempts to import `yaml`. If that import fails, convert the params to JSON or install PyYAML in the active Python environment; this is independent of NuPIC package imports.

## Building params for a new predicted field

1. **Choose the CSV column.** It must appear in row 1 and have a parseable type in row 2. Numeric prediction fields are usually `float` or `int`; category workflows usually use `int`, `list`, or a category encoder workflow that the target OPF config supports.
2. **Add/confirm encoders.** In `modelParams.sensorParams.encoders`, add an encoder whose `fieldname` equals the CSV column. Use [../../htm-algorithms/](../../htm-algorithms/) for direct encoder parameter semantics such as scalar width/resolution if needed.
3. **Set inference metadata.** For OPF prediction, use `model.enableInference({'predictedField': '<field>'})` in the run loop. Some configs also carry `modelParams.predictedField`; keep it aligned when present.
4. **Set classifier steps.** In `modelParams.clParams.steps`, use a comma-separated string such as `'1'` or `'1,5'` for SDR classifier region configs.
5. **Validate before running.** Use the bundled CSV validator with `--predicted-field` and `--model-params` before moving to [../../opf-prediction/](../../opf-prediction/).

## Aggregation blocks

The quick-start model file uses `aggregationInfo` to aggregate records before modeling. A null aggregation can be represented by `null` or by all period fields set to zero.

Shape:

```yaml
aggregationInfo:
  fields:
  - [consumption, mean]
  microseconds: 0
  milliseconds: 0
  seconds: 0
  minutes: 0
  hours: 1
  days: 0
  weeks: 0
  months: 0
  years: 0
```

Rules distilled from `nupic.data.aggregator`:

- `fields` is a list of `[fieldName, aggregationFunction]` pairs.
- Field names must exist in the input stream.
- Common aggregation functions include `first`, `last`, `sum`, `mean`, `max`, `min`, `mode`, and weighted mean as `wmean:<weightField>`.
- If timestamp (`T`), reset (`R`), or sequence (`S`) fields are present but omitted from `aggregationInfo.fields`, the aggregator adds them automatically with first-value behavior.
- A timestamp field is required for non-null time aggregation.
- `years`/`months` are handled as calendar units and are mutually exclusive with fixed-duration `weeks`/`days`/`hours`/`minutes`/`seconds`/`milliseconds`/`microseconds` periods in the source implementation.

When diagnosing aggregation output, first validate the CSV timestamp flag and timestamp parseability in [data-formats.md](data-formats.md), then verify the `aggregationInfo.fields` names and period values.

## Stream source paths and swarms

OPF experiment controls and swarm search definitions use stream dictionaries with a `source` string. Legacy OPF normalization expects file sources to begin with `file://`.

Good:

```json
{"source": "file:///absolute/path/to/data.csv"}
```

Risky or invalid in swarm/experiment contexts:

```json
{"source": "/absolute/path/to/data.csv"}
```

When drafting search definitions, hand off to [../../swarming/](../../swarming/) after checking the CSV field names here.

## Configuration files and environment overrides

NuPIC legacy configuration reads default properties, optional site/custom XML, and environment overrides.

Important mechanisms:

| Mechanism | Shape | Notes |
|---|---|---|
| Default config | packaged `nupic-default.xml` | Contains defaults such as classifier implementation, metric window, anomaly settings, and swarming database properties. |
| Site config path | `NTA_CONF_PATH=/dir1:/dir2` | Directories searched for config XML such as `nupic-site.xml`. Use the platform path separator. |
| Environment property override | `NTA_CONF_PROP_<property-with-dots-as-underscores>=value` | `Configuration.getString(prop)` checks this before stored XML properties. Values are strings; `getInt`, `getFloat`, and `getBool` cast them later. |

Examples:

```bash
# Override the default SDR classifier implementation for a process.
export NTA_CONF_PROP_nupic_opf_sdrClassifier_implementation=py

# Point swarming/job coordination at a specific local database host.
export NTA_CONF_PROP_nupic_cluster_database_host=127.0.0.1

# Boolean config values should be 0 or 1 because Configuration.getBool casts ints.
export NTA_CONF_PROP_nupic_hypersearch_enableModelMaturity=1
```

Recovery checklist for config override bugs:

1. Translate property names exactly: `nupic.cluster.database.host` becomes `NTA_CONF_PROP_nupic_cluster_database_host`.
2. Check shell quoting; values are strings and may need quotes if they contain spaces or punctuation.
3. Check whether the code path calls `getString`, `getInt`, `getFloat`, or `getBool`; invalid casts can raise later.
4. If a full NuPIC import fails before config is read, switch to [root troubleshooting](../../../references/troubleshooting.md) because the issue is package/runtime, not configuration shape.
