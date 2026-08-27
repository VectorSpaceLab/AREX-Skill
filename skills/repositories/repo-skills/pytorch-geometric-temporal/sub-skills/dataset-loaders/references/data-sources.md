# Dataset Data Sources and Cache Behavior

## Purpose

Read this before constructing a dataset loader. It explains which loaders fetch data from the network, which ones honor `raw_data_dir`, how to pre-stage files when supported, and what to do when no-download execution is required.

## Safe no-download operations

These operations should not download data:

- Importing `torch_geometric_temporal.dataset` when its import-time dependencies are installed.
- Inspecting classes and method signatures with `python scripts/list_dataset_loaders.py --format text`.
- Reading the bundled references in this sub-skill.

These operations may download or write files:

- Instantiating most `*DatasetLoader` classes.
- Calling constructors for traffic loaders when required files are missing from `raw_data_dir`.
- Instantiating synthetic PDE loaders, which fetch NumPy/PyTorch payloads immediately.

## Source families

### Remote JSON loaders without a local path parameter

The following constructors fetch JSON directly and do not expose `raw_data_dir`:

| Loader | Remote payload | Built-in no-download path? |
| --- | --- | --- |
| `ChickenpoxDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/chickenpox.json` | No. |
| `PedalMeDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/pedalme_london.json` | No. |
| `WikiMathsDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/wikivital_mathematics.json` | No. |
| `EnglandCovidDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/england_covid.json` | No. |
| `MontevideoBusDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/montevideo_bus.json` | No. |
| `MTMDatasetLoader` | `https://raw.githubusercontent.com/benedekrozemberczki/pytorch_geometric_temporal/master/dataset/mtm_1.json` | No. |
| `TwitterTennisDatasetLoader` | `https://raw.githubusercontent.com/ferencberes/pytorch_geometric_temporal/developer/dataset/twitter_tennis_<event_id>.json` | No. |

Even if similarly named JSON files are available in a package checkout, these constructors are implemented as web reads. For no-download work, avoid these constructors and build `StaticGraphTemporalSignal` or `DynamicGraphTemporalSignal` objects from already available arrays in the temporal-signals workflow.

### Traffic and large benchmark loaders with `raw_data_dir`

For these loaders, use a disposable or project-managed cache directory and pre-stage the expected filenames when downloads are not allowed.

| Loader | Files expected under `raw_data_dir` | Network source if missing | Pre-stage guidance |
| --- | --- | --- | --- |
| `METRLADatasetLoader` | `METR-LA.zip`; after extraction `adj_mat.npy`, `node_values.npy` | `https://anl.app.box.com/shared/static/plgsv3te0akmqluiuqva34su60nn93c2` | To avoid network, make the real `METR-LA.zip` available before construction. Keeping extracted arrays too avoids extraction work. |
| `PemsBayDatasetLoader` | `PEMS-BAY.zip`; after extraction `pems_adj_mat.npy`, `pems_node_values.npy` | `https://anl.app.box.com/shared/static/7ealcaw862pm12sglyt5g71743eu7s5l` | To avoid network, make the real `PEMS-BAY.zip` available before construction. Keeping extracted arrays too avoids extraction work. |
| `PemsDatasetLoader` | `pems_cali_adj_mat.pkl`, `pems_cali_speed.h5` | `https://anl.app.box.com/shared/static/4143x1repqa1u26aiz7o2rvw3vpcu0wp` and `https://anl.app.box.com/shared/static/7hfhtie02iufy75ac1d8g8530majwci0` | Pre-stage both files. This loader is index-only and requires HDF support through pandas/tables. |
| `PemsAllLADatasetLoader` | `pems_AllLA_adj_mat.pkl`, `pems_AllLA_speed.h5` | `https://anl.app.box.com/shared/static/9qc2lc1147xzh8kmq3j4fuo4buiksxua` and `https://anl.app.box.com/shared/static/crzf75ein8s839de8fklpubauddv1p6w` | Pre-stage both files. This loader is index-only and requires HDF support through pandas/tables. |
| `WindmillOutputLargeDatasetLoader` | `windmill_output.json` | `https://anl.app.box.com/shared/static/wgwb75lt3ty3pv5a15y9bilx1mjhcq59` | Pre-stage the JSON file. Construct with `index=True` only when planning index batching. |

Notes:

- For METR-LA and PeMS-Bay, the zip-file check happens before the extracted-file check. If the zip is absent, the constructor may try to download even when extracted arrays are present.
- If a path-related error shows nested cache directory names during download, pass a resolved cache directory and create it before construction.
- Use `raw_data_dir` only for data caches. Do not put generated skill files, model checkpoints, or verification artifacts there.

### Synthetic PDE loaders

These loaders are synthetic/benchmark sources, but their constructors still download remote payloads.

| Loader | Signal payload | Adjacency/edge payload | Built-in cache? |
| --- | --- | --- | --- |
| `AdvectionDiffusionDatasetLoader` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/advection_diffusion_equation/advection_diffusion_dataset.npy` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/advection_diffusion_equation/nuts3_adjacent_distances.pt` | No. |
| `SIDiffusionDatasetLoader` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/SI_diffusion_equation/SI_equation_dataset.npy` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/SI_diffusion_equation/nuts3_adjacent_distances.pt` | No. |
| `WaveEquationDatasetLoader` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/wave_equation/wave_equation_dataset.npy` | `https://raw.githubusercontent.com/Jostarndt/Synthetic_Datasets_for_Temporal_Graphs/main/data/wave_equation/germany_coastline_adjacency.pt` | No. |

For no-download experiments that only need PDE-like shapes, construct a small synthetic temporal signal directly instead of using these loaders.

### Unavailable windmill loaders

`WindmillOutputSmallDatasetLoader` and `WindmillOutputMediumDatasetLoader` are exported, but the inspected constructors raise a runtime error explaining that the historical `graphmining.ai` source is no longer accessible. Do not route users to these loaders for ordinary work in this version.

## Practical no-download alternatives

When network access is not allowed:

1. Use `scripts/list_dataset_loaders.py` for signature planning.
2. Prefer loaders with `raw_data_dir` only when every expected file is already staged.
3. For JSON and PDE loaders without a cache parameter, create a custom temporal signal from arrays that are already available to the user.
4. Use synthetic signal smoke tests for downstream iterator/model logic rather than constructing web loaders.
5. If the user's real goal is index batching, plan the dataset side here but route `get_index_dataset` and batch semantics to the index-batching sub-skill.

## Minimal allowed-network loading pattern

Use this only after the user permits downloads/cache writes:

```python
from torch_geometric_temporal.dataset import METRLADatasetLoader

loader = METRLADatasetLoader(raw_data_dir="<cache-dir>")
dataset = loader.get_dataset(num_timesteps_in=12, num_timesteps_out=12)
snapshot = next(iter(dataset))
print(snapshot.edge_index.shape, snapshot.x.shape, snapshot.y.shape)
```

Replace `METRLADatasetLoader` with the selected loader and use the parameter table in `dataset-loader-reference.md` to choose the correct `get_dataset` arguments.
