# Cross-cutting troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torchreid'` | Torchreid is not installed in the active Python environment. | Install the package and rerun `python scripts/check_torchreid_env.py`. Do not rely on a vanished source checkout to supply imports. |
| `ModuleNotFoundError: No module named 'torch'` or `torchvision` | PyTorch foundation packages are missing. | Install a CPU or CUDA PyTorch/torchvision pair appropriate for the task backend, then rerun the root check. |
| Build/install fails while evaluating `setup.py` with missing `numpy` or `Cython` | Torchreid's setup imports NumPy/Cython during extension build. | Install `numpy` and `Cython` before building the package; if build isolation hides them, use a build mode that makes the prepared build dependencies visible. |
| `pip check` reports OpenCV/NumPy conflicts | A new OpenCV wheel may require NumPy 2 while legacy Torchreid code is safer with NumPy 1.x. | Pin compatible package versions in the task environment and rerun smoke checks. Avoid claiming success until `pip check` and imports pass. |
| Cython rank extension unavailable warning | `torchreid.metrics.rank_cylib.rank_cy` did not build or cannot import. | CPU/Python rank evaluation can still work but is slower. Rebuild only if fast large-gallery evaluation is needed. |

## Backend confusion

- CPU smoke tests prove importability and API semantics, not multi-GPU training performance.
- CUDA should be checked with the task environment's `torch.cuda.is_available()`, device count, and a tiny allocation before running long training/evaluation.
- If a user asks for a CUDA result and CUDA is unavailable, either narrow to CPU semantics or stop and request compatible hardware/environment evidence.
- For OpenVINO/TFLite export, install only the requested optional packages and verify each stage separately.

## Network and data failures

- Many ReID datasets have fragile, moved, gated, or license-restricted downloads. Treat dataset roots as user-provided unless network access is explicitly approved.
- If a dataset class raises a missing-file error, read the dataset layout in `sub-skills/training-evaluation/references/data-formats.md` before retrying.
- If a pretrained model download starts unexpectedly, prefer a local checkpoint path or construct models with `pretrained=False` for smoke tests.

## Checkpoint/model mismatch

- `load_pretrained_weights` strips `module.` prefixes and ignores unmatched layers, so a partially mismatched checkpoint may warn instead of crashing.
- Export and feature helpers should use explicit `--model-name` when a checkpoint filename does not identify the architecture.
- If no checkpoint layers match, stop and verify the model key, classifier head, and training loss mode before trusting results.

## Config and CLI mistakes

- Dotted config overrides must use exact keys such as `model.load_weights`, `test.evaluate`, `test.visrank`, and `data.save_dir`.
- `visrank` is only valid in test-only/evaluation mode.
- Triplet training needs a triplet-capable model output and usually `RandomIdentitySampler` with enough instances per identity.
- Video ReID uses tracklet batches and `VideoDataManager`, not the image data manager.

## Export-stage failures

- Missing `onnx` blocks actual ONNX export; missing OpenVINO blocks OpenVINO conversion; missing `openvino2tensorflow`/TensorFlow blocks TFLite-style conversion.
- Dynamic axes are set during ONNX export; downstream converters may not preserve every dynamic behavior.
- Do not overwrite existing artifacts unless the user approved it or the helper was run with an explicit overwrite flag.

## Long-tail gaps

The advanced `projects/` workflows for DML, OSNet-AIN NAS, and PA-100K attribute recognition are not runtime-covered by this generated skill. If a task needs them, report that limitation or run an `extend-repo-skill`/refresh workflow that bundles the required project source and verifies project-specific fixtures.
