# MNE-Python Package Map

Read this for a quick map of public MNE-Python concepts and where to route work.

## Main object flow

```text
files / arrays -> Info + Raw -> events/annotations -> Epochs -> Evoked
                     |             |                 |        |
                     |             |                 |        +-> visualization/report
                     |             |                 +----------> PSD/TFR/stats/decoding
                     |             +----------------------------> preprocessing/artifacts
                     +------------------------------------------> source modeling inputs

Evoked/Epochs + covariance + forward -> inverse/beamformer -> SourceEstimate
SourceEstimate -> labels/morphing/statistics/visualization
```

## Public API roots

| Area | Important modules/classes/functions | Route |
| --- | --- | --- |
| I/O and containers | `mne.io`, `Raw`, `BaseRaw`, `RawArray`, `create_info`, `Info`, `read_raw*`, `concatenate_raws` | `io-raw-data` |
| Events/epochs/evoked | `find_events`, `events_from_annotations`, `Epochs`, `EpochsArray`, `Evoked`, `EvokedArray`, `combine_evoked`, `grand_average` | `preprocessing-epochs-evoked` |
| Preprocessing | `mne.preprocessing`, filtering, references, bads/interpolation, ICA, SSP, EOG/ECG/muscle/fNIRS/eye-tracking helpers | `preprocessing-epochs-evoked` |
| Visualization/report | `mne.viz`, object `.plot()` methods, `plot_topomap`, `Report`, browser/3D backends | `visualization-reporting` |
| Source modeling | `setup_source_space`, BEM, transforms, `make_forward_solution`, minimum norm, beamformer, source estimates, labels/morphing | `source-modeling-inverse` |
| Analysis methods | `mne.time_frequency`, `mne.stats`, `mne.decoding`, `mne.simulation`, spectra/TFR/CSD/statistics/ML/simulation | `timefreq-stats-decoding-simulation` |
| CLI/datasets/config | console script `mne`, `mne.commands`, `mne.datasets`, `get_config`, `set_config`, `sys_info`, logging | `cli-datasets-config` |
| Repository maintenance | lazy public API stubs, docs, tests, changelog fragments, contributor policy | `repo-development` |

## Architecture facts that affect generated code

- MNE-Python exposes a lazy public API. Stub files such as `mne/__init__.pyi`
  and subpackage `__init__.pyi` files are the public API source of truth.
- Neuromag/FIF internals live in `mne._fiff`; `mne.io._fiff_wrap` re-exports
  selected compatibility symbols.
- `Raw`, `Epochs`, and `Evoked` share behavior through mixins; methods often
  mutate in place and return `self`.
- Shared docstring text comes from `mne.utils.docs` and `@fill_doc`.
- User-facing changes need towncrier fragments under `doc/changes/dev/` rather
  than editing aggregated changelogs directly.

## Useful object checks

```python
print(type(obj).__name__)
print(obj.info['sfreq'])
print(obj.info['ch_names'][:5])
print(obj.info.get('bads', []))
```

For epochs/evoked/source data, also inspect:

```python
print(getattr(obj, 'events', None))
print(getattr(obj, 'event_id', None))
print(getattr(obj, 'nave', None))
print(getattr(obj, 'data', None).shape if hasattr(obj, 'data') else None)
```

Use these checks before choosing a downstream route.
