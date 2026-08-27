# Dataset Loader Reference

## Purpose

Read this when selecting a built-in `torch_geometric_temporal.dataset` loader or checking which call downloads data, which `get_dataset` arguments shape the returned snapshots, and whether a loader also has index-batching support.

The safest metadata check is the bundled helper: `python scripts/list_dataset_loaders.py --format text`. It imports loader classes and prints signatures without constructing loaders.

## Side-effect rule

For these loaders, importing `torch_geometric_temporal.dataset` is intended to be safe, but constructing many loader classes is not side-effect-free. A large part of the public loader catalog downloads or validates remote data in `__init__`. `get_dataset` usually transforms already loaded arrays into a temporal signal.

## Public loader catalog

| Loader class | Constructor args | `get_dataset` args | Return signal type | Constructor data/cache/network notes | Index support note |
| --- | --- | --- | --- | --- | --- |
| `AdvectionDiffusionDatasetLoader` | none | `lags=4` | `StaticGraphTemporalSignal` | Downloads a remote NumPy signal and PyTorch adjacency tensor in `__init__`; no local cache argument. Synthetic PDE static graph. | No `get_index_dataset`. |
| `ChickenpoxDatasetLoader` | `index=False` | `lags=4` | `StaticGraphTemporalSignal` | Downloads `chickenpox.json` from a web URL in `__init__`; no local cache argument. | Has `get_index_dataset(lags=4, batch_size=4, shuffle=False, allGPU=-1, ratio=(0.7, 0.1, 0.2), dask_batching=False)`. Use `index=True` and route mechanics to index-batching. |
| `EnglandCovidDatasetLoader` | none | `lags=8` | `DynamicGraphTemporalSignal` | Downloads `england_covid.json` in `__init__`; graph edges and weights vary by time. | No `get_index_dataset`. |
| `METRLADatasetLoader` | `raw_data_dir=<cwd>/data`, `index=False` | `num_timesteps_in=12`, `num_timesteps_out=12` | `StaticGraphTemporalSignal` | Downloads `METR-LA.zip` to `raw_data_dir` if missing, extracts `adj_mat.npy` and `node_values.npy`, and normalizes values for ordinary datasets. | Has 7-item `get_index_dataset(...)`; construct with `index=True` for index batching. Ordinary `get_dataset` remains this sub-skill; index mechanics route to index-batching. |
| `MTMDatasetLoader` | none | `frames=16` | `StaticGraphTemporalSignal` | Downloads `mtm_1.json` in `__init__`; hand keypoint motion dataset. | No `get_index_dataset`. |
| `MontevideoBusDatasetLoader` | none | `lags=4`, `target_var='y'`, `feature_vars=['y']` | `StaticGraphTemporalSignal` | Downloads `montevideo_bus.json` in `__init__`; feature variables are read from each node's `X` mapping and target variable from each node record. | No `get_index_dataset`. |
| `PedalMeDatasetLoader` | none | `lags=4` | `StaticGraphTemporalSignal` | Downloads `pedalme_london.json` in `__init__`; static weighted graph. | No `get_index_dataset`. |
| `PemsAllLADatasetLoader` | `raw_data_dir=<cwd>/data`, `index=False` | none | None; index-only | Downloads `pems_AllLA_adj_mat.pkl` and `pems_AllLA_speed.h5` into `raw_data_dir` if missing. Requires HDF support for the speed file. | Only `get_index_dataset(...)`; construct with `index=True`. No ordinary `get_dataset`. |
| `PemsBayDatasetLoader` | `raw_data_dir=<cwd>/data`, `index=False` | `num_timesteps_in=12`, `num_timesteps_out=12` | `StaticGraphTemporalSignal` | Downloads `PEMS-BAY.zip` to `raw_data_dir` if missing, extracts `pems_adj_mat.npy` and `pems_node_values.npy`, and normalizes values for ordinary datasets. | Has 7-item `get_index_dataset(...)`; construct with `index=True` for index batching. |
| `PemsDatasetLoader` | `raw_data_dir=<cwd>/data`, `index=False` | none | None; index-only | Downloads `pems_cali_adj_mat.pkl` and `pems_cali_speed.h5` into `raw_data_dir` if missing. Requires HDF support for the speed file. | Only `get_index_dataset(...)`; construct with `index=True`. No ordinary `get_dataset`. |
| `SIDiffusionDatasetLoader` | none | `lags=4` | `StaticGraphTemporalSignal` | Downloads a remote NumPy SI diffusion signal and PyTorch adjacency tensor in `__init__`; no local cache argument. Synthetic PDE static graph. | No `get_index_dataset`. |
| `TwitterTennisDatasetLoader` | `event_id='rg17'`, `N=None`, `feature_mode='encoded'`, `target_offset=1` | none | `DynamicGraphTemporalSignal` | Validates `event_id` and `feature_mode`, then downloads a remote event JSON in `__init__`; no local cache argument. | No `get_index_dataset`. |
| `WaveEquationDatasetLoader` | none | `lags=4` | `StaticGraphTemporalSignal` | Downloads a remote NumPy wave-equation signal and PyTorch adjacency tensor in `__init__`; no local cache argument. Synthetic PDE static graph. | No `get_index_dataset`. |
| `WikiMathsDatasetLoader` | none | `lags=8` | `StaticGraphTemporalSignal` | Downloads `wikivital_mathematics.json` in `__init__`; standardizes daily view targets. | No `get_index_dataset`. |
| `WindmillOutputLargeDatasetLoader` | `raw_data_dir=<cwd>/data`, `index=False` | `lags=8` | `StaticGraphTemporalSignal` | Downloads `windmill_output.json` into `raw_data_dir` if missing, then reads it locally. | Has `get_index_dataset(lags=8, batch_size=64, shuffle=False, allGPU=-1, ratio=(0.7, 0.1, 0.2), dask_batching=False)`. |
| `WindmillOutputMediumDatasetLoader` | none | `lags=8` | Intended `StaticGraphTemporalSignal`, but unavailable in inspected source | Constructor raises `RuntimeError` stating the old `graphmining.ai` dataset is no longer accessible. | No usable index support in inspected version. |
| `WindmillOutputSmallDatasetLoader` | none | `lags=8` | Intended `StaticGraphTemporalSignal`, but unavailable in inspected source | Constructor raises `RuntimeError` stating the old `graphmining.ai` dataset is no longer accessible. | No usable index support in inspected version. |

## Parameter notes

### `lags`

`lags` controls how many previous time steps are used as node features before predicting the next step or target frame. It is used by Chickenpox, PedalMe, WikiMaths, WindmillLarge, EnglandCovid, MontevideoBus, and the synthetic PDE loaders. If `lags` is too large for the number of time periods, the generated feature/target lists can be empty.

Typical snapshot shapes from loader tests and source behavior:

- Chickenpox: `x` shape `(20, lags)`, `y` shape `(20,)`.
- PedalMe: `x` shape `(15, lags)`, `y` shape `(15,)`.
- WikiMaths: `x` shape `(1068, lags)`, `y` shape `(1068,)`.
- EnglandCovid: dynamic edges; `x` shape `(129, lags)`, `y` shape `(129,)`.
- MontevideoBus with one feature variable: `x` shape `(675, lags)`, `y` shape `(675,)`; additional `feature_vars` increase the stacked feature dimension.
- WindmillLarge: `x` shape `(319, lags)`, `y` shape `(319,)`.

### Traffic windows

`METRLADatasetLoader.get_dataset(num_timesteps_in, num_timesteps_out)` and `PemsBayDatasetLoader.get_dataset(num_timesteps_in, num_timesteps_out)` generate sliding windows.

- METR-LA ordinary snapshots use `x` shape `(207, 2, num_timesteps_in)` and `y` shape `(207, num_timesteps_out)`.
- PeMS-Bay ordinary snapshots use `x` shape `(325, 2, num_timesteps_in)` and `y` shape `(325, 2, num_timesteps_out)`.
- Both loaders normalize the full time series with z-score style statistics before creating ordinary snapshots.

### `frames` for MTM

`MTMDatasetLoader.get_dataset(frames=16)` uses consecutive hand-keypoint frames. The inspected source returns `x` as `(3, 21, frames)` and a one-hot target array shaped `(frames, 6)`.

### Montevideo variables

`MontevideoBusDatasetLoader.get_dataset(lags=4, target_var='y', feature_vars=['y'])` is dataset-specific:

- `feature_vars` are looked up under each node's feature mapping.
- `target_var` is looked up on each node record.
- Invalid variable names surface as missing values or NumPy stacking/standardization failures; validate names before long experiments.

### Twitter Tennis options

`TwitterTennisDatasetLoader(event_id='rg17', N=None, feature_mode='encoded', target_offset=1)` validates options before downloading.

- `event_id` must be `'rg17'` or `'uo17'`.
- `feature_mode` must be `None`, `'encoded'`, or `'diagonal'`.
- `N` restricts snapshots to popular nodes if set; leave `None` to use the full stored event graph.
- `target_offset` chooses which future snapshot supplies node labels; the implementation clamps past the final snapshot.

### Synthetic PDE loaders

The PDE loaders return static graph temporal signals but differ in feature layout:

- Advection-diffusion and wave equation flatten lagged time/features per node before constructing `x`.
- SI diffusion keeps susceptible/infected channels in the feature tensor and targets only the infected channel.
- All three download both a signal payload and an adjacency/edge-distance payload in the constructor.
