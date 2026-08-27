# API reference

This reference records the public names and observed contracts for the MOABB
1.5 development API used by this route. Import public paradigms from
`moabb.paradigms`; import pipeline helpers from `moabb.pipelines` or
`moabb.pipelines.utils`. `BaseParadigm` is available from
`moabb.paradigms.base` for custom array adapters.

## Paradigms

All event-based paradigms expose `is_valid(dataset)`, `used_events(dataset)`,
`make_process_pipelines(dataset, return_epochs=False, return_raws=False,
postprocess_pipeline=None)`, and
`get_data(dataset, subjects=None, return_epochs=False, return_raws=False,
cache_config=None, postprocess_pipeline=None, process_pipelines=None,
additional_metadata=None, n_jobs=1)`. `get_data` returns `(X, labels,
metadata)`, where default `X` is a NumPy array, `return_epochs=True` gives an
MNE `Epochs`, and `return_raws=True` gives raw objects. For a filter bank, the
array branch is 4-D with bands on the last axis; for one filter it is 3-D.

Common arguments have these meanings:

| Argument | Contract |
|---|---|
| `fmin`, `fmax` | High/low cutoff in Hz for single-band convenience classes. |
| `filters` | A sequence of `(low_hz, high_hz)` bands; `None` may request SSVEP bands centered on numeric events. |
| `events` | Event labels to retain; `None` means class selection is delegated to the paradigm. |
| `n_classes` | Maximum/required number of classes, depending on paradigm; verify with `used_events`. |
| `tmin`, `tmax` | Epoch bounds in seconds relative to the dataset interval; `tmax=None` uses the dataset end. |
| `baseline` | `None` or a `(start, end)` baseline tuple passed to MNE epoching. |
| `channels` | Ordered channel names. Missing names fail unless an explicit interpolation policy is enabled on a custom paradigm. |
| `resample` | Target sampling rate in Hz, or `None` to retain the source rate. |
| `scorer` | sklearn-compatible scorer name/callable; otherwise a class-count default is used. |
| `overlap` | Sliding-window overlap percentage in `[0, 100)` for supported imagery processing. |
| `reject_by_annotation` | Reject epochs overlapping MNE annotations beginning with `bad`; defaults to `True`. |

### Selection table

| Class and signature | Use and defaults |
|---|---|
| `LeftRightImagery(fmin=8, fmax=32, events=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, overlap=None, reject_by_annotation=True)` | Exactly `left_hand` and `right_hand`; rejects a non-`None` `events`; default score `roc_auc`. |
| `MotorImagery(n_classes=None, fmin=8, fmax=32, events=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, overlap=None, reject_by_annotation=True)` | N-class imagery. With two classes the default score is `roc_auc`; otherwise `accuracy`. |
| `SpeechImagery(n_classes=None, fmin=1, fmax=100, events=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, overlap=None, reject_by_annotation=True)` | Imagined speech under the imagery dataset tag; use only when event/task evidence supports it. |
| `FilterBankMotorImagery(n_classes=2, filters=((8,12),(12,16),(16,20),(20,24),(24,28),(28,32)), events=None, ...)` | N-class imagery with one processing branch per band. |
| `FilterBankLeftRightImagery(filters=((8,12),(12,16),(16,20),(20,24),(24,28),(28,32)), events=None, ...)` | Left/right filter bank; fixed left/right events. |
| `P300(fmin=1, fmax=24, events=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, ignore_relabelling=False, scorer=None, reject_by_annotation=True)` | Target/non-target ERP; `events=None` becomes `['Target', 'NonTarget']`; default score `roc_auc`. |
| `SSVEP(fmin=7, fmax=45, filters=None, events=None, n_classes=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, reject_by_annotation=True)` | One broad band; `filters` must remain `None`; two-class default score `roc_auc`, otherwise `accuracy`. |
| `FilterBankSSVEP(filters=None, events=None, n_classes=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, reject_by_annotation=True)` | One band centered at each numeric event when `filters=None`; otherwise uses the supplied bank. |
| `CVEP(fmin=1.0, fmax=45.0, filters=None, events=None, n_classes=None, tmin=0.0, tmax=None, baseline=None, channels=None, resample=None, scorer=None, reject_by_annotation=True)` | Single-band c-VEP; `filters` must remain `None`; event labels conventionally encode intensity. |
| `FilterBankCVEP(filters=((1,45),(12,45),(30,45)), events=None, n_classes=None, ...)` | c-VEP filter bank. |
| `FixedIntervalWindowsProcessing(fmin=7, fmax=45, baseline=None, channels=None, resample=None, length=5.0, stride=10.0, start_offset=0.0, stop_offset=None, marker=-1)` | Ignores dataset events and creates fixed windows labeled `Window`; `filters` is required in the base class. |
| `FilterBankFixedIntervalWindowsProcessing(filters=((8,12),(12,16),(16,20),(20,24),(24,28),(28,32)), baseline=None, channels=None, resample=None, length=5.0, stride=10.0, start_offset=0.0, stop_offset=None, marker=-1)` | Fixed windows with multiple filter branches. |

`BaseParadigm(filters, events=None, tmin=0.0, tmax=None, baseline=None,
channels=None, resample=None, overlap=None, scorer=None,
reject_by_annotation=True)` is the extension point for an X/y adapter. A
concrete subclass must implement `datasets`, `is_valid`, `used_events`, and the
`scoring` property. A custom adapter should return stable subject/session/run
metadata and must not pretend that an arbitrary X/y dataset has continuous raw
semantics.

## Features and filter banks

| Name and signature | Input/output contract |
|---|---|
| `LogVariance()` | `transform(X)` requires `X.ndim == 3`; returns `log(var(X, axis=-1))`, shape `(trials, channels)`. |
| `FM(freq=128)` | Hilbert phase-derived instantaneous-frequency features; `freq` scales the result. |
| `ExtendedSSVEPSignal()` | Converts `(trials, channels, times, bands)` to `(trials, channels*bands, times)`. |
| `FilterBank(estimator, flatten=True)` | `fit/transform` require 4-D input. Clones and fits the estimator per last-axis band; each inner result must be 2-D. `flatten=True` concatenates columns; `False` stacks along axis 2. |
| `filterbank(X, sfreq, idx_fb, peaks)` | Functional SSVEP band decomposition for 2-D single-trial or 3-D trial arrays; `idx_fb` must be less than `len(peaks)`. |

Use `sklearn.pipeline.make_pipeline` or `Pipeline` around these objects. Do
not place a supervised transformer outside the CV/evaluation split.

## SSVEP classifiers

All names below are exported by `moabb.pipelines` and are sklearn estimators.
Their fitting/prediction API is `fit(X, y)`, `predict(X)`, and usually
`predict_proba(X)`. The CCA-style implementations validate direct `X` input as
an MNE `BaseEpochs` object and preserve the labels supplied in `y`.

| Class and defaults | Important knobs |
|---|---|
| `SSVEP_CCA(n_harmonics=3, freq_map=None)` | Sinusoidal reference CCA. `freq_map` maps class labels to physical Hz when inference is ambiguous. |
| `SSVEP_MsetCCA(n_filters=1, n_jobs=1)` | Learns references from repeated training trials; accepts MNE epochs. |
| `SSVEP_itCCA()` | Uses individual class-average templates. |
| `SSVEP_eCCA(n_harmonics=3, freq_map=None)` | Fuses sinusoidal and individual-template correlations; same frequency-map rule as CCA. |
| `SSVEP_TRCA(n_fbands=5, is_ensemble=True, method='original', estimator='scm')` | Data-driven filter bank; `method` is `original`, `riemann`, or `logeuclid`; covariance estimator can be `scm`, `lwf`, `oas`, or `schaefer`. |
| `SSVEP_TRCA_R(n_fbands=5, n_harmonics=3, is_ensemble=True, method='original', estimator='scm')` | Regularized TRCA with reference projection. |
| `SSVEP_SSCOR(n_fbands=5, is_ensemble=True, estimator='scm')` | Sum-of-squared-correlations filter bank. |
| `SSVEP_TDCA(n_fbands=5, n_components=1, n_delay=6, is_ensemble=True)` | Temporal-delay augmentation plus discriminant components. |

Use string frequency events such as `"13"`, `"17"`, `"21"` when the dataset
uses numeric stimulus names. If labels were converted to `0, 1, 2`, CCA/eCCA
can reject them as ordinal event codes; pass `freq_map` with the true Hz.

## Public imports and errors

```python
from moabb.paradigms import LeftRightImagery, P300, SSVEP, FilterBankSSVEP
from moabb.pipelines import LogVariance, FilterBank, SSVEP_CCA
from moabb.pipelines.utils import create_pipeline_from_config
```

Expected validation errors include `ValueError` for invalid epoch bounds,
filter-bank dimensionality, unsupported convenience arguments, too few events,
or missing frequency mappings; `AssertionError` can be raised by dataset
validity checks. Check the exception text and inspect `dataset.event_id` before
loosening a selection.
