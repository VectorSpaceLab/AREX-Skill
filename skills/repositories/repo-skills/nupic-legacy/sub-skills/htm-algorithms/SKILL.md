---
name: htm-algorithms
description: "Direct NuPIC legacy HTM encoders, SpatialPooler, TemporalMemory,
  SDRClassifier, anomaly score, and anomaly likelihood workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HTM Algorithms

Use this sub-skill when a task asks for direct NuPIC legacy HTM algorithm APIs: encoders, `SpatialPooler`, `TemporalMemory`, `SDRClassifier`, raw anomaly score, or anomaly likelihood for a small streaming scalar/temporal example.

NuPIC legacy is a Python 2.7 package. Direct algorithm workflows normally require installed `nupic`, `nupic.bindings`, `numpy` in the legacy-compatible range, and `pycapnp`/Cap'n Proto only when serialization is needed.

## Route first

- Stay here for: `ScalarEncoder`, `RandomDistributedScalarEncoder`, `DateEncoder`, `CategoryEncoder`, `MultiEncoder`, `SpatialPooler.compute`, `TemporalMemory.compute`, `SDRClassifier.compute`, `computeRawAnomalyScore`, and `AnomalyLikelihood.anomalyProbability`.
- Read [references/api-reference.md](references/api-reference.md) when you need constructor signatures, input/output shapes, classifier result keys, or anomaly helper semantics.
- Read [references/workflows.md](references/workflows.md) when you need a direct encoders -> SP -> TM -> classifier/anomaly recipe or a debugging checklist for algorithm pipelines.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an algorithm example fails with encoder parameter, active-array shape, TM state/reset, classifier dict, Python 2, bindings, or serialization errors.
- Run [scripts/algorithm_smoke.py](scripts/algorithm_smoke.py) when you need a deterministic installed-package smoke check for tiny encoders, SP/TM, classifier, and anomaly helpers.
- Route CSV stream headers, field metadata, OPF model parameter files, and config validation to [../data-and-configuration/](../data-and-configuration/).
- Route high-level `ModelFactory`, OPF inference dictionaries, checkpoints, and experiment workflows to [../opf-prediction/](../opf-prediction/).
- For package-wide install/import failures before algorithm code runs, start with the root troubleshooting guide at `../../references/troubleshooting.md`; local reference files also cross-link to that guide from their own relative paths.

## Direct API checklist

1. Confirm the runtime is Python 2.7 and can import `nupic`, `nupic.bindings`, and `numpy`.
2. Encode every raw value into a one-dimensional binary SDR. Allocate one zero-filled NumPy array per encoder with `encoder.getWidth()` and call `encoder.encodeIntoArray(value, bits)`.
3. Concatenate encoder outputs. Set `SpatialPooler(inputDimensions=(encodingWidth,), columnDimensions=(columnCount,), ...)` so `encodingWidth == len(concatenatedEncoding)`.
4. Allocate `activeArray = numpy.zeros(columnCount, dtype="uint32")`, call `sp.compute(encoding, learn, activeArray)`, then pass `numpy.nonzero(activeArray)[0]` to `TemporalMemory.compute`.
5. Set `TemporalMemory(columnDimensions=(columnCount,), ...)` to the same column count used by the SP. Use `tm.getActiveCells()` for classifier `patternNZ`; use `tm.getPredictiveCells()` plus `tm.columnForCell(cell)` to build next-step predicted columns for anomaly score.
6. For scalar predictions, call `classifier.compute(recordNum, patternNZ, {"bucketIdx": bucketIdx, "actValue": rawValue}, learn=True, infer=True)`. Look for integer step keys such as `1` plus the `"actualValues"` key in the result.
7. For anomaly checks, compare current active columns with previous-step predicted columns using `computeRawAnomalyScore(activeColumns, prevPredictedColumns)`, then optionally update `AnomalyLikelihood` with the raw value, anomaly score, and timestamp.

## Minimal validation command

From this sub-skill directory in a prepared NuPIC legacy environment:

```bash
python scripts/algorithm_smoke.py --mode all --records 20 --encoder scalar
```

Expected success signal: the script prints `PASS`, encoder/SP/TM dimensions, a final one-step prediction summary, and bounded anomaly likelihood values. If it fails before imports, use root install/import troubleshooting; if it fails after imports, use the local troubleshooting reference.

## Evidence provenance

This sub-skill distills NuPIC legacy algorithm evidence from source/doc paths such as `src/nupic/algorithms/`, `src/nupic/encoders/`, `docs/source/quick-start/algorithms.rst`, `docs/examples/algo/complete-algo-example.py`, `examples/sp/hello_sp.py`, `examples/tm/hello_tm.py`, and unit tests under `tests/unit/nupic/algorithms/` and `tests/unit/nupic/encoders/`. Runtime guidance here is self-contained; future agents should not need to open the original checkout examples to use it.
