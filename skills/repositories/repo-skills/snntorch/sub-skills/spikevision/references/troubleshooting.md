# spikevision troubleshooting

> [!WARNING]
> `snntorch.spikevision` is deprecated. The recommended fix for new work is to move to Tonic, not to expand this legacy surface.

## Import and dependency issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `DeprecationWarning: The module snntorch.spikevision is deprecated...` | Expected import-time warning | Keep going only if you are maintaining legacy code. For a new project, use Tonic instead. |
| `ImportError` involving `h5py` | The dataset modules import `h5py` at module load time | Install `h5py` before importing `spikedata` or the dataset submodules. |
| `ImportError` involving `torchvision` | The local transform module imports `torchvision.transforms` | Install `torchvision` before importing the local transforms. |
| `ImportError` involving `pandas` | The `Attention` helper uses `pandas.DataFrame` | Install `pandas` or avoid the `Attention` helper. |
| `ImportError` involving `dv` or `importRosbag` | Optional file-conversion helpers were called | Those helpers are optional and require external packages that are not part of the core legacy dataset flow. |

## Path and cache problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `File ... does not exist and download_and_create is False` | The cache file is missing, but the constructor was told not to download or build it | Point `root` at a directory with the expected cache file already present, or allow cache creation in your own environment. |
| `N-MNIST Dataset not found, looked at: ...` | The raw N-MNIST directory layout is missing | Check that `Train/` and `Test/` are present under the dataset directory and that each contains digit subfolders with `.bin` files. |
| `DVS Gestures Dataset not found, looked at: ...` | The extracted DVS Gesture tree is missing | Check that `DvsGesture/` and the `userXX*.aedat` files exist under the dataset directory. |
| `File not found or corrupted.` | A download completed but failed integrity verification | Replace the archive, then rebuild the cache. |
| `Attempted Path Traversal in Tar File` | The archive failed the safe extraction check | Treat the archive as invalid and fetch a clean copy. |

## File-format expectations

| Dataset | Raw format expected by the reader | Generated cache format |
| --- | --- | --- |
| `NMNIST` | ATIS `.bin` event files | `n_mnist.hdf5` |
| `DVSGesture` | `.aedat` event files plus label CSVs | `dvs_gesture.hdf5` |
| `SHD` | HDF5 spike files (`shd_train.h5`, `shd_test.h5`) | `shd.hdf5` |

If the file layout does not match these expectations, the constructor will not be able to build or read the dataset cache.

## Constructor quirks to remember

- `NMNIST` and `SHD` replace any non-`None` `target_transform` with their own repeated one-hot transform.
- `DVSGesture` accepts `target_transform` in the signature, but the current implementation does not wire that hook into the active base-class transform path.
- `DVSGesture(..., return_meta=True)` changes the return arity to four values.
- `DVSGesture` uses a legacy `sample(...)` helper that slices with fixed train/test defaults; treat `num_steps` as a sizing hint, not a guarantee of the exact slice logic.
- `toOneHot` is easiest to use after `Repeat(...)` because it expects a column-vector style label array.
- `ToChannelHeightWidth` only accepts 2-column or 4-column event rows.
- `ToCountFrame` and `ToEventSum` expect time-sorted event rows; if the times are not sorted, the binning will be wrong.

## Out of scope here

- Real dataset downloads
- Notebook-style plotting and training
- Tonic implementation details
- Any assumption that network access is available during skill extraction
