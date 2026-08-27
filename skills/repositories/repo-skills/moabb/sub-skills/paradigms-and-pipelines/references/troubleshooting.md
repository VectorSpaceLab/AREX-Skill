# Troubleshooting

Start every diagnosis by printing the object type, shape, label set, metadata
shape, paradigm scoring, and selected events. Keep the check inside the current
training fold when it involves fitted objects.

```python
print(type(X), getattr(X, "shape", None), len(y), metadata.shape)
print(paradigm.scoring, paradigm.used_events(dataset))
```

## Decision matrix

| Symptom | Likely cause | Check | Recovery |
|---|---|---|---|
| `ModuleNotFoundError: moabb` | MOABB is not installed in the active interpreter. | `python -c "import sys, moabb; print(sys.executable, moabb.__version__)"` | Install the project-supported MOABB release in the active environment, then repeat the import. Avoid relying on a source checkout being on `PYTHONPATH`. |
| `ImportError` for `pyriemann`, YAML, MNE decoder, or another component | The chosen optional recipe is not installed. | Import each component named in the pipeline config. | Install the matching optional dependency or select a documented base recipe. Do not change the scientific method silently. |
| Importing a historical Keras/EEGNet class from `moabb.pipelines` raises `AttributeError` | TensorFlow deep-learning models are no longer part of MOABB's pipeline package. | Inspect the exception and selected config class. | Route deep learning to a separately installed/supported framework; deep-learning benchmarking is intentionally omitted from this core route. |
| `Dataset ... is not valid for paradigm` | Dataset task family or required events do not match the paradigm. | Inspect `dataset.paradigm`, `dataset.event_id`, `paradigm.events`, and `paradigm.is_valid(dataset)`. | Choose the correct task family or an explicitly supported event subset. Do not suppress the validity check. |
| `KeyError` for an event such as `left_hand`, `Target`, or `NonTarget` | Event names differ from the paradigm's required labels. | Print the exact keys and value types in `dataset.event_id`. | Use the correct paradigm, remap labels in the dataset adapter with documented semantics, or pass supported `events`. Never guess by integer code alone. |
| “not enough events/freqs” or `n_classes exceeds number of events` | `n_classes` and selected events disagree. | Compare `n_classes`, requested `events`, and `used_events(dataset)`. | Reduce `n_classes` only if scientifically intended, or provide a complete event list/dataset. |
| `tmax must be greater than tmin` | Invalid epoch interval. | Print `tmin`, `tmax`, and `dataset.interval`. | Make `tmax > tmin`; remember the paradigm bounds are offsets relative to the dataset task interval. |
| No events found / zero epochs | Triggers, annotations, selected codes, or interval/window do not overlap. | Inspect raw stim channels/annotations, `event_id`, extracted event count, epoch window, and bad annotations. | Correct event mapping/window. Use `reject_by_annotation=False` only after reviewing why marked-bad epochs should be retained. |
| MNE baseline or epoch-bound error | Baseline lies outside loaded data, or the requested window exceeds recordings. | Compare absolute dataset interval, shifted baseline, and raw duration. | Choose a valid baseline/window and rerun the preprocessing smoke before an evaluation. |
| Channel selection fails or channel count/order is wrong | Requested names are absent, differ in case/montage, or datasets have incompatible channel sets. | Compare `paradigm.channels` with each raw's `info['ch_names']`. | Use an explicit ordered intersection, or deliberately enable a documented interpolation/union policy. Route dataset metadata issues to dataset-management. |
| Output sample count differs across datasets | Source sampling rates/windows differ or MNE rounding differs. | Inspect `X.shape[-1]`, `info['sfreq']`, `tmin/tmax`, and `resample`. | Set a shared resampling/window policy; review `match_all` output rather than assuming identical shapes. |
| sklearn says “Found array with dim 3” or expects at most 2-D | A classifier received raw epoch arrays instead of features. | Print `X.ndim` before each conceptual stage; inspect pipeline steps. | Insert `LogVariance`, CSP plus vectorization, covariance/tangent space, or another validated 3-D-to-2-D transformer inside the pipeline. |
| `LogVariance`: `X must be 3-dimensional` | Input was already flattened, is an MNE object, or is a 4-D filter bank. | Print `type(X)` and `X.shape`. | For MNE, call a proper MNE-to-array/vectorizer step; for 4-D, use `FilterBank(LogVariance())` or `ExtendedSSVEPSignal` as appropriate; remove accidental pre-flattening. |
| `FilterBank`: `X must be 4-dimensional` | A filter-bank transformer received a single-band 3-D array. | Check chosen paradigm and last-axis band count. | Pair `FilterBank` with a `FilterBank*` paradigm, or remove `FilterBank` and use the estimator directly on 3-D data. |
| FilterBank says each band must return 2-D | The inner estimator leaves channel/time dimensions. | Test `inner.fit_transform(X[..., 0], y).shape`. | Put a feature/vectorizer step inside the inner estimator so each band yields `(trials, features)`. |
| `ExtendedSSVEPSignal` transpose/shape error | Input is not `(trials, channels, times, bands)`. | Print rank and confirm the paradigm is `FilterBankSSVEP`. | Use a filter-bank SSVEP output or remove the extension transformer for a single-band route. |
| CCA/eCCA cannot infer physical stimulus frequencies | Labels/events are ordinal codes rather than Hz. | Compare `y`, `X.event_id`, and the actual stimulus-frequency metadata. | Pass `freq_map={class_label: frequency_hz}` and preserve it in config. Do not map codes to Hz without dataset evidence. |
| CCA-style classifier says `X should be an MNE Epochs object` | Default array output was supplied. | Check `isinstance(X, mne.BaseEpochs)` and evaluation `return_epochs`. | Request/retain MNE epochs for that pipeline; do not vectorize before the classifier. |
| TRCA/TDCA filter design fails on a tiny fixture | Too many bands/harmonics for sampling rate, signal duration, or stimulus range. | Inspect sampling rate, Nyquist limit, times, frequency peaks, `n_fbands`, and `n_delay`. | For a smoke test reduce only the fixture complexity; for an experiment, redesign parameters with method evidence and report the change. |
| YAML `KeyError: 'from'/'name'`, class resolution error, or duplicate pipeline name | Invalid schema/module/class or repeated label. | Validate each component mapping; import module and retrieve class manually; inspect benchmark names. | Correct schema/import path and assign unique names per paradigm. See [pipeline-configs.md](pipeline-configs.md). |
| YAML loads but pipeline fails at fit | Metadata compatibility is not runtime shape validation. | Inspect `pipeline`, `pipeline.get_params()`, input type/rank, and final estimator API. | Validate with the bundled synthetic shape checks, then with one approved dataset subject before scaling. |
| Pipeline works in a notebook but not the evaluator | A preprocessing step was fitted globally, input mode differs, or custom fixed processing returns the wrong stage. | Reconstruct a clean pipeline and compare array versus `return_epochs=True`; inspect the process pipeline's final step type. | Move all learned transforms into the estimator pipeline and align `return_epochs`/`return_raws` with the processing output. |
| Unexpectedly high scores | Leakage from fitting before splits, duplicate trials/windows, or subject/session leakage. | Confirm every learned object is inside the evaluation pipeline and inspect split/group metadata. | Rebuild inside the evaluation route, preserve groups, and invalidate contaminated results. Route protocol repair to evaluations-and-benchmarks. |
| Real-data command hangs, downloads, or consumes large disk | Dataset acquisition/network/cache work was triggered. | Inspect dataset path/cache status and provider requirements before `get_data`. | Stop, obtain data/network approval, and route acquisition to dataset-management. The bundled scripts are offline and must remain so. |
| Parallel workers fail or memory spikes | Large Epochs/filter-bank arrays are copied across jobs. | Re-run the same tiny case with `n_jobs=1`; inspect array sizes and process backend. | Validate sequentially, reduce subjects/bands for diagnosis, then select bounded parallelism in the evaluation route. |
| Config works only from one current directory | Relative paths point to a checkout or notebook location. | Run from a temporary directory and list all opened config/data paths. | Resolve user-provided paths explicitly. Bundled smoke scripts are arbitrary-CWD safe and use no checkout resources. |

## Repairing the difficult 3-D mismatch

A common failure is:

```python
# Wrong: LinearDiscriminantAnalysis expects 2-D features.
classifier.fit(X_3d, y)
```

Use a supervised-safe composition:

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from moabb.pipelines import LogVariance

pipeline = make_pipeline(LogVariance(), LinearDiscriminantAnalysis())
pipeline.fit(X_3d, y)
```

For 4-D filter-bank data:

```python
from moabb.pipelines import FilterBank, LogVariance
pipeline = make_pipeline(
    FilterBank(LogVariance()),
    LinearDiscriminantAnalysis(),
)
```

Both feature transforms are inside the pipeline, so an evaluation can clone
and fit them per split. Confirm the intermediate feature matrix is 2-D and that
all rows still align with `y`.

## CLI and script checks

The bundled helpers expose only local, synthetic fixtures:

```bash
python scripts/smoke_xy_dataset.py --help
python scripts/smoke_xy_dataset.py --tiny-fixture
python scripts/smoke_preprocessing.py --help
python scripts/smoke_preprocessing.py --tiny-fixture
```

A nonzero exit means the printed assertion or import error must be repaired.
They do not test network access, dataset downloads, hardware acceleration,
benchmark splitting, or scientific accuracy on real EEG.
