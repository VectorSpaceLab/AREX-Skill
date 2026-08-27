# HTM Algorithms API Reference

This reference is for direct NuPIC legacy algorithm code, not OPF `ModelFactory` models. NuPIC legacy is Python 2.7 oriented and direct SP/TM code normally depends on compiled `nupic.bindings`; `pycapnp`/Cap'n Proto is only needed when using Cap'n Proto serialization APIs.

## Import map

```python
import datetime
import numpy

from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder
from nupic.encoders.date import DateEncoder
from nupic.encoders.category import CategoryEncoder
from nupic.encoders.multi import MultiEncoder

from nupic.algorithms.spatial_pooler import SpatialPooler
from nupic.algorithms.temporal_memory import TemporalMemory
from nupic.algorithms.sdr_classifier import SDRClassifier
from nupic.algorithms.anomaly import Anomaly, computeRawAnomalyScore
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
```

If importing `SpatialPooler`, `TemporalMemory`, or encoders fails with a bindings-related error, go to local [troubleshooting](troubleshooting.md#missing-nupicbindings-or-compiled-runtime) and then the root package troubleshooting guide.

## Encoder APIs

All standard encoders expose `getWidth()` and `encodeIntoArray(value, outputArray)`. Allocate `outputArray` as a zero-filled one-dimensional NumPy array of exactly `encoder.getWidth()` before calling `encodeIntoArray`.

| Encoder | Constructor | Use when | Key checks |
|---|---|---|---|
| `ScalarEncoder` | `ScalarEncoder(w, minval, maxval, periodic=False, n=0, radius=0, resolution=0, name=None, verbosity=0, clipInput=False, forced=False)` | Numeric scalar with contiguous on-bits and known range. | `w` must be odd; exactly one of `n`, `radius`, or `resolution` must be set; `w >= 21` unless `forced=True`; `minval < maxval`. |
| `RandomDistributedScalarEncoder` | `RandomDistributedScalarEncoder(resolution, w=21, n=400, name=None, offset=None, seed=42, verbosity=0)` | Numeric scalar when you prefer stable distributed bits and do not want to hand-pick a fixed `minval`/`maxval`. | `resolution` controls how far apart values must be before they differ; default `w=21` is HTM-safe. |
| `DateEncoder` | `DateEncoder(season=0, dayOfWeek=0, weekend=0, holiday=0, timeOfDay=0, customDays=0, name='', forced=True, holidays=())` | Temporal fields such as time-of-day, day-of-week, weekend, season, holidays. | Input is a `datetime.datetime`; each non-zero field adds a sub-encoding to total width. |
| `CategoryEncoder` | `CategoryEncoder(w, categoryList, name='category', verbosity=0, forced=False)` | Small fixed list of categories. | `categoryList` must contain every category you will encode; use `forced=True` only when deliberately bypassing width safety checks. |
| `MultiEncoder` | `MultiEncoder(); addMultipleEncoders(fieldEncodings)` | Named field encodings in a fixed order. | `fieldEncodings` maps field keys to dicts with `fieldname`, `type`, and that encoder's parameters; output width is the sum of member widths. |

### Scalar/temporal encoding template

```python
value_encoder = ScalarEncoder(
    w=21, minval=0.0, maxval=100.0, resolution=1.0,
    name="value", clipInput=True)
time_encoder = DateEncoder(timeOfDay=(21, 9.5), weekend=21)

value_bits = numpy.zeros(value_encoder.getWidth(), dtype="uint32")
time_bits = numpy.zeros(time_encoder.getWidth(), dtype="uint32")

value_encoder.encodeIntoArray(42.0, value_bits)
time_encoder.encodeIntoArray(datetime.datetime(2020, 1, 1, 9, 0), time_bits)
encoding = numpy.concatenate([time_bits, value_bits]).astype("uint32")
assert len(encoding) == time_encoder.getWidth() + value_encoder.getWidth()
```

### Bucket indices for classifiers

For scalar predictions, keep the raw numeric value and the encoder bucket together:

```python
bucket_idx = value_encoder.getBucketIndices(42.0)[0]
classification = {"bucketIdx": bucket_idx, "actValue": 42.0}
```

`SDRClassifier` also supports list-valued `bucketIdx`/`actValue` for multi-class cases, but the direct scalar pipeline usually passes a single bucket index and a single actual value.

## SpatialPooler

Verified constructor and compute signature:

```python
SpatialPooler(
    inputDimensions=(32, 32), columnDimensions=(64, 64),
    potentialRadius=16, potentialPct=0.5, globalInhibition=False,
    localAreaDensity=-1.0, numActiveColumnsPerInhArea=10.0,
    stimulusThreshold=0, synPermInactiveDec=0.008,
    synPermActiveInc=0.05, synPermConnected=0.1,
    minPctOverlapDutyCycle=0.001, dutyCyclePeriod=1000,
    boostStrength=0.0, seed=-1, spVerbosity=0, wrapAround=True)

sp.compute(inputVector, learn, activeArray)
```

Shape contract:

- `inputVector`: one-dimensional binary/dense vector whose length is `product(inputDimensions)`.
- `activeArray`: mutable one-dimensional NumPy array with length `product(columnDimensions)`, usually `numpy.zeros(columnCount, dtype="uint32")`.
- After `compute`, active columns are `numpy.nonzero(activeArray)[0]`.
- For a one-dimensional stream, set `inputDimensions=(encodingWidth,)` and `columnDimensions=(columnCount,)`.

Minimal allocation:

```python
encoding_width = len(encoding)
column_count = 128
sp = SpatialPooler(inputDimensions=(encoding_width,),
                   columnDimensions=(column_count,),
                   potentialRadius=encoding_width,
                   potentialPct=0.8,
                   globalInhibition=True,
                   numActiveColumnsPerInhArea=10,
                   seed=42)
active_array = numpy.zeros(column_count, dtype="uint32")
sp.compute(encoding, True, active_array)
active_columns = [int(i) for i in numpy.nonzero(active_array)[0]]
```

## TemporalMemory

Verified constructor and compute signature:

```python
TemporalMemory(
    columnDimensions=(2048,), cellsPerColumn=32,
    activationThreshold=13, initialPermanence=0.21,
    connectedPermanence=0.5, minThreshold=10,
    maxNewSynapseCount=20, permanenceIncrement=0.1,
    permanenceDecrement=0.1, predictedSegmentDecrement=0.0,
    maxSegmentsPerCell=255, maxSynapsesPerSegment=255,
    seed=42, **kwargs)

tm.compute(activeColumns, learn=True)
```

State methods used by direct pipelines:

| Method | Return/use |
|---|---|
| `tm.getActiveCells()` | Active cell indices for the current step; pass to `SDRClassifier.compute(..., patternNZ=activeCells, ...)`. |
| `tm.getPredictiveCells()` | Cell indices predicted for the next step. Convert to columns with `tm.columnForCell(cell)` before raw anomaly scoring. |
| `tm.getWinnerCells()` | Winner cells for inspection/debugging. |
| `tm.columnForCell(cell)` | Column index containing a cell index. |
| `tm.numberOfColumns()` | Total TM column count; should match SP `columnCount`. |
| `tm.reset()` | Clear temporal state between unrelated sequences or epoch boundaries. |

TM receives active **column indices**, not a dense binary array. Prefer sorted Python integers:

```python
tm = TemporalMemory(columnDimensions=(column_count,), cellsPerColumn=4,
                    activationThreshold=4, minThreshold=3,
                    maxNewSynapseCount=8, seed=42)
tm.compute(active_columns, learn=True)
active_cells = list(tm.getActiveCells())
predicted_columns = sorted(set(tm.columnForCell(c)
                               for c in tm.getPredictiveCells()))
```

## SDRClassifier

Verified constructor and compute signature:

```python
SDRClassifier(steps=[1], alpha=0.001, actValueAlpha=0.3, verbosity=0)
classifier.compute(recordNum, patternNZ, classification, learn, infer)
```

Input contract:

- `recordNum`: monotonically increasing record number. It may skip numbers for missing records but must not go backward.
- `patternNZ`: non-empty list of active indices, usually `tm.getActiveCells()`.
- `classification`: either `None` for infer-only calls or a dict with keys `"bucketIdx"` and `"actValue"`.
- `learn` / `infer`: booleans. `learn=True, infer=False` returns `{}`; `infer=True` returns probabilities.

Result contract:

```python
result = classifier.compute(
    recordNum=count,
    patternNZ=active_cells,
    classification={"bucketIdx": bucket_idx, "actValue": raw_value},
    learn=True,
    infer=True)

assert "actualValues" in result
assert 1 in result              # when steps=[1]
probabilities = result[1]       # NumPy array indexed by bucket id
actual_values = result["actualValues"]
```

Best one-step scalar prediction:

```python
probability, predicted_value = sorted(
    zip(result[1], result["actualValues"]), reverse=True)[0]
```

## Anomaly score and likelihood

Raw anomaly score:

```python
from nupic.algorithms.anomaly import computeRawAnomalyScore
score = computeRawAnomalyScore(activeColumns, prevPredictedColumns)
```

- `activeColumns`: active columns for the current step.
- `prevPredictedColumns`: columns predicted at the previous step.
- Return is a float in `[0, 1]`: `0.0` for no active columns or perfect prediction, `1.0` for no overlap, and fractional for partial overlap.

Likelihood helper:

```python
likelihood = AnomalyLikelihood(
    learningPeriod=20, estimationSamples=20,
    historicWindowSize=200, reestimationPeriod=20)
prob = likelihood.anomalyProbability(raw_value, score, timestamp)
```

`anomalyProbability` returns a bounded likelihood/probability-like value after maintaining historical scores. The default constructor is tuned for longer streams (`learningPeriod=288`, `estimationSamples=100`), so tiny tests should use smaller periods only for smoke validation. For production anomaly scoring, choose periods that reflect stream cadence and expected history length.

The `Anomaly` convenience class can compute pure, likelihood, or weighted scores:

```python
anomaly = Anomaly(mode=Anomaly.MODE_PURE)
score = anomaly.compute(active_columns, previous_predicted_columns)
```

## Serialization note

Many algorithm and encoder classes attempt optional `capnp` imports. Ordinary in-memory `compute` workflows do not require `pycapnp`, but Cap'n Proto `read`/`write` serialization does. If serialization fails while basic compute succeeds, fix `pycapnp`/Cap'n Proto rather than changing SP/TM/encoder parameters.
