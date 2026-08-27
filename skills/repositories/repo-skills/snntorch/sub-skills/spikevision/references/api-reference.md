# spikevision API reference

> [!WARNING]
> `snntorch.spikevision` is deprecated. Use Tonic for new neuromorphic dataset work. This reference exists for legacy compatibility only.

## Import pattern

The top-level package only emits the deprecation warning. Import the legacy dataset namespace explicitly:

```python
from snntorch.spikevision import spikedata
from snntorch.spikevision.neuromorphic_dataset import NeuromorphicDataset, StandardTransform
from snntorch.spikevision import _transforms as svt
from snntorch.spikevision import events_timeslices as ets
```

## Dataset wrappers and base helpers

| Symbol | Live signature | What it does | Legacy notes |
| --- | --- | --- | --- |
| `NeuromorphicDataset` | `root=None, transforms=None, transform=None, target_transform=None, transform_train=None, transform_test=None, target_transform_train=None, target_transform_test=None` | Abstract HDF5-backed dataset base class. Provides `transform_append`, `target_transform_append`, `__repr__`, and shared download/extract helpers. | `transforms` is mutually exclusive with `transform`/`target_transform`. The `transform_train*` parameters are accepted for compatibility but are not used by the current implementation. |
| `StandardTransform` | `transform=None, target_transform=None` | Callable shim that applies an input transform and a target transform as a pair. | Use when a dataset or wrapper needs a single object that handles both input and label transforms. |
| `NMNIST` | `root, train=True, transform=None, target_transform=None, download_and_create=True, num_steps=300, dt=1000` | Legacy N-MNIST wrapper over ATIS `.bin` data. Default output shape is `[T, 2, 32, 32]`. | `root` is a dataset directory, not the generated `.hdf5` file. If a non-`None` `target_transform` is supplied, the constructor replaces it with a built-in repeated one-hot transform for 10 classes. |
| `DVSGesture` | `root, train=True, transform=None, target_transform=None, download_and_create=True, num_steps=None, dt=1000, ds=None, return_meta=False, time_shuffle=False` | Legacy DVS Gesture wrapper over `.aedat` data. Default output shape is `[T, 2, 128, 128]`. | `return_meta=True` adds light-condition and subject metadata to the return tuple. The current `target_transform` hook is not wired through to the active base-class transform path. |
| `SHD` | `root, train=True, transform=None, target_transform=None, download_and_create=True, num_steps=1000, ds=1, dt=1000` | Legacy Spiking Heidelberg Digits wrapper over HDF5 spike streams. Default output shape is `[T, 700 // ds]`. | `root` is a dataset directory, not the generated `.hdf5` file. If a non-`None` `target_transform` is supplied, the constructor replaces it with a built-in repeated one-hot transform for 20 classes. |

### On-disk expectations

| Dataset | Raw files expected | Generated cache | Notes |
| --- | --- | --- | --- |
| `NMNIST` | `Train/` and `Test/` trees with digit subfolders containing `.bin` files, or the matching archives before cache creation | `n_mnist.hdf5` | Constructor-level cache creation is legacy behavior. |
| `DVSGesture` | `DvsGesture.tar.gz` or an extracted `DvsGesture/` tree with `userXX*.aedat` files and labels CSVs | `dvs_gesture.hdf5` | `time_shuffle` can randomize the sampled start time for training-like use. |
| `SHD` | `shd_train.h5` and `shd_test.h5` before cache creation | `shd.hdf5` | The helper reads spike times and units from the HDF5 structure. |

## Transform helpers

These helpers are import-only and safe to instantiate on synthetic arrays or tensors.

| Symbol | Live signature | Input / output | Notes |
| --- | --- | --- | --- |
| `toOneHot` | `num_classes` | Label array -> one-hot tensor | Expects a column-vector style integer label array. |
| `toDtype` | `dtype` | Array -> tensor with dtype | Thin cast helper. |
| `Downsample` | `factor` | Event rows -> integer-divided event rows | Factor can be an integer or iterable. |
| `CropDims` | `low_crop, high_crop, dims` | Event rows -> cropped event rows | Removes rows outside the requested bounds and re-normalizes coordinates. |
| `CropCenter` | `center, size` | Event rows -> centered crop | Uses `size[1:]` as the spatial extent. |
| `Attention` | `n_attention_events, size` | Event rows -> attention crop | Uses pandas rolling medians to re-center events. |
| `ToChannelHeightWidth` | `()` | Event rows -> 2- or 4-column event rows | If the input has 2 columns, two zero columns are appended; 4-column input is passed through. |
| `ToCountFrame` | `T=500, size=[2, 32, 32]` | Event rows -> dense time-first counts | Produces a `[T, ...size]` count tensor. |
| `ToEventSum` | `T=500, size=[2, 32, 32]` | Event rows -> summed frame | Time integrates and then sums across time. |
| `FilterEvents` | `kernel=None, groups=1, tpad=None` | Dense chunks -> filtered dense chunks | Wraps `conv3d` over 4D or 5D tensors. |
| `ExpFilterEvents` | `length, tau=200, channels=2, tpad=None, device='cpu', **kwargs` | Dense chunks -> filtered dense chunks | Builds an exponential kernel and delegates to `FilterEvents`. |
| `Rescale` | `factor` | Tensor -> scaled tensor | Multiplies by the given factor. |
| `hflip` | `()` | Tensor -> flipped tensor | Legacy horizontal flip helper. |
| `rot90` | `()` | Tensor -> rotated tensor | Rotates 90 degrees clockwise. |
| `dvs_permute` | `()` | Tensor -> permuted tensor | Legacy DVS orientation helper. |
| `Repeat` | `n_repeat` | Label -> repeated label sequence | Used to turn scalar labels into time sequences. |
| `ToTensor` | `device='cpu'` | Array -> `torch.FloatTensor` | Moves the tensor to the requested device. |

## File readers, cache builders, and download helpers

These helpers are local-data or download oriented, not synthetic-smoke helpers.

| Symbol | Live signature | Purpose | Network? |
| --- | --- | --- | --- |
| `download_url` | `url, root, filename=None, md5=None, total_size=None` | Download one file, verify it if an MD5 is supplied, and store it under `root`. Handles Dropbox links specially and falls back from HTTPS to HTTP once. | Yes |
| `download_and_extract_archive` | `url, download_root, extract_root=None, filename=None, md5=None, remove_finished=False` | Download then extract an archive into the requested directory. | Yes |
| `check_integrity` | `fpath, md5=None` | Check whether a file exists and optionally matches a checksum. | No |
| `calculate_md5` | `fpath, chunk_size=1048576` | Compute a file checksum. | No |
| `check_md5` | `fpath, md5, **kwargs` | Compare a computed checksum to an expected checksum. | No |
| `_extract_archive` | `from_path, to_path=None, remove_finished=False` | Extract `.tar`, `.tar.gz`, `.tgz`, `.tar.xz`, `.gz`, or `.zip` files with safe tar extraction checks. | No |
| `identity` | `x` | Backward-compatibility passthrough. | No |
| `events_timeslices.get_tmad_slice` | `times, addrs, start_time, T` | Slice an event stream by time into `[t, m, a, d]` rows. Used by the dataset readers. | No |
| `nmnist.nmnist_load_events_from_bin` | `file_path, max_duration=None` | Parse ATIS `.bin` events into a legacy event array. | No |
| `nmnist.nmnist_get_file_names` | `dataset_path` | Scan local `Train/` and `Test/` trees and return digit-balanced file lists. | No |
| `nmnist.create_events_hdf5` | `directory, hdf5_filename` | Build the N-MNIST cache file from local raw data. | No |
| `shd.load_shd_hdf5` | `filename, train=True` | Read SHD spike times and units from an HDF5 file. | No |
| `dvs_gesture.gather_aedat` | `directory, extracted_directory, start_id, end_id, filename_prefix='user'` | Find DVS Gesture `.aedat` files inside an extracted tree. | No |
| `dvs_gesture.create_events_hdf5` | `directory, extracted_directory, hdf5_filename` | Build the DVS Gesture cache file from local raw data. | No |
| `shd.create_events_hdf5` | `directory, hdf5_filename` | Build the SHD cache file from local raw data. | No |

## Public import surface

- `from snntorch.spikevision import spikedata` exposes `NMNIST`, `DVSGesture`, and `SHD`.
- `snntorch.spikevision` itself only emits the deprecation warning; it is not a modern dataset namespace.
- The legacy dataset classes are the supported public surface for this sub-skill. Everything else is helper-level support for those classes.
