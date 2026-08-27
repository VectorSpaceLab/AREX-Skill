# Network API troubleshooting

Use this guide for NuPIC legacy `nupic.engine.Network` failures after the package imports, or when the failure message mentions regions, links, parameters, initialization, classifier outputs, or Network bundles. For package-level Python 2.7, `nupic.bindings`, `numpy`, Cap'n Proto, or `pycapnp` installation/import failures, start with the root guide at [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## Fast diagnostic flow

1. Run the bundled smoke helper in the same Python runtime:
   ```bash
   python scripts/network_smoke.py --inspect-region-types
   ```
   From this reference directory, the helper is [`../scripts/network_smoke.py`](../scripts/network_smoke.py).
2. Confirm the graph lifecycle: all regions added, sensor `encoder` and `dataSource` set, all required links created, modes/parameters set, then `network.initialize()`, then `network.run(1)`.
3. Print the region spec names before changing code:
   ```python
   for name, region in network.regions.items():
     print(name, region.getInputNames(), region.getOutputNames())
   ```
4. If a failure is about data fields, `FileRecordStream`, CSV headers, or model params, route to [`../../data-and-configuration/`](../../data-and-configuration/). If it is about encoder/SP/TM/classifier parameter meaning, route to [`../../htm-algorithms/`](../../htm-algorithms/). If the user does not need explicit regions, consider [`../../opf-prediction/`](../../opf-prediction/).

## Common symptoms and fixes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError: No module named nupic.bindings`, `engine_internal`, or `PyRegion` | Wrong Python runtime or incomplete compiled NuPIC legacy install. | Use a Python 2.7-compatible environment with NuPIC legacy runtime dependencies (`nupic.bindings`, `numpy` 1.12.x family, Cap'n Proto/`pycapnp` where needed). Then rerun `python scripts/network_smoke.py`. See root [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md). |
| `Region type ... not found`, `py.NonExistingNode`, or import failure inside `addRegion` | Wrong type string or custom region not registered/importable. | Built-in Python regions use strings like `py.RecordSensor`, `py.SPRegion`, `py.TMRegion`, `py.SDRClassifierRegion`. For custom regions call `Network.registerRegion(MyRegion)` before `addRegion("name", "py.MyRegion", ...)`; see [`custom-region.md`](custom-region.md). |
| `Input ... does not exist`, `Output ... does not exist`, or initialization/link failure | Bad `srcOutput` or `destInput` name, or omitted endpoint default was not the desired one. | Inspect `region.getOutputNames()` on the source and `region.getInputNames()` on the destination. Use the explicit link table in [`network-workflows.md`](network-workflows.md). |
| Initialization fails with `RecordSensor -- encoder has not been set` or `dataSource has not been set` | Sensor runtime attributes were not attached before `network.initialize()`. | Set `network.regions["sensor"].getSelf().encoder = MultiEncoder(...)` and `.dataSource = FileRecordStream(...)` before adding dependent regions/initializing. |
| Initialization fails due to `inputWidth`, `columnCount`, or buffer width | SP/TM params do not match upstream output width, often because `spParams["inputWidth"]` remained `0`. | Set `spParams["inputWidth"] = sensor.encoder.getWidth()` before `addRegion("SP", "py.SPRegion", ...)`. Check downstream `columnCount`/`inputWidth` consistency. |
| `run()` computes nothing useful or fails on first iteration | Network was not explicitly initialized after final graph edits, or required links/attributes were added after initialization. | Build/link/set attributes first, call `network.initialize()`, then `network.run(1)`. If the graph changes, rebuild or reinitialize as appropriate rather than mutating an already-running graph. |
| `setParameter -- parameter name ... does not exist` | Parameter name belongs to a different region type or uses the wrong spelling/case. | Inspect `region.getSpec().parameters` or use `python scripts/network_smoke.py --inspect-region-types`. Common names: `predictedField` on sensor; `learningMode`/`inferenceMode` on SP, TM, classifier; `anomalyMode` on SP/TM. |
| Parameter type errors or silent bad behavior | Typed engine parameter mismatch: booleans/integers/strings are not interchangeable for every parameter. | Use `0`/`1` or `True`/`False` for bool-like modes; use a byte/string value for `predictedField`; pass create-time region params through JSON with numeric values already numeric. |
| Classifier `actualValues`/`probabilities` are empty, zeros, or misaligned | Missing sensor-classifier links, `predictedField` not set/mismatched, classifier inference disabled, or not enough training records. | Add `bucketIdxOut -> bucketIdxIn`, `actValueOut -> actValueIn`, `categoryOut -> categoryIn`, and `TM.bottomUpOut -> classifier.bottomUpIn`; set `sensor.predictedField`; enable classifier `learningMode` and `inferenceMode`; run enough rows. |
| Prediction confidence indexing is wrong | `probabilities` is flattened by prediction step and category capacity. | Slice with `N = classifier.getSelf().maxCategoryCount`; for step index `i`, use `probabilities[i * N:(i + 1) * N]`, then `argmax()` into `actualValues`. |
| Anomaly likelihood output missing | Anomaly links or modes are missing. | Link `TM.anomalyScore -> AnomalyLikelihoodRegion.rawAnomalyScore` and `sensor.sourceOut -> metricValue`; set TM `anomalyMode` if using TM anomaly score. |
| Bundle save/load fails with Cap'n Proto, schema, or pickle errors | Serialization path requires `pycapnp`/Cap'n Proto support and Python-region state may be pickled. | Prefer regenerating the graph from code. Only load bundles produced by trusted code in a compatible runtime. Treat bundles as unsafe executable-code-equivalent artifacts. |

## Link endpoint reference

| Source -> destination | `srcOutput` | `destInput` | Required for |
|---|---|---|---|
| `RecordSensor -> SPRegion` | `dataOut` | `bottomUpIn` | Sensor encodings into SP |
| `SPRegion -> TMRegion` | `bottomUpOut` | `bottomUpIn` | SP active columns into TM |
| `TMRegion -> SDRClassifierRegion` | `bottomUpOut` | `bottomUpIn` | TM pattern into classifier |
| `RecordSensor -> SDRClassifierRegion` | `bucketIdxOut` | `bucketIdxIn` | Classifier bucket target |
| `RecordSensor -> SDRClassifierRegion` | `actValueOut` | `actValueIn` | Classifier actual numeric value |
| `RecordSensor -> SDRClassifierRegion` | `categoryOut` | `categoryIn` | Classifier category input; the classifier spec marks this required |
| `RecordSensor -> SPRegion` | `resetOut` | `resetIn` | Optional sequence reset propagation |
| `RecordSensor -> TMRegion` | `resetOut` | `resetIn` | Optional sequence reset propagation |
| `TMRegion -> AnomalyLikelihoodRegion` | `anomalyScore` | `rawAnomalyScore` | Anomaly likelihood graph |
| `RecordSensor -> AnomalyLikelihoodRegion` | `sourceOut` | `metricValue` | Anomaly likelihood metric value |

## Spec inspection snippets

Use these in user code or an interactive Python 2.7 session after the package imports:

```python
from nupic.engine import Region
for regionType in ("py.RecordSensor", "py.SPRegion", "py.TMRegion", "py.SDRClassifierRegion"):
  spec = Region.getSpecFromType(regionType)
  print(regionType)
  print("  inputs:", [spec.inputs.getByIndex(i)[0] for i in xrange(spec.inputs.getCount())])
  print("  outputs:", [spec.outputs.getByIndex(i)[0] for i in xrange(spec.outputs.getCount())])
```

After constructing a graph:

```python
for name, region in network.regions.items():
  print(name)
  print("  inputs:", region.getInputNames())
  print("  outputs:", region.getOutputNames())
```

## Unsafe pickle/bundle note

Network serialization stores the graph structure plus region implementation state. For Python `PyRegion` regions, that state is commonly pickled. Do not load untrusted bundles, do not exchange bundles as a safe data format, and do not treat a bundle load failure as evidence that the in-memory Network recipe is wrong. Prefer a plain construction script plus explicit data/config files for reproducible work.

## Evidence provenance

This troubleshooting matrix was distilled from NuPIC legacy Network guide material, Network examples, region specs, and engine tests that exercise missing region types, bad output names, typed parameters, and initialization behavior. It is self-contained for runtime use.
