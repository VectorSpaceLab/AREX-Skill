# Tensorpack DataFlow Troubleshooting

Start from the symptom. Recover with the smallest change that restores the
DataFlow contract before increasing parallelism or changing storage.

## Reset state and worker initialization

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `self.rng` is missing, all workers produce identical random samples, or augmentors repeat the same randomness. | `reset_state()` was not called in the process that iterates the DataFlow, or the DataFlow was forked after reset. | For standalone use, call `df.reset_state()` immediately before iterating. In custom wrappers, call `self.ds.reset_state()` from wrapper `reset_state()`. Do not fork a DataFlow after `reset_state()`. Use `RNGDataFlow` for sources that need per-process RNG. |
| A forking wrapper behaves strangely after TensorFlow session/GPU creation. | `MultiProcessRunnerZMQ` forks in its `reset_state()`; forking a live TensorFlow/GPU session can be unsafe. | Build/reset forking DataFlows before creating sessions, or switch to mapper/threaded patterns that do not fork after the session exists. |
| Augmentation randomness repeats in subprocesses. | Manual augmentor use did not call `augmentor.reset_state()` in each subprocess. | If using `AugmentImageComponent`, rely on its `reset_state()`. If using `AugmentorList` manually in workers, call `augs.reset_state()` in the worker before use. |

## Reentrancy and concurrent iteration

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error similar to `This DataFlow is not reentrant!`. | One non-reentrant DataFlow instance is being iterated by two consumers at once. | Create two independent DataFlow instances, materialize/cache the data, or restructure so one owner iterates and fans out results. Do not call `iter(df)` again until the previous iterator finishes. |
| Iteration hangs or produces inconsistent samples after nesting parallel DataFlows. | A reset/fork/thread-sensitive DataFlow is nested or shared in a way its contract forbids. | Flatten the pipeline. Avoid nesting multiple `MultiProcessRunnerZMQ` instances. Use mapper-style parallelism for expensive transforms instead of cloning a parallel runner. |
| Validation results depend on iteration order but order changes between runs. | Parallel mappers preserve finite set in strict mode, but not ordering. Parallel runners can duplicate/reorder when worker count is greater than one. | For order-sensitive validation, avoid multi-worker runners and add explicit sequence ids/order restoration around mappers, or run the validation reader serially. |

## Parallel duplicates, order, and randomness

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| First datapoint appears `num_proc` or `num_thread` times. | Runner-style parallelism cloned a deterministic source into independent workers. | Use runner-style only for stochastic training where duplicates/reordering are acceptable. Add worker-local randomness in the source, or switch to `MultiThreadMapData`/`MultiProcessMapData` so only mapping is parallelized. |
| Validation score is wrong or non-reproducible after adding `MultiProcessRunnerZMQ(ds, N)`. | Multiple independent validation readers changed membership/order. | For validation/test, use a single source plus mapper-style parallelism with `strict=True`, batch with `remainder=True`, or keep a single runner process only to move work out of the main process. |
| `strict=True` mapper hangs or behaves undefined. | The wrapped DataFlow is infinite; strict mode is defined for finite iteration to `StopIteration`. | Use a finite source for strict validation. For infinite training data, use non-strict mode and accept stream semantics. |
| Process mapper fails on Windows or spawn-based multiprocessing. | The mapper is a lambda/local closure or an object that cannot be pickled. ZMQ IPC runner is not supported on Windows. | Define mapper functions at module top level, avoid lambdas, or choose thread mapping. Avoid ZMQ IPC runner on Windows. |
| ZMQ pipe crashes or behaves oddly on network filesystems. | ZMQ IPC pipe path or named pipe is on a non-local filesystem, or the pipe path is too long. | Use a local scratch pipe directory through Tensorpack's `TENSORPACK_PIPEDIR` environment variable, or switch to a non-ZMQ/threaded pattern. |

## Serializer and optional dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Cannot import 'lmdb', therefore 'LMDBSerializer' is not available`. | `lmdb` Python package is missing. | Install/enable `lmdb`, then run the bundled smoke script with `--formats lmdb`. If installation is not allowed, use NumPy for tiny fixtures or TFRecord/HDF5 if their deps are present. |
| `Cannot import 'h5py', therefore 'HDF5Serializer' is not available`. | `h5py` is missing. | Install/enable `h5py` or choose LMDB/NumPy/TFRecord. Remember HDF5 is not the high-throughput default. |
| TFRecord serializer fails or `tf.python_io` is unavailable. | TensorFlow/Tensorpack compatibility mismatch, or TensorFlow is missing. | Confirm Tensorpack import and TensorFlow compatibility. Use LMDB when the goal is Tensorpack-native large data storage rather than TFRecord interoperability. |
| `HDF5Serializer.save` asserts datapoint component count. | `data_paths` length does not match each datapoint's component count. | Pass one HDF5 dataset path per component, e.g. `['image', 'label']` for `[image, label]`. |
| NumPy serialization consumes too much memory or is slow. | `NumpySerializer` materializes the entire DataFlow into a compressed object array. | Use LMDB or TFRecord for larger datasets. Keep NumPy serialization for tiny deterministic fixtures. |
| Loaded TFRecord DataFlow has no length. | TFRecord files do not store Tensorpack DataFlow size metadata. | Pass `TFRecordSerializer.load(path, size=<record-count>)` when a length-aware DataFlow is needed. |

Bundled check:

```bash
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats all
```

The smoke script prints clear `OK`, `SKIP`, or `FAIL` lines for each selected
format.

## OpenCV, image dtype, and color order

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cv2` import error for image datasets or augmentors. | OpenCV is missing; `ILSVRC12`, `ImageFromFile`, and many augmentors require it. | Install/enable an OpenCV package appropriate for the environment. For headless servers, prefer a headless build. If OpenCV is impossible, avoid those dataset/augmentor paths. |
| Image colors look swapped or model accuracy collapses after changing loaders. | BGR/RGB mismatch. Tensorpack `ILSVRC12` uses OpenCV and yields BGR images; some custom loaders may yield RGB. | Keep color order explicit. Match augmentation and model preprocessing flags (`rgb=False` for BGR-aware contrast/saturation patterns). Convert only once at the boundary where needed. |
| Augmentor rejects image dtype or produces clipped values. | Tensorpack image augmentors expect uint8 `[0,255]` or floating images in `[0,1]`/`[0,255]`; photometric augmentors may clip. | Normalize dtype/range before augmentation. Use `ToFloat32()` before chained photometric augmentors and `ToUint8()` before IPC/copy-heavy stages if uint8 is acceptable. |
| Bounding boxes/keypoints no longer align with images. | A random transform was applied separately to image and coordinates. | Use `tfm = augmentor.get_transform(image)`, then replay `tfm.apply_image(image)` and `tfm.apply_coords(coords.astype('float32'))`. |
| Crop/resize asserts on shape. | Input image is smaller than the requested crop or has unexpected dimensions. | Add a resize-shortest-edge step before center/random crop, or validate input dimensions before augmentation. |

## Dataset layout and download surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MNIST/CIFAR/SVHN loader tries to download data. | Default dataset cache lacks the files and no prepared `dir`/`data_dir` was supplied. | Ask the user for a prepared dataset directory or explicitly allow download. For no-network settings, use `FakeData` or a custom source over available files. |
| `ILSVRC12` asserts a directory or image file is missing. | Directory layout does not match the expected split structure. | Ensure root has `train/`, `val/`, and/or `test/`. Training expects `train/<synset>/*.JPEG`. Validation can be flat original layout or train-like class subdirectories; set `dir_structure` when auto-detection is wrong. |
| ImageNet labels are wrong for validation. | Metadata directory or validation layout does not match the expected synset mapping. | Verify `ILSVRCMeta` metadata and the `dir_structure` argument. Keep `shuffle=False` for validation unless the metric is order-independent and membership remains exact. |
| `SVHNDigit` fails on `scipy.io`. | SciPy is missing or `.mat` files are absent. | Install/enable SciPy or provide another DataFlow. If files are missing, do not assume network download is allowed. |
| TIMIT-style preprocessing cannot run. | TIMIT data is licensed/external and feature extraction may need compiled audio packages. | Treat it as a reference pattern. Have the user provide data and dependencies, then build a custom source and serialize to LMDB under a user-chosen output path. |

## Slow or empty queues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Tensorpack input queue size is close to zero. | Data pipeline cannot keep up with trainer. | Benchmark DataFlow alone with `TestDataSpeed`. Increase mapper/runner workers only after finding whether CPU, disk, network, decode, augmentation, or IPC is limiting. |
| Queue is nearly full but GPU utilization is low. | Input pipeline is not the bottleneck; model graph/trainer/device placement likely is. | Route to training troubleshooting. Use `FakeData` or `DummyConstantInput` only to isolate graph speed. |
| `TestDataSpeed` is slow only with augmentors enabled. | CPU-bound augmentation or OpenCV transform. | Try `MultiThreadMapData` first for OpenCV-heavy work; try process mapper if Python/GIL-bound. Consider simplifying photometric augmentors or moving cheap normalization into the graph. |
| `TestDataSpeed` is slow without augmentation. | Raw disk/network read or image decode is bottleneck. | Compare a reader that returns a tiny token after reading. If random reads are slow, serialize encoded bytes to LMDB and read sequentially. If decode is slow, move decode into parallel mappers. |
| Process-based pipeline is slower than serial. | IPC serialization/copy overhead exceeds saved compute. | Reduce payload size before IPC (uint8/JPEG bytes), increase batch/mapper granularity, try threads, or keep pipeline serial. |
| First benchmark iterations are slow. | Warmup effects: caches, process startup, graph/session initialization. | Ignore first iterations. Use `TestDataSpeed(ds, warmup=50, size=...)` and compare steady-state changes. |
| Increasing workers stops helping. | Bottleneck moved to disk/network/IPC or oversubscription. | Sweep worker counts and buffer sizes; stop at the fastest stable setting. Do not exceed what storage and CPU can sustain. |

## InputSource bridge failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `QueueInput` datapoint length differs from placeholders. | DataFlow components do not match model input signature. | Inspect with `PrintData`; ensure each datapoint has one component per model input, in the same order or matching dict keys by placeholder op name. |
| `FeedInput` does not work for data-parallel training. | It reuses the same placeholders after first `get_input_tensors()`. | Use `QueueInput`, `TFDatasetInput`, or another feed-free source for data-parallel trainers. |
| Training stops after one dataset pass with `TFDatasetInput`. | The dataset/DataFlow is finite. | Add `.repeat()` to `tf.data.Dataset` or wrap DataFlow with `RepeatedData(ds, -1)` for training. Keep finite data for validation/inference. |
| `StagingInput` fails in inference or multi-GPU fetches. | It requires coordinated stage/unstage hooks and all staged tensors fetched together. It is not suitable for `InferenceRunner` and cannot be nested. | Use plain `QueueInput` for inference/validation unless the trainer setup specifically supports staging. |
| `ZMQInput` import fails. | External `zmq_ops` is missing or sender format is not compatible. | Install/enable matching ZMQ ops and use a compatible Tensorpack dataflow sender, or avoid `ZMQInput` and use `QueueInput`/`TFDatasetInput`. |
