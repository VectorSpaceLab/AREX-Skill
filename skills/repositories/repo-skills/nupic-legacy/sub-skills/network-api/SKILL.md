---
name: network-api
description: "Build, link, run, inspect, and debug NuPIC legacy Network API
  pipelines and custom PyRegion regions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NuPIC Legacy Network API

Use this sub-skill when the user asks to build a NuPIC `Network`, add/link regions, initialize/run a Network API pipeline, read region outputs, debug link names, or create a custom Python region. NuPIC legacy is a Python 2.7-era package; Network API workflows normally require `nupic.bindings`, `numpy` 1.12.x-compatible runtime packages, and working Cap'n Proto/`pycapnp` support for some serialization paths.

Do **not** use this sub-skill for every prediction task. If the user wants the higher-level OPF model workflow, route to [`../opf-prediction/`](../opf-prediction/). If the task is about CSV headers, `FileRecordStream`, or model parameter files, route to [`../data-and-configuration/`](../data-and-configuration/). If the task is about encoder, SP, TM, or classifier parameter semantics outside a Network graph, route to [`../htm-algorithms/`](../htm-algorithms/). For package installation/import failures, use the root troubleshooting guide at [`../../references/troubleshooting.md`](../../references/troubleshooting.md) first.

## Fast path

1. Confirm that the legacy runtime can import and construct an empty Network:
   ```bash
   python scripts/network_smoke.py
   ```
2. Build the graph in this order: `Network()` -> `addRegion(...)` -> attach `RecordSensor.encoder` and `RecordSensor.dataSource` -> set `SPRegion` `inputWidth` -> `link(...)` -> set `predictedField`/modes -> `initialize()` -> `run(n)`.
3. Use region type strings exactly: `py.RecordSensor`, `py.SPRegion`, `py.TMRegion`, and `py.SDRClassifierRegion` unless a custom region has been registered.
4. Use explicit link endpoint names when debugging: `srcOutput="dataOut"`, `destInput="bottomUpIn"`, `srcOutput="bottomUpOut"`, `destInput="bottomUpIn"`, and sensor-to-classifier `bucketIdxOut`, `actValueOut`, `categoryOut` links.
5. Query outputs with `network.regions["name"].getOutputData("outputName")`; classifier predictions come from `actualValues` and flattened `probabilities` arrays.

## Bundled runtime resources

- [`references/network-workflows.md`](references/network-workflows.md): read this for the complete sensor -> SP -> TM -> classifier construction recipe, link table, output shapes, validation checks, and safe serialization notes.
- [`references/custom-region.md`](references/custom-region.md): read this when the user needs a custom `PyRegion` skeleton, registration steps, `getSpec()` contract, or dynamic output width handling.
- [`references/troubleshooting.md`](references/troubleshooting.md): read this when Network imports, region type strings, link endpoint names, initialization, typed parameters, classifier outputs, or bundle loading/saving fail.
- [`scripts/network_smoke.py`](scripts/network_smoke.py): run this deterministic helper to import `nupic.engine.Network`, construct an empty network by default, optionally inspect built-in region specs, and print a safe next-step pipeline template without requiring source data files.

## Minimal Network API shape

```python
import json
from nupic.engine import Network

network = Network()
network.addRegion("sensor", "py.RecordSensor", "{}")
# Attach a MultiEncoder and FileRecordStream to network.regions["sensor"].getSelf().

network.addRegion("SP", "py.SPRegion", json.dumps(spParams))
network.addRegion("TM", "py.TMRegion", json.dumps(tmParams))
network.addRegion("classifier", "py.SDRClassifierRegion", json.dumps(clParams))

network.link("sensor", "SP", "UniformLink", "", srcOutput="dataOut", destInput="bottomUpIn")
network.link("SP", "TM", "UniformLink", "", srcOutput="bottomUpOut", destInput="bottomUpIn")
network.link("TM", "classifier", "UniformLink", "", srcOutput="bottomUpOut", destInput="bottomUpIn")
network.link("sensor", "classifier", "UniformLink", "", srcOutput="bucketIdxOut", destInput="bucketIdxIn")
network.link("sensor", "classifier", "UniformLink", "", srcOutput="actValueOut", destInput="actValueIn")
network.link("sensor", "classifier", "UniformLink", "", srcOutput="categoryOut", destInput="categoryIn")

network.regions["sensor"].setParameter("predictedField", "consumption")
for name in ("SP", "TM", "classifier"):
  network.regions[name].setParameter("learningMode", 1)
  network.regions[name].setParameter("inferenceMode", 1)

network.initialize()
network.run(1)
```

Keep generated or copied user examples self-contained. Do not require future agents to open the original repository docs, tests, scripts, examples, notebooks, or local checkout paths.
