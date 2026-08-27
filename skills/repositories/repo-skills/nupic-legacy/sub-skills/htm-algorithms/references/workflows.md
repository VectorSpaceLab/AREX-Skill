# HTM Algorithm Workflows

Use these workflows when the user wants direct NuPIC algorithm objects rather than OPF `ModelFactory` or Network API regions. For CSV header validation, model parameter YAML, or stream definitions, route to [data and configuration](../../data-and-configuration/). For high-level prediction models, route to [OPF prediction](../../opf-prediction/).

## Workflow: build a tiny scalar/temporal HTM pipeline

Goal: consume streaming rows like `(timestamp, value)` and produce SP active columns, TM state, one-step classifier predictions, and anomaly scores.

### 1. Choose encoders

Use one temporal encoder and one scalar encoder. `ScalarEncoder` is explicit and bounded; `RandomDistributedScalarEncoder` is convenient when the scalar range is not fixed.

```python
import datetime
import numpy

from nupic.encoders.date import DateEncoder
from nupic.encoders.scalar import ScalarEncoder
# Alternative: from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder

# Time-of-day plus weekend bits.
time_encoder = DateEncoder(timeOfDay=(21, 9.5), weekend=21)

# Bounded scalar bits. Exactly one of n/radius/resolution must be specified.
value_encoder = ScalarEncoder(w=21, minval=0.0, maxval=100.0,
                              resolution=1.0, name="value",
                              clipInput=True)
```

Validation:

```python
encoding_width = time_encoder.getWidth() + value_encoder.getWidth()
assert encoding_width > 0
```

### 2. Create SP and TM with matching column counts

```python
from nupic.algorithms.spatial_pooler import SpatialPooler
from nupic.algorithms.temporal_memory import TemporalMemory

column_count = 128
sp = SpatialPooler(inputDimensions=(encoding_width,),
                   columnDimensions=(column_count,),
                   potentialRadius=encoding_width,
                   potentialPct=0.8,
                   globalInhibition=True,
                   numActiveColumnsPerInhArea=10,
                   synPermActiveInc=0.03,
                   synPermInactiveDec=0.008,
                   synPermConnected=0.1,
                   seed=42)

tm = TemporalMemory(columnDimensions=(column_count,),
                    cellsPerColumn=4,
                    activationThreshold=4,
                    minThreshold=3,
                    maxNewSynapseCount=8,
                    permanenceIncrement=0.1,
                    permanenceDecrement=0.0,
                    seed=42)
```

Validation:

- `len(encoding) == product(sp.inputDimensions)`.
- `len(active_array) == product(sp.columnDimensions) == column_count`.
- `tm.columnDimensions == (column_count,)`.

### 3. Encode and compute one row

```python
def encode_row(timestamp, value):
  time_bits = numpy.zeros(time_encoder.getWidth(), dtype="uint32")
  value_bits = numpy.zeros(value_encoder.getWidth(), dtype="uint32")
  time_encoder.encodeIntoArray(timestamp, time_bits)
  value_encoder.encodeIntoArray(value, value_bits)
  encoding = numpy.concatenate([time_bits, value_bits]).astype("uint32")
  assert len(encoding) == encoding_width
  return encoding

active_array = numpy.zeros(column_count, dtype="uint32")
encoding = encode_row(datetime.datetime(2020, 1, 1, 9, 0), 42.0)
sp.compute(encoding, True, active_array)
active_columns = [int(i) for i in numpy.nonzero(active_array)[0]]

tm.compute(active_columns, learn=True)
active_cells = list(tm.getActiveCells())
```

Do not pass the dense SP `active_array` to TM. TM expects active column indices.

### 4. Add one-step scalar prediction

```python
from nupic.algorithms.sdr_classifier import SDRClassifier

classifier = SDRClassifier(steps=[1], alpha=0.1, actValueAlpha=0.1, verbosity=0)
bucket_idx = value_encoder.getBucketIndices(42.0)[0]
result = classifier.compute(
    recordNum=0,
    patternNZ=active_cells,
    classification={"bucketIdx": bucket_idx, "actValue": 42.0},
    learn=True,
    infer=True)

assert set(result.keys()) == set(["actualValues", 1])
```

After several records, extract the highest-probability prediction:

```python
probability, prediction = sorted(zip(result[1], result["actualValues"]),
                                 reverse=True)[0]
```

### 5. Add raw anomaly score and likelihood

Compute raw anomaly for record `t` from active columns at `t` and predicted columns produced by TM at `t-1`.

```python
from nupic.algorithms.anomaly import computeRawAnomalyScore
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood

likelihood = AnomalyLikelihood(learningPeriod=20, estimationSamples=20,
                               historicWindowSize=200,
                               reestimationPeriod=20)
previous_predicted_columns = []

# inside the streaming loop, after SP active_columns and before updating TM:
raw_score = computeRawAnomalyScore(active_columns, previous_predicted_columns)

# after tm.compute(...): save predictions for the next row
previous_predicted_columns = sorted(set(tm.columnForCell(c)
                                        for c in tm.getPredictiveCells()))
prob = likelihood.anomalyProbability(value, raw_score, timestamp)
assert 0.0 <= raw_score <= 1.0
assert 0.0 <= prob <= 1.0
```

For tiny smoke tests, smaller likelihood learning periods are acceptable. For real streams, avoid reading too much into likelihood until the probationary/history window has enough data.

## Workflow: debug SpatialPooler dimensions

Use this when a user reports shape mismatch, empty active columns, or unexpected sparsity.

1. Print encoder widths:

   ```python
   print("time width", time_encoder.getWidth())
   print("value width", value_encoder.getWidth())
   print("encoding width", encoding_width)
   ```

2. Assert the encoded vector width before SP:

   ```python
   assert len(encoding) == encoding_width
   ```

3. Allocate `active_array` from SP column count, not input width:

   ```python
   active_array = numpy.zeros(column_count, dtype="uint32")
   sp.compute(encoding, True, active_array)
   assert len(active_array) == column_count
   active_columns = numpy.nonzero(active_array)[0]
   assert len(active_columns) > 0
   ```

4. If active columns are empty, inspect `stimulusThreshold`, `potentialPct`, `potentialRadius`, and whether input bits are actually non-zero:

   ```python
   print("input on bits", int(encoding.sum()))
   print("active columns", len(active_columns))
   ```

5. If TM later fails, confirm `TemporalMemory(columnDimensions=(column_count,))` uses the same count as SP.

## Workflow: use ScalarEncoder vs RandomDistributedScalarEncoder

Choose `ScalarEncoder` when the user knows a range and wants inspectable contiguous encodings:

```python
value_encoder = ScalarEncoder(w=21, minval=0.0, maxval=100.0,
                              resolution=1.0, clipInput=True)
```

Choose `RandomDistributedScalarEncoder` when the range is open-ended and a fixed-width distributed representation is acceptable:

```python
from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder
value_encoder = RandomDistributedScalarEncoder(resolution=1.0, w=21,
                                               n=400, seed=42)
```

In both cases, use:

```python
bits = numpy.zeros(value_encoder.getWidth(), dtype="uint32")
value_encoder.encodeIntoArray(value, bits)
bucket_idx = value_encoder.getBucketIndices(value)[0]
```

## Workflow: add DateEncoder fields

`DateEncoder` concatenates only fields you enable. Common choices:

```python
# Time of day with width 21 and radius 9.5 hours, plus weekend flag width 21.
DateEncoder(timeOfDay=(21, 9.5), weekend=21)

# Day-of-week periodic encoding only.
DateEncoder(dayOfWeek=(21, 1))

# Season plus holiday flag; holidays can be (month, day) or (year, month, day).
DateEncoder(season=(21, 91.5), holiday=21, holidays=[(12, 25)])
```

The input must be a `datetime.datetime`, not a string. Parse strings before encoding:

```python
timestamp = datetime.datetime.strptime("7/2/10 9:00", "%m/%d/%y %H:%M")
```

## Workflow: reset TM between unrelated sequences

Use `tm.reset()` when a sequence boundary is real: end of an epoch, independent sequence, or a gap that should not be learned as a transition.

```python
for epoch in range(10):
  for active_columns in sequence:
    tm.compute(active_columns, learn=True)
  tm.reset()
```

Do not reset for every row in a continuous stream; that prevents sequence learning.

## Workflow: smoke-check an installed environment

From this sub-skill directory:

```bash
python scripts/algorithm_smoke.py --help
python scripts/algorithm_smoke.py --mode all --records 20 --encoder scalar
python scripts/algorithm_smoke.py --mode all --records 20 --encoder rds
```

The helper imports installed `nupic`, not the original checkout. It fails with explicit messages for Python 3, missing `nupic`, missing `nupic.bindings`, or missing `numpy`.

## When to route away from direct APIs

- A user wants NuPIC three-row CSV headers, `FileRecordStream`, model parameter YAML, or config property validation: use [data and configuration](../../data-and-configuration/).
- A user wants `ModelFactory.create`, `enableInference`, `model.run`, checkpoint load/save, or OPF result dictionaries: use [OPF prediction](../../opf-prediction/).
- A user wants regions, links, sensors, SP/TM/classifier regions, or custom `PyRegion`: use the sibling Network API sub-skill.
- A user wants swarming/search definitions or generated model params: use the sibling Swarming sub-skill, then route generated model execution to OPF.
