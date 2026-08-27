# Troubleshooting

## Purpose

Read this when CenterNet fails to import, build, find data, or run on the GPU.

## `pycocotools._mask` is missing

**Symptoms**

- `ModuleNotFoundError: No module named 'pycocotools._mask'`
- `train.py --help` or `test.py --help` fails during import of `db.coco`

**Likely causes**

- The COCO Python API was not built in the active environment.
- `Cython` or `numpy` is missing from the same environment that runs CenterNet.
- The extension was built in a different Python environment.

**Recovery**

1. Make sure the active environment has `Cython`, `numpy`, and the other runtime packages listed in `SKILL.md`.
2. Build the COCO API in place from `data/coco/PythonAPI`.
3. Re-run `scripts/check_install.py --repo-root <checkout>`.

## `external.nms` fails to import or build

**Symptoms**

- `ModuleNotFoundError: No module named 'external.nms'`
- Cython errors mentioning `np.int_t` or generated `nms.c` compile failures
- `#error Do not use this file, it is the result of a failed Cython compilation.`

**Likely causes**

- The custom NMS extension was never built.
- The checked-in generated `nms.c` is stale for the active Cython/Numpy combination.
- The toolchain is too new for the legacy source without a compatibility update.

**Recovery**

1. Rebuild from `external/nms.pyx` with the active environment's Cython/Numpy stack.
2. If the modern toolchain rejects the legacy source, use a historically compatible version mix or apply a source compatibility patch before building.
3. Re-run `scripts/check_install.py --repo-root <checkout>`.

## `_cpools` fails to import or build

**Symptoms**

- `ModuleNotFoundError: No module named 'top_pool'`
- Torch C++ errors such as `No matching function for call to 'zeros'`
- ABI mismatch errors while compiling `models/py_utils/_cpools`

**Likely causes**

- The custom pooling extensions were not built in the active environment.
- The extension source does not match the installed torch C++ API.
- The build used a different torch/CUDA combination than the runtime import.

**Recovery**

1. Rebuild the extension against the active torch installation.
2. If the unmodified legacy source fails against a newer torch API, pin to a compatible torch version or adapt the extension source before compiling.
3. Re-run `scripts/check_install.py --repo-root <checkout>`.

## CUDA is unavailable

**Symptoms**

- `torch.cuda.is_available() == False`
- `.cuda()` failures in `train.py` or `test.py`
- `nvidia-smi` shows no visible GPU

**Likely causes**

- CPU-only PyTorch was installed.
- The container or host has no GPU passthrough.
- The driver and wheel combination are incompatible.

**Recovery**

1. Install a CUDA-enabled PyTorch build in the same environment.
2. Confirm that `nvidia-smi` sees a device.
3. Re-run `scripts/check_install.py --repo-root <checkout>`.

## COCO files or cache paths are wrong

**Symptoms**

- `FileNotFoundError` for `annotations/instances_*.json` or an image directory
- The dataset length is zero
- `cache/coco_*.pkl` is missing or rebuilt repeatedly

**Likely causes**

- The COCO split folders are not in the expected layout.
- `data_dir` does not point to the directory that contains `coco/`.
- The annotation file names do not match the selected split.

**Recovery**

1. Follow `references/data-layout.md` exactly.
2. Check `config.py` and the selected JSON config for the `data_dir` setting.
3. Remove stale caches only after the layout is corrected.

## Checkpoint or result path is missing

**Symptoms**

- `pretrained model does not exist`
- `loading model from ...` points to a file that is absent
- `test.py` writes an empty result directory

**Likely causes**

- The `--iter` or `--testiter` value does not match an existing checkpoint.
- The checkpoint was stored under a different snapshot name.

**Recovery**

1. Confirm the snapshot name is the config basename.
2. Confirm the checkpoint exists under `cache/nnet/<snapshot_name>/`.
3. Re-run the command with the correct iteration number.

## `testdev` does not print COCO metrics

**Symptoms**

- The command writes detections but stops before a metric summary.

**Likely cause**

- `testdev` has no ground-truth evaluation in this repo.

**Recovery**

- Treat `results.json` as the output artifact.
- Use `validation` or `training` when you need COCO metrics from this repo.
