---
name: paradigms-and-pipelines
description: "Choose a MOABB task paradigm and build a verified preprocessing,
  feature, classifier, filter-bank, or YAML pipeline for EEG decoding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Paradigms and pipelines

Use this route when a task must turn EEG recordings or already-epoched arrays
into sklearn-compatible inputs and predictions. Start by identifying the task
family, class/event semantics, and whether the consumer expects a NumPy array,
MNE `Epochs`, or a filter-bank tensor. Follow the shared installation and
import policy in the [MOABB root skill](../../SKILL.md). Route dataset
selection, downloads, subject/session discovery, and cache configuration to
[dataset-management](../dataset-management/SKILL.md). Route train/test or
cross-subject protocol choices to
[evaluations-and-benchmarks](../evaluations-and-benchmarks/SKILL.md).

## Fast routing

| Task evidence | Paradigm | Typical output and default score |
|---|---|---|
| Left/right or N-class imagined movement | `LeftRightImagery` or `MotorImagery` | 3-D array `(trials, channels, times)`; ROC-AUC for two classes, otherwise accuracy |
| Imagined words, phonemes, or speech | `SpeechImagery` | Same imagery machinery, broadband default `1–100 Hz`; validate the dataset's event labels |
| Target versus non-target ERP | `P300` | 3-D array or MNE `Epochs`; ROC-AUC |
| Frequency-tagged visual stimulation | `SSVEP` or `FilterBankSSVEP` | 3-D or 4-D filter-bank data; accuracy except two-class ROC-AUC |
| Binary/multilevel coded visual stimulation | `CVEP` or `FilterBankCVEP` | 3-D/4-D c-VEP epochs; accuracy except two-class ROC-AUC |
| No event markers; fixed windows | `FixedIntervalWindowsProcessing` | Windows labeled `"Window"`; specify `resample` when sample-count properties are needed |

When the request is underspecified, ask whether the signal is an ERP response,
frequency-tagged stimulation, or imagery before selecting a class. Do not infer
P300, SSVEP, or motor imagery from an arbitrary binary label vector.

## Minimal procedure

1. Confirm the dataset's `paradigm`, `event_id`, interval, channel names, and
   sampling rate. Use dataset-management for acquisition; this route only
   consumes a dataset object or a prepared array.
2. Choose event labels and class count. `used_events(dataset)` is the final
   check; an absent event or too-small class set is a configuration error, not
   a reason to silently use all events.
3. Set `fmin/fmax` or `filters`, `tmin/tmax`, optional `baseline`, `channels`,
   `resample`, `overlap`, and `reject_by_annotation`. `tmax` is relative to the
   dataset task interval; `tmax <= tmin` raises `ValueError`.
4. Call `paradigm.get_data(dataset, subjects=[...])`. The result is
   `(X, labels, metadata)`. Default `X` is a 3-D NumPy array; use
   `return_epochs=True` for an MNE `Epochs` object or `return_raws=True` for
   raw objects. `return_epochs` and `return_raws` are mutually exclusive.
5. Fit the classifier *inside* a sklearn `Pipeline` and pass the pipeline to
   the evaluation route. Never fit a scaler, CSP, covariance, template, or
   classifier on all trials before a split.
6. Run the bundled deterministic checks:
   `python scripts/smoke_xy_dataset.py --tiny-fixture` and
   `python scripts/smoke_preprocessing.py --tiny-fixture`.

For exact constructor defaults and output contracts, use
[api-reference.md](references/api-reference.md). For end-to-end choices use
[workflows.md](references/workflows.md); for YAML use
[pipeline-configs.md](references/pipeline-configs.md); for failures use
[troubleshooting.md](references/troubleshooting.md).

Bundled offline helpers are [smoke_xy_dataset.py](scripts/smoke_xy_dataset.py)
and [smoke_preprocessing.py](scripts/smoke_preprocessing.py). They are safe to
run from any working directory and never acquire a dataset.

## Configuration patterns

### Paradigm preprocessing

```python
from moabb.paradigms import LeftRightImagery

paradigm = LeftRightImagery(
    fmin=8, fmax=35, tmin=0.5, tmax=3.5,
    channels=["C3", "Cz", "C4"], resample=200.0,
)
X, y, meta = paradigm.get_data(dataset, subjects=[1])
```

Use `FilterBankLeftRightImagery(filters=[...])` when the pipeline consumes a
filter bank. A filter-bank paradigm returns `(trials, channels, times, bands)`
for array output. `FilterBank` then applies a cloned estimator independently to
each last-axis band and concatenates its 2-D features by default.

### sklearn composition

For a 3-D array, `LogVariance()` produces a 2-D `(trials, channels)` feature
matrix and can precede LDA or another sklearn classifier. CSP, covariance plus
tangent-space, and MNE decoders are also pipeline steps. For a 4-D filter bank,
use `FilterBank(estimator=...)`; the inner estimator must return 2-D features.
`ExtendedSSVEPSignal()` converts SSVEP filter-bank data to
`(trials, channels * bands, times)` for covariance methods.

The SSVEP CCA-family (`SSVEP_CCA`, `SSVEP_MsetCCA`, `SSVEP_itCCA`,
`SSVEP_eCCA`) consumes MNE `Epochs` when fitted directly. Preserve string
frequency labels or pass an explicit `freq_map` when labels have been encoded
as ordinal integers. TRCA, TRCA-R, SSCOR, and TDCA are filter-bank SSVEP
classifiers; reduce `n_fbands`, `n_delay`, or estimator complexity for a tiny
smoke test, not for an unreviewed scientific comparison.

### YAML boundary

`create_pipeline_from_config(config)` accepts a **list of component mappings**,
not a file path. Each mapping has `name`, `from`, and optional `parameters`.
Load a trusted local YAML file with a safe YAML loader, validate its shape, and
pass `config["pipeline"]`. Class imports are dynamic, so do not execute
untrusted configuration. A config's `paradigms` and `name` metadata are used by
benchmark tooling; they do not alter the sklearn pipeline itself.

## Boundaries and safety

- Real datasets can require network access, provider credentials, large disk,
  and long preprocessing. The bundled scripts never download data.
- `mne`, `scikit-learn`, and NumPy are core runtime assumptions. `pyriemann`,
  `scipy`, and YAML support are needed by selected pipelines; deep-learning
  pipelines are outside this route's selected core and are not restored by
  importing MOABB.
- Keep channel order explicit when comparing datasets. Use an intersection of
  channels or a deliberate interpolation policy; do not silently accept an
  empty or reordered channel selection.
- Inspect `X.ndim`, `X.shape`, `type(X)`, `len(y)`, and `meta.shape` before
  fitting. A 3-D epoch array is not a 2-D feature matrix until a transformer
  makes that conversion.
- `P300` uses its event relabeling behavior unless
  `ignore_relabelling=True`; preserve the target/non-target semantics when
  interpreting ROC-AUC.
- SSVEP frequency inference requires physical frequencies. Encoded labels
  such as `0, 1, 2` can be ambiguous; use `freq_map={0: 13.0, 1: 17.0, 2: 21.0}`
  when necessary.

## Verification handoff

The bundled scripts are safe adapted replacements for the X/y and preprocessing
recipes and are the preferred offline checks for this runtime graph. Separate
repository verification may add focused CPU tests, but those tests are not a
runtime dependency of this skill. See the references for expected observations
and recovery actions; do not treat a successful import alone as evidence that a
paradigm matches a dataset.
