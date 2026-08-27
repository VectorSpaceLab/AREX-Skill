# Network API workflows

This reference is a self-contained operating guide for NuPIC legacy `nupic.engine.Network` workflows. It distills the public Network quick-start/guide, Network examples, region source specs, and engine tests into reusable patterns. Use it when the task says "build a NuPIC Network API pipeline", "link regions", "run the Network", "read classifier outputs", or "debug link names".

NuPIC legacy Network API code is Python 2.7-oriented and usually depends on compiled `nupic.bindings`, `numpy` 1.12.x-compatible packages, and Cap'n Proto/`pycapnp` for some serialization paths. For install/import failures, see the root guide from this reference directory: [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## Choose the right surface

- Use this Network API when the user needs explicit region graphs, custom regions, region output buffers, link debugging, or engine-level save/load awareness.
- Use [`../../opf-prediction/`](../../opf-prediction/) when the user wants the higher-level `ModelFactory` / OPF prediction API instead of managing regions and links.
- Use [`../../data-and-configuration/`](../../data-and-configuration/) for the three-header CSV format, `FileRecordStream`, data field names, model YAML structure, and predicted-field/data mismatches.
- Use [`../../htm-algorithms/`](../../htm-algorithms/) for encoder/SP/TM/classifier parameter semantics, active-array shapes, and direct algorithm-only workflows.

## Core API names

| Object | Import / call | Notes |
|---|---|---|
| Network | `from nupic.engine import Network`; `network = Network()` | Container for named regions and links. |
| Add region | `network.addRegion(name, typeString, jsonParams)` | `jsonParams` is commonly `json.dumps(params)` or `'{}'`. Returns a wrapped Region. |
| Link regions | `network.link(src, dest, "UniformLink", "", srcOutput="...", destInput="...")` | Use `UniformLink` and an empty policy string for ordinary buffer copies. |
| Initialize | `network.initialize()` | Call after all required regions, links, encoders, and data sources are set. |
| Run | `network.run(n)` | Runs `n` iterations through phases in dependency order. Prefer `n=1` when reading outputs after every row. |
| Get regions | `network.regions["SP"]` | Region wrapper; use `getSelf()` for Python region implementation object. |
| Parameters | `region.setParameter("learningMode", 1)` / `region.getParameter("learningMode")` | The wrapper dispatches to typed engine parameter accessors. Use exact names and compatible values. |
| Outputs | `region.getOutputData("bottomUpOut")` | Returns a buffer/array view. Output names are region-specific. |
| Spec inspection | `region.getInputNames()`, `region.getOutputNames()`, `Region.getSpecFromType("py.SPRegion")` | Useful before fixing link endpoint names. |

## Standard prediction graph

The canonical prediction graph is:

```text
RecordSensor --dataOut--> SPRegion --bottomUpOut--> TMRegion --bottomUpOut--> SDRClassifierRegion
     |                                                                          ^
     |--bucketIdxOut------------------------------------------------------------|
     |--actValueOut-------------------------------------------------------------|
     |--categoryOut-------------------------------------------------------------|
```

Optional reset links propagate sequence resets:

```text
RecordSensor --resetOut--> SPRegion.resetIn
RecordSensor --resetOut--> TMRegion.resetIn
```

### 1. Create the Network and sensor

```python
import json
from nupic.engine import Network
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder

network = Network()
network.addRegion("sensor", "py.RecordSensor", "{}")

sensorImpl = network.regions["sensor"].getSelf()
sensorImpl.encoder = MultiEncoder()
sensorImpl.encoder.addMultipleEncoders(modelParams["sensorParams"]["encoders"])
sensorImpl.dataSource = FileRecordStream(streamID="data.csv")
```

The CSV and `modelParams` schema are owned by [`../../data-and-configuration/`](../../data-and-configuration/). The important Network-side invariant is that `sensorImpl.encoder.getWidth()` is known before creating the SP region.

### 2. Add SP/TM/classifier regions

```python
spParams = dict(modelParams["spParams"])
spParams["inputWidth"] = sensorImpl.encoder.getWidth()
network.addRegion("SP", "py.SPRegion", json.dumps(spParams))

network.addRegion("TM", "py.TMRegion", json.dumps(modelParams["tmParams"]))

clParams = dict(modelParams["clParams"])
# clParams often includes steps such as "1,5", alpha, implementation, maxCategoryCount.
# If a model-param file stores a regionName key, consume it before addRegion.
regionName = clParams.pop("regionName", "SDRClassifierRegion")
network.addRegion("classifier", "py.%s" % regionName, json.dumps(clParams))
```

Minimum practical fields:

| Region | Type string | Required/important params | Important outputs |
|---|---|---|---|
| Sensor | `py.RecordSensor` | Runtime attributes `encoder`, `dataSource`; parameter `predictedField` before classifier use | `dataOut`, `resetOut`, `bucketIdxOut`, `actValueOut`, `categoryOut`, `sourceOut` |
| SP | `py.SPRegion` | `columnCount`, `inputWidth`, `spatialImp`, learning/inference mode | `bottomUpOut`, `anomalyScore`, optional top-down outputs |
| TM | `py.TMRegion` | `columnCount`, `inputWidth`, `cellsPerColumn`, `temporalImp`, learning/inference/anomaly/topDown modes | `bottomUpOut`, `topDownOut`, `anomalyScore`, `activeCells`, `predictedActiveCells` |
| Classifier | `py.SDRClassifierRegion` | `steps` as comma-separated string, `alpha`, `maxCategoryCount`, `implementation`, learning/inference mode | `actualValues`, `probabilities`, `categoriesOut` |

Parameter meaning and tuning belongs in [`../../htm-algorithms/`](../../htm-algorithms/). This sub-skill focuses on passing those parameters into regions correctly.

### 3. Link regions with explicit endpoint names

```python
def data_link(network, src, dest):
  network.link(src, dest, "UniformLink", "",
               srcOutput="dataOut", destInput="bottomUpIn")

def feedforward_link(network, src, dest):
  network.link(src, dest, "UniformLink", "",
               srcOutput="bottomUpOut", destInput="bottomUpIn")

def reset_link(network, src, dest):
  network.link(src, dest, "UniformLink", "",
               srcOutput="resetOut", destInput="resetIn")

def sensor_classifier_links(network, sensor, classifier):
  network.link(sensor, classifier, "UniformLink", "",
               srcOutput="bucketIdxOut", destInput="bucketIdxIn")
  network.link(sensor, classifier, "UniformLink", "",
               srcOutput="actValueOut", destInput="actValueIn")
  network.link(sensor, classifier, "UniformLink", "",
               srcOutput="categoryOut", destInput="categoryIn")

data_link(network, "sensor", "SP")
feedforward_link(network, "SP", "TM")
feedforward_link(network, "TM", "classifier")
sensor_classifier_links(network, "sensor", "classifier")
reset_link(network, "sensor", "SP")
reset_link(network, "sensor", "TM")
```

If link names are omitted, the engine uses default output/default input only. Be explicit while debugging because classifier and reset links are not defaults.

### 4. Set prediction field and modes

```python
network.regions["sensor"].setParameter("predictedField", "consumption")

for name in ("SP", "TM", "classifier"):
  network.regions[name].setParameter("learningMode", 1)
  network.regions[name].setParameter("inferenceMode", 1)

# Optional anomaly-specific flags:
# network.regions["TM"].setParameter("anomalyMode", 1)
# network.regions["TM"].setParameter("topDownMode", 1)
```

`predictedField` must match a data field known to the sensor's data source and encoder configuration. If this field is wrong, classifier `bucketIdxOut`/`actValueOut` may be empty or meaningless; route to [`../../data-and-configuration/`](../../data-and-configuration/) for CSV/model-param reconciliation.

### 5. Initialize, run, and read outputs

```python
network.initialize()

for row in range(numRows):
  network.run(1)
  classifier = network.regions["classifier"]
  actualValues = classifier.getOutputData("actualValues")
  probabilities = classifier.getOutputData("probabilities")
```

Classifier output shape:

- `steps = classifier.getSelf().stepsList` is a list such as `[1, 5]`.
- `N = classifier.getSelf().maxCategoryCount` is the category/value capacity.
- `probabilities` is flattened by step. Slice step `i` with `probabilities[i * N:(i + 1) * N]`.
- The predicted value for a step is `actualValues[stepProbs.argmax()]`; confidence is `stepProbs.max()`.

Helper:

```python
def classifier_predictions(network, classifierName="classifier"):
  classifier = network.regions[classifierName]
  actualValues = classifier.getOutputData("actualValues")
  probabilities = classifier.getOutputData("probabilities")
  steps = classifier.getSelf().stepsList
  N = classifier.getSelf().maxCategoryCount
  results = {}
  for i, step in enumerate(steps):
    stepProbs = probabilities[i * N:(i + 1) * N]
    best = stepProbs.argmax()
    results[step] = {
      "predictedValue": actualValues[best],
      "predictionConfidence": stepProbs[best],
    }
  return results
```

Other useful output reads:

```python
spActive = network.regions["SP"].getOutputData("bottomUpOut")
tmActiveOrCells = network.regions["TM"].getOutputData("bottomUpOut")
anomalyScore = network.regions["TM"].getOutputData("anomalyScore")[0]
rawValue = network.regions["sensor"].getOutputData("sourceOut")
```

## Anomaly-oriented graph variation

For temporal anomaly scoring without a classifier, add `py.AnomalyLikelihoodRegion` and link:

```python
network.addRegion("anomaly", "py.AnomalyLikelihoodRegion", "{}")
network.link("TM", "anomaly", "UniformLink", "",
             srcOutput="anomalyScore", destInput="rawAnomalyScore")
network.link("sensor", "anomaly", "UniformLink", "",
             srcOutput="sourceOut", destInput="metricValue")
network.regions["TM"].setParameter("anomalyMode", 1)
```

Then read `network.regions["anomaly"].getOutputData("anomalyLikelihood")[0]`. Parameter semantics for anomaly score/likelihood are covered by [`../../htm-algorithms/`](../../htm-algorithms/).

## Validation checklist before `initialize()`

- `python scripts/network_smoke.py` succeeds in the active legacy Python runtime.
- `sensorImpl.encoder` is non-`None` and `sensorImpl.encoder.getWidth() > 0`.
- `sensorImpl.dataSource` is non-`None` and uses a valid NuPIC stream; CSV details are in [`../../data-and-configuration/`](../../data-and-configuration/).
- `spParams["inputWidth"] == sensorImpl.encoder.getWidth()`.
- Region type strings match installed/registered region types exactly: built-ins usually have the `py.` prefix.
- Required classifier links exist if classifier predictions are expected: `bucketIdxOut -> bucketIdxIn`, `actValueOut -> actValueIn`, `categoryOut -> categoryIn`, and `bottomUpOut -> bottomUpIn`.
- `predictedField` is set on the sensor before expecting `actValueOut`/`bucketIdxOut` classifier learning.
- `learningMode` and `inferenceMode` are set using booleans or `0`/`1`, not arbitrary strings.

## Save/load and bundle safety

The engine can save a Network bundle, but bundles for Python regions normally include pickled Python region state. Treat bundle files as executable-code-equivalent: only load bundles produced by trusted code in the same dependency family. Do not accept a user-supplied or downloaded bundle as safe input. If Cap'n Proto/`pycapnp` is unavailable, serialization or newer schema paths may fail even when ordinary in-memory Network runs work.

## Evidence provenance

This reference was distilled from NuPIC legacy Network quick-start/guide material, Network examples, `nupic.engine` wrappers, region specs for `RecordSensor`, `SPRegion`, `TMRegion`, and `SDRClassifierRegion`, and Network unit/integration tests. The runtime guidance above is self-contained and does not require reopening those source files.
