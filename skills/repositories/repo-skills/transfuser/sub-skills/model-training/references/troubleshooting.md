# Training Troubleshooting

Use this reference after the safe validator and checkpoint inspector. Each symptom is paired with a likely source-level cause and a bounded next step. Do not “fix” a required CUDA failure by switching to CPU: this training implementation has no CPU substitute.

## Environment and imports

### `torch.cuda.is_available()` is false, CUDA allocation fails, or `torch.cuda.set_device` errors

**Cause:** no visible NVIDIA device, incompatible driver/wheel, a masked device, or a process running outside the intended CUDA environment.

**Recover:** run the validator with `--check-runtime`; confirm the visible-device count and a tiny CUDA allocation; use a matching PyTorch/CUDA wheel. Keep the documented cu113 stack and verify the actual device mapping. A CPU import or `pip check` is not sufficient. Stop if no CUDA-capable runtime is available.

### `ImportError: mmcv...`, `No module named mmdet`, `mmsegmentation`, or `mmcls`

**Cause:** the legacy OpenMMLab dependency family is absent, or `mmcv`/`mmcv-full` is the wrong variant/version.

**Recover:** install the explicitly required versions from the repository compatibility plan, using a wheel built for PyTorch 1.12/CUDA 11.3. Re-run `--check-runtime` and `pip check`. Do not silently substitute modern OpenMMLab APIs; `model.py` imports `mmcv` operators, mmdet heads/utilities, and their older APIs.

### `No module named torch_scatter` or an undefined compiled `torch_scatter` symbol

**Cause:** PointPillars was enabled without the matching PyG wheel, or the extension was built for a different torch/CUDA ABI.

**Recover:** install `torch-scatter` 2.1.0 from a wheel matching PyTorch 1.12/CUDA 11.3, verify a tiny `scatter_max` import, then rerun the validator. This is required only for PointPillars, but the imported `model.py` itself imports PointPillarNet, so the model import probe may still expose it.

### `timm` tries to download weights, hangs, or fails with a network error

**Cause:** image encoders use `pretrained=True` during model construction; a fresh environment has no local cache.

**Recover:** pre-stage trusted weights in an approved cache or allow the network operation explicitly. Do not add downloads to the bundled safe scripts, and do not claim a model construction smoke passed merely because imports passed.

## Dataset and configuration

### `FileNotFoundError` for `rgb`, `topdown/encoded_*.png`, `label_raw`, or `measurements`

**Cause:** wrong dataset root depth, flat route layout, missing modality, wrong topdown filename prefix, or incomplete frame retention.

**Recover:** run `validate_training_setup.py --dataset-root ... --strict`; inspect the reported scenario/town/route and repair the data tree. The loader expects scenario → town-group → route → modality. It reserves two leading and two trailing frames and `pred_len` future labels, so a route can be non-empty but still yield zero samples.

### `IndexError` or empty DataLoader after `02_05_withheld`

**Cause:** no nested directory name contains the exact case-sensitive substrings `Town02` or `Town05`, or every group matches them; alternatively routes are too short for the frame margins.

**Recover:** inspect the validator split summary. Rename or regenerate groups only if that is truly the dataset convention; otherwise choose a split consistent with the data. Require nonzero train and validation candidates before launch.

### `JSONDecodeError`, missing label keys, or matrix/shape errors in `__getitem__`

**Cause:** malformed measurement/label JSON or an export that omitted `ego_matrix`, command coordinates, object geometry, or future-frame annotations.

**Recover:** validate JSON and required keys in the failing route. Every current measurement needs `ego_matrix`, `x`, `y`, `theta`, `x_command`, `y_command`, speed and controls. Current-frame label objects parsed for detection need `id`, `ego_matrix`, `num_points`, `position`, `extent`, `yaw`, `speed`, and `brake`; future label frames at minimum need matching `id` and `ego_matrix` for waypoint lookup. Do not use a single-frame annotation as a four-step future sequence.

### `ValueError` from image/BEV array shape or a semantic loss dtype error

**Cause:** HWC/CHW confusion, non-integer semantic labels, wrong crop dimensions, color/encoding mismatch, or a topdown file that is not the expected encoded map.

**Recover:** confirm RGB/depth/semantic preprocessing yields the shapes and dtypes in `data-format.md`; preserve nearest-neighbor semantic resizing and channels-first image/LiDAR outputs. Use the safe validator first; it intentionally does not pretend to prove decoded tensor semantics.

### `GlobalConfig` prints an unknown setting error or silently accepts a typo override

**Cause:** only `all`, `02_05_withheld`, and `eval` are recognized; kwargs are assigned with no name validation.

**Recover:** use one of the exact settings, pass an explicit dataset root, and review `args.txt`. For config overrides, compare the effective attributes against `api-reference.md`; a typo such as `backbome` creates an unused attribute rather than changing the model.

## Backbone and model construction

### `The chosen vision backbone does not exist` or a similar dispatch failure

**Cause:** case-sensitive mismatch or a name outside `transFuser`, `late_fusion`, `latentTF`, `geometric_fusion`.

**Recover:** use one of the four exact names. Do not use `transfuser`, `late-fusion`, or an arbitrary timm model as the top-level backbone. The error originates in `LidarCenterNet`/Engine dispatch.

### `AttributeError` for `feature_info`, `layer1`, `s1`, `conv1`, `global_pool`, or ConvNeXt/RegNet internals

**Cause:** an image/LiDAR architecture does not expose the stage layout expected by the selected implementation, or a newer `timm` changed the model internals.

**Recover:** start with the source-tested families such as `regnety_032`, `resnet34`, or `efficientnet_b0` only where the selected code path has been checked. Pin `timm==0.6.7` for the verified stack. Do not paper over the error by loading a checkpoint with missing keys; revalidate model construction.

### OOM during model construction or first batch

**Cause:** model/backbone resolution, batch size, DDP world size, PointPillars canvas, workers/cache, or a debug visualization allocation exceeds available VRAM/system memory.

**Recover:** first preserve the architecture/checkpoint contract and lower per-GPU `--batch_size`; reduce visible GPUs only with a deliberate DDP change; disable disk cache/debug if storage or host memory is the bottleneck. For PointPillars, confirm `max_lidar_points` and range. Do not claim a smaller architecture is compatible with an existing checkpoint without inspection.

### Geometric fusion fails with index, reshape, or device errors

**Cause:** `bev_points`/`cam_points` were omitted, created at the wrong scale, or do not match batch and anchor dimensions; the model expects correspondence tensors generated from the current raw LiDAR geometry.

**Recover:** use `backbone=geometric_fusion` consistently in config and data loader, keep the loader-generated projections, and validate batch size/shape on CUDA. A fabricated zero tensor is not a valid substitute for camera↔BEV correspondences.

### LatentTF outputs look wrong or the input tensor is unexpectedly modified

**Cause:** latentTF overwrites LiDAR channels 0 and 1 with a positional grid in-place.

**Recover:** pass the intended tensor and do not reuse the pre-positional histogram object. Keep sequence length 1; the GPT implementation asserts it. Compare the effective `args.txt` and model family to the checkpoint provenance.

### PointPillars fails in `scatter_max`, has no points, or reports a tensor width mismatch

**Cause:** missing/mismatched `torch-scatter`, a raw point array not shaped as XYZI, invalid `num_points`, or all points filtered outside `min_x..max_x`/`min_y..max_y`.

**Recover:** validate the raw array and actual counts; ensure padding is `(max_lidar_points,4)` and only the first `num_points` rows are real. Check coordinate sign/range and matching `num_input=9`, `num_features=[32,32]`. If the run was not trained with PointPillars, disable it rather than changing the input encoder under an old checkpoint.

## CLI and DDP

### `KeyError: 'RANK'`, `'LOCAL_RANK'`, or `'WORLD_SIZE'`

**Cause:** `--parallel_training` remained `1` (the default) but the script was launched with plain Python.

**Recover:** for one GPU pass `--parallel_training 0`. For DDP use the documented `torchrun` command. Never hand-edit rank variables as a substitute for a process group; `torchrun` must set all three and the world size must match the process count.

### NCCL initialization timeout, wrong device, or ranks hang at barrier

**Cause:** device count mismatch, duplicate visible GPU assignment, bad rendezvous arguments, occupied/unavailable devices, or a backend/network issue.

**Recover:** use `CUDA_VISIBLE_DEVICES` with exactly `--nproc_per_node` devices, set `OMP_NUM_THREADS` and `OPENBLAS_NUM_THREADS=1`, select a unique `--rdzv_id`, and inspect every rank's startup line. Test a two-process launch only after a single-GPU CUDA probe succeeds. Stop if the node cannot provide the required GPUs/NCCL.

### `--sync_batch_norm` or `--zero_redundancy_optimizer` appears ineffective

**Cause:** those options are only meaningful in distributed mode.

**Recover:** use `--parallel_training 1` with `torchrun` for them, or leave them zero in single-GPU mode. If using Zero Redundancy, wait for rank 0 consolidation before assuming optimizer state is saved.

### The run writes to an unexpected directory or starts at an unexpected epoch

**Cause:** the script appends `id` to `logdir`, and Engine increments its epoch counter inside `train()`.

**Recover:** expect `<logdir>/<id>/model_1.pth` for a fresh `start_epoch=0`. On resume, set `--start_epoch` explicitly to the intended outer epoch and confirm the derived optimizer filename exists.

## Checkpoints and logs

### `FileNotFoundError` for `optimizer_*.pth` while `model_*.pth` exists

**Cause:** resume always derives the optimizer path by replacing `model_` with `optimizer_`; model-only recovery is not implemented.

**Recover:** restore the matching optimizer state or start a deliberate weights-only port using a separate, reviewed loading path. Do not rename an unrelated optimizer file.

### `Missing key(s)`, `Unexpected key(s)`, or `size mismatch` in `load_state_dict`

**Cause:** wrong backbone/architecture/config, DDP `module.` prefix difference, changed heads, or an incompatible checkpoint.

**Recover:** run `inspect_checkpoint.py` on the model file and compare keys/shape metadata with effective `args.txt` and config. For DDP prefix conversion, explicitly strip or add `module.` only after verifying all keys. Keep strict loading; investigate every mismatch.

### A checkpoint can be inspected but unsafe loading fails

**Cause:** the file is not a plain state dict, was saved with a different PyTorch object layout, or requires trusted pickle globals.

**Recover:** keep default metadata inspection; only use `--unsafe-load` for a trusted artifact in the matching legacy environment. Never execute an untrusted `.pth` during diagnosis.

### TensorBoard is empty or only rank 0 has logs

**Cause:** rank 0 is the only writer by design; the run may have failed before the first logging step or may be reading the parent logdir instead of `<logdir>/<id>`.

**Recover:** inspect `args.txt`, rank-0 stdout, and event files under the run directory. Do not expect one event stream per rank.

## Cache and debug

### `SCRATCH` becomes `None/dataset_cache`, permission denied, or cache fills the disk

**Cause:** DDP disk-cache mode assumes `SCRATCH` exists and is writable; the source sets a very large 768-GiB cache cap.

**Recover:** set `SCRATCH` to a writable fast local filesystem visible to all ranks on the node, check free space, or disable `--use_disk_cache`. The helper never creates or clears the cache.

### Cache mode fails while `multitask=False`

**Cause:** the cache encoding path calls PNG compression on depth/semantic values that are `None`.

**Recover:** disable disk cache for this configuration or patch/test the cache branch before training. Do not delete cache contents as a first response.

### Debug visualization crashes or files collide under DDP

**Cause:** visualization expects multitask decoder outputs and a shared path; it runs periodically and is not designed as a rank-safe artifact writer.

**Recover:** set `config.debug=False` for training or run debugging on one GPU. If changing the source to support DDP debug, use rank-specific output and verify it separately.

## External boundaries

- Missing CARLA is not a training-package failure. Dataset generation and runtime evaluation need CARLA 0.9.10.1 and are handled by sibling sub-skills.
- Missing network access can prevent pretrained `timm` initialization or dataset/checkpoint acquisition; bundled helpers do not download.
- Docker, cloud credentials, and large storage are not prerequisites for a local training preflight; do not add them to a training command unless the downstream evaluation task requires them.
