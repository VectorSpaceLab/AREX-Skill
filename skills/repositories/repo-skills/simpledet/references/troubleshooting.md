# Cross-cutting troubleshooting

Read this when a route reports a failure that crosses setup, data, config, and
execution boundaries.

## Import and package failures

- `ModuleNotFoundError: mxnet`: use the environment diagnostic first. SimpleDet
  has no package metadata and expects imports from the checkout root; a CPU
  environment may import `mxnet` while still being unable to run the entry
  points.
- `ModuleNotFoundError: mxnext`: install the separate `mxnext` dependency at a
  version compatible with the selected SimpleDet commit. Do not substitute a
  current unrelated package.
- `ImportError` in `operator_py.cython`: build the CPU Cython extensions and
  confirm the generated modules are discoverable from the checkout root. The
  repository Makefile also attempts `gpu_nms` and therefore requires `nvcc`;
  do not call a partial CPU build CUDA-complete.
- OpenCV import or GUI errors: use a headless-compatible OpenCV build for data
  loading, and avoid the debug visualization helpers in non-GUI environments.

## Data, config, and checkpoint failures

- Missing `data/cache/<dataset>_<split>.roidb`: run the data-preparation route;
  the train/test scripts do not generate roidb files automatically.
- `assert os.path.exists(image_url)` or COCO annotation errors: validate the
  annotation path, split name, image symlink, and generated record before
  launching a GPU workflow.
- Config import errors: entry scripts convert a path such as
  `config/foo.py` to module `config.foo`; keep the checkout root on the Python
  path and use importable filenames/directories.
- Missing `experiments/...-0000.params`: check `TestParam.model.prefix` and
  `epoch`, then verify that the checkpoint was produced by a compatible symbol.
  Do not blindly download or rename weights.
- Shape/name mismatch: compare `data_name`, `label_name`, static padded shape,
  `max_num_gt`, class count, anchor settings, and class-aware bbox dimensions.

## Backend and runtime failures

- `mx.gpu(...)` failure, zero GPU count, or MXNet CUDA library errors: stop. The
  core train/test/speed workflows require CUDA; CPU import is only a partial
  inspection fallback. Verify the exact MXNet CUDA wheel/toolkit/driver matrix
  rather than changing configs to hide the error.
- `no kernel image` or unsupported architecture: the legacy build may not have
  been compiled for the installed GPU. Use a compatible source build or a
  documented wheel; do not infer success from `mx.gpu(0)` construction alone.
- NCCL/kvstore/worker hangs: reduce to one GPU and a local kvstore first; only
  use `nccl`/distributed launch after all nodes, interfaces, hostfile, and
  shared data paths are validated.
- Out-of-memory or worker stalls: lower `batch_image`, `loader_worker`, image
  shape, proposal/ROI limits, or GPU count; inspect the config's static shape
  and data-loader queues before changing model code.

## Side effects and safety

Training, test, speed benchmarking, checkpoint download, dataset download,
cluster launch, SSH cleanup, and `pkill` operations are not read-only checks.
The source repository's cluster scripts contain private paths and destructive
process cleanup; use them only after explicit operator review and adaptation.
The generated skill does not bundle or invoke those scripts.
