# Shared troubleshooting

## Package install/import

- **`mmcv` version mismatch or missing**: inspect `python -m pip show mmcv`
  and require `0.2.16` for this revision. Do not fix it by mixing modern
  MMDetection/MMCV APIs into the old package.
- **`mmdet` imports the wrong checkout**: print `mmdet.__file__` and verify the
  intended environment and package revision. Use isolated environments for
  multiple MMDetection generations.
- **Editable install fails in metadata generation**: legacy `setup.py` imports
  torch and constructs CUDA extensions during setup. Check torch, `CUDA_HOME`,
  and the toolkit before retrying; do not repeatedly rerun an opaque install.
- **Pillow/NumPy resolver conflicts**: follow the documented old stack and
  choose mutually compatible wheels. A resolver success does not guarantee
  old torchvision or compiled operators work.

## Compiled backends

- **`CUDA_HOME`/`nvcc` missing**: install or expose a compatible CUDA toolkit,
  set `CUDA_HOME`, and verify `nvcc --version` before rebuilding. A visible
  NVIDIA driver is insufficient.
- **`cannot import name nms_cuda`, `deform_conv_cuda`, or `roi_align_cuda`**:
  the extension build did not complete or the `.so` is not on the package path.
  Rebuild against the active torch/CUDA pair; do not silently route a CUDA
  config to CPU.
- **undefined symbols/ABI errors**: rebuild after changing torch, compiler,
  CUDA, or NumPy. Remove only stale build outputs in a disposable environment;
  preserve the error evidence in the project environment.
- **CPU NMS works but GPU NMS fails**: classify this as a partial backend
  result. Check tensor device, dtype, shape `[N, 5]`, and operator build
  separately.

## Data and configuration

- **missing file/empty dataset**: resolve the final inherited config, check
  `data` paths and annotation/image existence, and validate category ids before
  launching a model.
- **wrong annotation semantics**: COCO instance segmentation needs image,
  annotation, category, and segmentation fields consistent with the chosen
  dataset class. VOC, Cityscapes, and WIDER Face are not interchangeable by
  renaming directories.
- **config key has no effect**: Python config inheritance and dictionary merges
  may leave an inherited value active. Print the final config and verify the
  consumer module reads the key.
- **shape/target errors**: check image transforms, mask dimensions, class count,
  bbox format, and train/test pipeline alignment before debugging the model.

## CLI/API misuse

- **unknown flag or positional mismatch**: use the exact script's `--help` and
  keep config/checkpoint order explicit. The old tools are not modern
  `tools/test.py` interfaces.
- **API result appears nested**: detection APIs return per-class structures;
  instance-segmentation results contain masks and scores in a different shape
  from bbox-only detectors. Inspect the configured detector family before
  indexing.
- **device mismatch**: choose `cuda:0` only after CUDA and extensions pass;
  move tensors/model consistently and do not use a CPU checkpoint load as proof
  of GPU readiness.
- **visualization fails in headless execution**: use file output, a headless
  image backend, or the non-GUI helper. Webcam and display workflows are
  hardware-dependent and not safe default smoke tests.

## Training/evaluation failures

- **out of memory**: reduce batch/image scale/model size or use a smaller local
  fixture; do not change evaluation semantics merely to fit memory.
- **distributed launch hangs**: stop the job, verify process count, visible
  devices, rendezvous/port, and NCCL. Do not launch cluster scripts from a
  single-GPU smoke test.
- **metrics are unexpectedly low**: confirm checkpoint/config pairing, dataset
  split, class order, annotation format, score thresholds, and whether the
  reported model-zoo number used a different test-time policy.
- **robustness benchmark cannot start**: install the optional corruption
  dependency only when that workflow is selected and use a local, bounded
  image set; never download benchmark data implicitly.
