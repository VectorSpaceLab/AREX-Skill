# MOABB API overview

Read this when a task crosses more than one route or when a public import needs
orientation. The names and signatures below were checked against the inspected
MOABB 1.5 development package used to build this graph; consult the nearest
sub-skill reference for full parameters.

## Core object flow

```text
Dataset object -> Paradigm.get_data() -> (X, labels, metadata)
             -> sklearn Pipeline -> Evaluation.process()
             -> pandas DataFrame / Results HDF5 store
             -> analysis, statistics, plots, or report folder
```

- `moabb.datasets`: catalog classes, `FakeDataset`, dataset metadata, data
  paths, `BaseDataset`, and local/BIDS adapters.
- `moabb.paradigms`: `MotorImagery`, `LeftRightImagery`, `SpeechImagery`,
  `P300`, `SSVEP`, `CVEP`, fixed-window processors, and `BaseParadigm`.
- `moabb.pipelines`: sklearn-compatible features (`LogVariance`, `FM`),
  `FilterBank`, SSVEP CCA/TRCA/eCCA/TDCA families, and
  `create_pipeline_from_config`.
- `moabb.evaluations`: `WithinSessionEvaluation`, `WithinSubjectEvaluation`,
  `CrossSessionEvaluation`, `CrossSubjectEvaluation`, and protocol splitters.
- `moabb.analysis`: `Results`, `analyze`, chance-level helpers, statistical
  comparison, plotting, style, and timeline APIs.

## Verified anchors

| API | Signature or contract | Route |
|---|---|---|
| `FakeDataset` | `FakeDataset(event_list=(...), n_sessions=2, n_runs=2, n_subjects=10, code="FakeDataset", paradigm="imagery", channels=(...), seed=None, sfreq=128, duration=120, n_events=60, ...)` | dataset-management |
| `dataset_search` | `dataset_search(paradigm=None, multi_session=False, events=None, has_all_events=False, interval=None, min_subjects=1, channels=())` | dataset-management |
| `MotorImagery` | `MotorImagery(n_classes=None, fmin=8, fmax=32, events=None, tmin=0.0, tmax=None, ...)` | paradigms-and-pipelines |
| `P300` | `P300(fmin=1, fmax=24, events=None, tmin=0.0, tmax=None, ..., ignore_relabelling=False, ...)` | paradigms-and-pipelines |
| `SSVEP` | `SSVEP(fmin=7, fmax=45, filters=None, events=None, n_classes=None, tmin=0.0, tmax=None, ...)` | paradigms-and-pipelines |
| `WithinSessionEvaluation` | Evaluation with `paradigm`, `datasets`, `random_state`, `n_jobs`, `overwrite`, `suffix`, `hdf5_path`, `n_splits`, and related cache/model options | evaluations-and-benchmarks |
| `Results` | `Results(evaluation_class, paradigm_class, suffix="", overwrite=False, hdf5_path=None, ...)`; call `to_dataframe()` before analysis | analysis-and-visualization |
| `adjusted_chance_level` | `adjusted_chance_level(n_classes, n_trials, alpha=0.05)` | analysis-and-visualization |

## Cross-route invariants

- A dataset's `paradigm` and `event_id` must be compatible with the selected
  paradigm. Validate with `is_valid()`/`used_events()` rather than guessing
  from integer event codes.
- Default paradigm output is a 3-D array `(trials, channels, times)`. A filter
  bank adds a final band axis. Feature transformers such as `LogVariance` turn
  trials into 2-D rows for sklearn estimators.
- Evaluation splitters define the scientific claim. Use group-aware subject
  splits for unseen-subject claims and session-aware splits for future-session
  claims; random trial CV is not a substitute.
- Result analysis needs stable `dataset`, `pipeline`, `subject`, `session`, and
  numeric `score` columns. Chance calculations additionally need valid
  `samples_test` and `n_classes`.
