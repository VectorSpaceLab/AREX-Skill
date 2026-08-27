# Data-preparation troubleshooting

## Path, classes, and cached indexes

- **`Found 0 images in subfolders`:** verify that `--data_root` is the parent
  of `ImageNet`, not `ImageNet` itself. Confirm the tree is
  `data/ImageNet/<class>/<image>`, class entries are directories, and files
  use one of the supported image suffixes. Decode one image with Pillow before
  launching a large conversion.
- **Wrong labels after changing folders:** remove the relevant
  `<dataset>_imgs.npz` index from the current working directory and let
  `ImageFolder` regenerate it. The cache stores path/class pairs and is not
  automatically invalidated when the tree changes.
- **Classes are unexpectedly reordered:** class ids are sorted by directory
  name, not by archive order or an external label file. Preserve the same
  class directory names between direct and HDF5 preparation.
- **Object-array/index load error on a newer NumPy:** this legacy index cache
  contains tuples. Do not blindly enable unsafe pickle loading in a shared
  environment. Remove the cache and either run with the repository's
  compatible dependency set or make a reviewed source compatibility change;
  then regenerate and verify the class mapping.

## CIFAR acquisition and shape

- **`Dataset not found or corrupted`:** the archive is absent or its checksum
  failed. Approve/retry the network download, or install the correct
  torchvision-style archive beneath `data/cifar` and use the class's
  integrity check. Do not treat a partial archive as a valid dataset.
- **CIFAR labels or dimensions look wrong:** `C10` is 10 classes and `C100`
  is 100, both at 32x32. The loader reshapes pickled CHW-flat arrays to HWC,
  converts each sample to PIL, then applies the configured transforms. A
  custom preprocessing script must not feed CHW arrays directly to a PIL
  transform.
- **Augmentation seems frozen:** `load_in_mem=True` for ImageFolder applies
  the transform while caching, so random choices are made once at
  initialization. Omit it when per-epoch random augmentation matters. CIFAR
  itself always materializes its archive arrays in RAM.

## HDF5 schema and conversion

- **`make_hdf5.py` refuses to start:** pass `I32`, `I64`, `I128`, or `I256`,
  not an `_hdf5` key. The guard prevents accidentally reading a file that the
  script is about to overwrite.
- **Validator reports wrong shape/dtype:** `imgs` must be `(N, 3, S, S)` and
  `uint8`; `labels` must be `(N,)` and `int64`, with the same N. The HDF5
  loader expects channel-first bytes and performs the only normalization. Do
  not repair a file by merely renaming it; regenerate from the correct
  non-HDF5 source.
- **Labels are out of range or N differs:** inspect the source class
  directories and the selected dataset key. For ImageNet, ids should be
  `0..999`. A stale ImageFolder index can make a source tree and HDF5 label
  mapping disagree; regenerate the index and HDF5 together.
- **Conversion runs out of disk, is killed, or leaves a partial file:** stop
  downstream training, record the partial path, check its metadata with the
  validator, and normally remove/recreate it after confirming free space.
  Conversion is a large write and is intentionally not auto-retried by this
  skill.
- **Conversion is slow:** reduce or increase `--chunk_size` only after a
  representative benchmark. Larger chunks improve contiguous batch reads but
  increase chunk-buffer size and random-read amplification; LZF trades CPU
  work for smaller output. Also tune `--batch_size` and `--num_workers`
  independently.

## RAM, workers, and HDF5 I/O

- **Host RAM exhaustion with `--load_in_mem`:** omit it first. For HDF5 the
  whole `imgs` array is resident; for ImageFolder all transformed tensors are
  resident. The README's I128 estimate is about 64GB for the file and roughly
  96GB+ recommended RAM for the full training recipe. Leave headroom for
  workers, Python, the model, and other processes.
- **Worker hangs, file-lock errors, or poor HDF5 throughput:** start with
  `--num_workers 0`, then increase cautiously. The non-memory HDF5 path opens
  the file inside each sample access; many workers can overload storage or
  expose old h5py/process behavior. Do not assume more workers is faster.
- **CUDA out-of-memory during moments:** lower moments `--batch_size`; this
  controls Inception's GPU batch and is independent of HDF5 `--chunk_size`.
  `--num_workers` and `--load_in_mem` affect host-side pressure, not the
  Inception model's GPU batch.
- **Pinned-memory pressure:** remove `--pin_memory`-equivalent behavior by
  passing `--no_pin_memory` through training/data-loader entry points when
  host pinned memory is constrained. `make_hdf5.py` already disables pinning.

## Transforms and moments mismatch

- **HDF5 `--augment` changes nothing:** this is expected. `ILSVRC_HDF5`
  converts bytes to `[-1,1]` internally and ignores `transform`. Prepare an
  augmented distribution from ImageFolder instead, or implement and verify a
  deliberate HDF5 transform change outside this sub-skill.
- **Images look stretched or cropped unexpectedly:** ImageNet non-augmented
  mode center-crops the shorter square and resizes; augmented mode samples a
  random square from the long-edge geometry and resizes. CIFAR remains 32x32.
  Check the selected `I32/I64/I128/I256` key rather than changing only a model
  flag.
- **Missing moments or incompatible FID:** calculate moments after the final
  representation and resolution are fixed. `I128_inception_moments.npz` is
  not interchangeable with 256px, a different class domain, or a different
  preprocessing distribution. The output is saved in the current directory;
  verify that this is where `inception_utils.py` will look.
- **Unexpected Inception Score:** the source warns that ordered, class-grouped
  traversal underestimates training-data IS; use `--shuffle` if that estimate
  is the goal. Also remember that this PyTorch Inception implementation is
  for monitoring and differs from official TensorFlow metrics.
