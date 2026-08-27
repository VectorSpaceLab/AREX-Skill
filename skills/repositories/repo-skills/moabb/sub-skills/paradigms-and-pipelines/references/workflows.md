# Workflows

These workflows are intentionally small enough to inspect before a real
benchmark. They assume a prepared MOABB dataset object; acquisition and cache
settings belong to the dataset-management route. The examples below avoid
network access and use only public imports.

## 1. Resolve an underspecified task

Ask for the evidence that distinguishes the three common families:

1. **P300/ERP**: an event-locked response to target/non-target stimuli. Choose
   `P300`, usually with `events=["Target", "NonTarget"]` or its defaults,
   `fmin=1`, `fmax=24`, and an epoch window appropriate to the stimulus.
2. **SSVEP**: periodic visual stimulation with known stimulus frequencies.
   Choose `SSVEP` for one broad band or `FilterBankSSVEP` for a band per
   numeric stimulus event. Preserve event labels such as `"13"`, `"17"`, and
   `"21"` so frequency-aware estimators can infer physical frequencies.
3. **Motor imagery**: imagined movement classes. Choose
   `LeftRightImagery` for the canonical `left_hand`/`right_hand` pair, or
   `MotorImagery(n_classes=...)` for a selected N-class imagery task. Use
   `SpeechImagery` only when the task is explicitly imagined speech.

If the only supplied information is “two-class EEG classification”, stop and
request task/event semantics. A classifier choice cannot repair a wrong
paradigm.

## 2. Extract array epochs

```python
from moabb.paradigms import LeftRightImagery

paradigm = LeftRightImagery(
    fmin=8, fmax=35,
    tmin=0.5, tmax=3.5,
    channels=["C3", "Cz", "C4"],
    resample=200.0,
)

# Dataset acquisition, subject validation, and cache policy happen elsewhere.
X, y, metadata = paradigm.get_data(dataset, subjects=[1], n_jobs=1)
assert X.ndim == 3
assert X.shape[0] == len(y) == len(metadata)
```

`get_data` creates a fixed processing pipeline: raw annotation/event handling,
filtering, event extraction, MNE epoching, optional cropping/resampling, and
conversion to an array. A `tmin`/`tmax` window is relative to the dataset task
interval. `baseline` is shifted by that interval before MNE epoching. MNE
annotations beginning with `bad` are rejected by default.

When comparing several datasets, call `paradigm.match_all(datasets)` only after
checking that the datasets are intentionally comparable. It selects common
channels (or a union with interpolation when explicitly requested) and changes
`resample`; inspect the resulting `paradigm.channels` and `paradigm.resample`.

## 3. Use MNE Epochs in a pipeline

Use `return_epochs=True` when an estimator requires MNE metadata or MNE-aware
input. The returned object is an `mne.Epochs` with labels and metadata aligned
by trial. A simple sklearn-compatible adapter can be written with
`mne.decoding.Vectorizer`, or a custom transformer can call `X.get_data()` and
reshape to `(trials, features)`.

```python
from mne.decoding import Vectorizer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from moabb.paradigms import P300

paradigm = P300(resample=128)
pipeline = make_pipeline(Vectorizer(), LinearDiscriminantAnalysis())
# Pass pipeline to the evaluation route with return_epochs=True.
```

For P300, keep target/non-target mapping and use ROC-AUC. For a CCA-style SSVEP
classifier, do not insert `Vectorizer`: `SSVEP_CCA`, `SSVEP_MsetCCA`,
`SSVEP_itCCA`, and `SSVEP_eCCA` expect MNE `BaseEpochs` when fitted directly.

## 4. Array pipeline and shape contract

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from moabb.pipelines import LogVariance

pipeline = make_pipeline(LogVariance(), LinearDiscriminantAnalysis())
# X: (n_trials, n_channels, n_times)
pipeline.fit(X, y)
predicted = pipeline.predict(X)
```

`LogVariance` is a deterministic feature transformer and returns
`(n_trials, n_channels)`. It is appropriate for a quick smoke or as one
baseline, not a universal best model. A raw 3-D array sent directly to LDA or
SVC is a shape error; put an explicit transformer in the pipeline.

For MNE/pyRiemann alternatives, keep the whole chain inside the pipeline:

```python
from pyriemann.estimation import Covariances
from pyriemann.tangentspace import TangentSpace
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

pipeline = make_pipeline(
    Covariances(estimator="oas"),
    TangentSpace(metric="riemann"),
    LogisticRegression(max_iter=1000),
)
```

Fit-dependent covariance, tangent-space, CSP, scaling, template, and feature
selection steps must be fitted anew inside each evaluation split.

## 5. Filter-bank motor imagery

A filter-bank paradigm creates one processing branch per band and returns a
last-axis band dimension for array output. Pair it with `FilterBank` when the
same estimator is to be fitted independently per band:

```python
from mne.decoding import CSP
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from moabb.paradigms import FilterBankLeftRightImagery
from moabb.pipelines import FilterBank

paradigm = FilterBankLeftRightImagery(
    filters=[[8, 24], [16, 32], [24, 40]],
    channels=["C3", "Cz", "C4"],
)
pipeline = make_pipeline(
    FilterBank(CSP(n_components=4, reg="oas")),
    LinearDiscriminantAnalysis(),
)
```

The inner estimator must output a 2-D feature matrix. With `flatten=True`,
features from all bands are concatenated. If the estimator returns an array
with three or more dimensions, `FilterBank.transform` raises an assertion;
add a vectorizer/feature transformer inside the inner estimator or use a
classifier designed for the resulting representation.

## 6. SSVEP pipeline choices

- Start with `SSVEP(fmin=10, fmax=42, n_classes=3)` and
  `make_pipeline(SSVEP_CCA(n_harmonics=3))` for a transparent reference-based
  baseline.
- Use `FilterBankSSVEP(filters=None, n_classes=3)` when events are numeric
  frequencies and narrow event-centered bands are wanted.
- Use `SSVEP_TRCA(n_fbands=3)` or `SSVEP_TDCA(n_fbands=3, n_delay=3)` only when
  enough repeated training trials exist; the estimators learn templates or
  spatial filters and should remain inside the evaluation pipeline.
- For an extended covariance route, use `ExtendedSSVEPSignal()` before
  `Covariances`, `TangentSpace`, and a classifier. The first transformer is
  required because filter-bank data is 4-D while covariance estimators expect
  trial-wise channel-by-time arrays.

When the evaluation encodes labels to ordinal integers, CCA/eCCA may reject
frequency inference. Supply `freq_map` with the true Hz, not the event codes.
Record that mapping in the experiment configuration.

## 7. Fixed windows and preprocessing surgery

Use `FixedIntervalWindowsProcessing` when event markers should be ignored. Its
`length`, `stride`, `start_offset`, and `stop_offset` are seconds. If asking for
sample-count properties such as `length_samples`, `resample` must be set. The
created event label is `"Window"` unless a different `marker` is chosen.

For a custom raw-stage operation, inspect the generated processing pipeline and
insert a fixed transformer at the raw stage. The operation must be deterministic
and must not fit on held-out data. A postprocess pipeline supplied to
`get_data` is also fixed: MOABB will call its transform path without fitting it.
For learned operations, use the evaluation's sklearn pipeline instead.

## 8. Offline X/y data

Already-epoched data has shape `(trials, channels, times)` and labels of length
`trials`. It can be classified directly with an sklearn pipeline such as
`LogVariance` plus LDA. A custom `BaseParadigm` adapter is appropriate only when
MOABB evaluation metadata (subject/session/run) and split semantics are needed;
implement `is_valid`, `used_events`, `datasets`, `scoring`, and a stable
`get_data` contract. Do not wrap arbitrary arrays as continuous raw data merely
to make a dataset loader appear compatible.

The bundled `scripts/smoke_xy_dataset.py` demonstrates the smallest safe
array contract. It does not download data or write results.
