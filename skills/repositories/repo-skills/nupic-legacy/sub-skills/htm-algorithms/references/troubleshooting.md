# HTM Algorithms Troubleshooting

Start here for direct encoder, `SpatialPooler`, `TemporalMemory`, `SDRClassifier`, anomaly score, and anomaly likelihood failures. If the failure happens before the direct algorithm code runs, also read the root cross-cutting install/import guide at [../../../references/troubleshooting.md](../../../references/troubleshooting.md).

## Quick triage

| Symptom | Likely owner | First action |
|---|---|---|
| `SyntaxError` around `print "..."`, `except ..., e`, or `xrange` | Python version | NuPIC legacy code and examples target Python 2.7. Run direct examples in Python 2.7, or port only your wrapper syntax while keeping NuPIC imports in the legacy environment. |
| `ImportError: No module named nupic` | Package install | Use root package troubleshooting before changing algorithm code. |
| `ImportError` mentioning `nupic.bindings`, `nupic.bindings.math`, or compiled algorithms | Compiled runtime | Fix the NuPIC bindings install; direct SP/TM/encoder imports depend on it. |
| Basic compute works but `read`/`write` serialization fails with `capnp`/Cap'n Proto errors | Serialization dependency | Install/fix `pycapnp` and Cap'n Proto; do not change SP/TM parameters to solve serialization. |
| `ValueError: Number of bits in the SDR ... must be >= 21` | Encoder settings | Increase `w` to at least 21 or deliberately set `forced=True` only for a known compatibility case. |
| SP compute shape/type error | SP input/output arrays | Match `len(inputVector)` to `inputDimensions` and `len(activeArray)` to `columnDimensions`. |
| TM learns nothing or predictions bleed across sequences | TM state/reset semantics | Pass active column indices, not dense arrays; reset only at real sequence boundaries. |
| Classifier returns missing keys or `ValueError` about record numbers | Classifier call contract | Use monotonic `recordNum`, non-empty `patternNZ`, `classification` keys `bucketIdx`/`actValue`, and check integer step keys plus `actualValues`. |

## Python 2.7 versus Python 3

NuPIC legacy public examples and source use Python 2 idioms such as `print "..."`, `reader.next()`, `xrange`, `itertools.izip`, and `except TypeError, e`. A Python 3 interpreter can fail before imports or during dependency import.

Recovery:

1. Confirm the interpreter:

   ```bash
   python --version
   ```

2. Use a Python 2.7 environment for installed `nupic` workflows.
3. If you write a new helper, you may make the helper's syntax Python 2/3 compatible for `--help`, but the actual NuPIC algorithm imports should still run under Python 2.7.
4. Do not copy Python 2-only snippets into a Python 3 application unless you port syntax and confirm the NuPIC package can import in that environment.

## Missing `nupic.bindings` or compiled runtime

Direct algorithm code commonly imports compiled binding modules indirectly:

- `nupic.algorithms.spatial_pooler` imports binding math types.
- `nupic.algorithms.temporal_memory` imports binding random/math support.
- Several encoders import binding math support.
- `SDRClassifierFactory` can select a C++ classifier implementation depending on configuration.

Common messages:

```text
ImportError: No module named nupic.bindings
ImportError: No module named nupic.bindings.math
ImportError: cannot import name ... from nupic.bindings...
```

Recovery:

1. Do not rewrite algorithm imports first; install/fix `nupic.bindings` for the same Python 2.7 environment as `nupic`.
2. Prefer direct `from nupic.algorithms.sdr_classifier import SDRClassifier` for pure-Python classifier smoke checks, but remember SP/TM still require bindings.
3. Run the bundled smoke helper after fixing imports:

   ```bash
   python ../scripts/algorithm_smoke.py --mode all --records 20
   ```

   If you are in this `references/` directory, the relative path above is correct; from the sub-skill root use `python scripts/algorithm_smoke.py`.

## Missing `pycapnp` for serialization

Many NuPIC legacy algorithm and encoder modules do:

```python
try:
  import capnp
except ImportError:
  capnp = None
```

That means ordinary in-memory construction and `compute` may work without `pycapnp`, but Cap'n Proto serialization methods (`read`, `write`, proto-specific load/save) will fail or be unavailable.

Recovery:

- If only serialization fails, install a compatible `pycapnp`/Cap'n Proto stack for the legacy environment.
- If direct `compute` fails before serialization, diagnose `nupic`, `nupic.bindings`, and `numpy` first.
- Avoid using pickle/Cap'n Proto files from untrusted sources.

## ScalarEncoder parameter mistakes

`ScalarEncoder` is strict because poor encodings make SP/TM behavior misleading.

| Mistake | Error or symptom | Fix |
|---|---|---|
| `w` is even | `Width must be an odd number` | Use an odd width such as `21`. |
| `w < 21` with default safety | `Number of bits in the SDR (...) must be >= 21` | Use `w=21` or larger. Use `forced=True` only when compatibility with an old parameter file is more important than SDR safety. |
| More than one of `n`, `radius`, `resolution` set | `Only one of n/radius/resolution can be specified` | Pick exactly one sizing strategy. |
| None of `n`, `radius`, `resolution` set | `One of n, radius, resolution must be specified` | Supply `resolution` for most scalar streams, or `n` when you want an exact output width. |
| `minval >= maxval` | Constructor error | Correct bounds; for values outside bounds use `clipInput=True` only when clipping is intended. |
| `periodic=True` but values equal `maxval` | Boundary surprises | Periodic encoders wrap; keep values strictly below `maxval` or normalize before encoding. |

Recommended scalar starter:

```python
ScalarEncoder(w=21, minval=0.0, maxval=100.0,
              resolution=1.0, clipInput=True, name="value")
```

If the user specifically asks about the `forced=True` caveat: it skips safety checks for compatibility, but it does not make a narrow SDR a good HTM representation. Prefer fixing `w`, `resolution`, or `n` unless reproducing an old model parameter file.

## DateEncoder input mistakes

`DateEncoder` expects a `datetime.datetime`, not a string.

```python
import datetime
stamp = datetime.datetime.strptime("7/2/10 9:00", "%m/%d/%y %H:%M")
```

If width is zero, no sub-fields were enabled. Enable at least one field:

```python
DateEncoder(timeOfDay=(21, 9.5), weekend=21)
```

## SpatialPooler dimensions and `activeArray` shape

SP has two independent shapes:

- `inputDimensions`: shape of the encoded input vector.
- `columnDimensions`: shape of the output column space.

For a flat stream:

```python
encoding_width = len(encoding)
column_count = 128
sp = SpatialPooler(inputDimensions=(encoding_width,),
                   columnDimensions=(column_count,), ...)
active_array = numpy.zeros(column_count, dtype="uint32")
sp.compute(encoding, True, active_array)
active_columns = numpy.nonzero(active_array)[0]
```

Do not allocate `active_array` with `encoding_width`. Do not pass a multi-dimensional array unless `inputDimensions`/`columnDimensions` are designed for that topology. If active columns are empty, print:

```python
print("encoding width", len(encoding))
print("input on bits", int(encoding.sum()))
print("active array length", len(active_array))
print("active count", len(numpy.nonzero(active_array)[0]))
```

Then inspect `stimulusThreshold`, `potentialPct`, `potentialRadius`, `numActiveColumnsPerInhArea`, and whether the input encoding has any on-bits.

## TemporalMemory active columns, learning, and reset semantics

TM expects iterable active column indices:

```python
active_columns = [int(i) for i in numpy.nonzero(active_array)[0]]
tm.compute(active_columns, learn=True)
```

Common mistakes:

| Mistake | Consequence | Fix |
|---|---|---|
| Passing dense `active_array` instead of indices | TM treats array values as columns or errors. | Pass `numpy.nonzero(active_array)[0]` converted to Python ints. |
| SP column count differs from TM column count | Cells map to unexpected columns or validation fails. | Use identical `column_count` for SP `columnDimensions` and TM `columnDimensions`. |
| Resetting every row | TM cannot learn transitions. | Use `tm.reset()` only at true sequence boundaries. |
| Never resetting between independent sequences | Predictions bleed across unrelated sequences. | Reset at end of each independent sequence/epoch. |
| Using `learn=False` during training | No sequence memory is learned. | Train with `learn=True`; use `learn=False` for evaluation/inference passes. |

To convert predictive cells to columns for next-step anomaly scoring:

```python
predicted_columns = sorted(set(tm.columnForCell(c)
                               for c in tm.getPredictiveCells()))
```

## SDRClassifier dict keys and result keys

Classifier input:

```python
result = classifier.compute(
    recordNum=count,
    patternNZ=active_cells,
    classification={"bucketIdx": bucket_idx, "actValue": raw_value},
    learn=True,
    infer=True)
```

Required checks:

- `recordNum` must increase monotonically; missing records may skip numbers, but do not go backward.
- `patternNZ` should be active cell indices from TM, not SP active columns, for the standard SP->TM->classifier pipeline.
- `classification` must contain `"bucketIdx"` and `"actValue"` when learning. Use `classification=None` only for infer-only calls.
- With `steps=[1]`, result keys are `"actualValues"` and integer `1`. With `steps=[1, 5]`, expect `"actualValues"`, `1`, and `5`.
- Step values are NumPy probability arrays indexed by bucket id; `actualValues` maps bucket id to representative values.

Top prediction:

```python
probability, value = sorted(zip(result[1], result["actualValues"]),
                            reverse=True)[0]
```

If `result == {}`, check whether `infer=False` or both `learn=False` and `infer=False` were used.

## Anomaly score and likelihood surprises

Raw anomaly score compares current active columns to previous predicted columns. Keep the update order straight:

1. SP computes current `active_columns`.
2. Raw anomaly uses current `active_columns` and `previous_predicted_columns` saved from the last row.
3. TM computes current row.
4. Convert `tm.getPredictiveCells()` to predicted columns and save them for the next row.

If the first several likelihood values are uninformative, remember that `AnomalyLikelihood` has a probationary/history period. Defaults are long (`learningPeriod=288`, `estimationSamples=100`). Use smaller periods only for smoke tests; for real streams, use a history window that matches cadence and expected seasonality.

## Reference-only source scripts and benchmarks

The generated skill bundles `scripts/algorithm_smoke.py` as the safe direct algorithm helper. Profiling and performance scripts from the source tree, such as Temporal Memory benchmarks and profiling helpers, are intentionally not bundled as runnable runtime tools because they are expensive, environment-sensitive, and measure performance rather than baseline correctness. Treat them as provenance for advanced performance investigations, not as default validation commands.
