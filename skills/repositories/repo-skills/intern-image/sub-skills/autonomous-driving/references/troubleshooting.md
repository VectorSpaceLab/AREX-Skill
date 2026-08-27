# Autonomous-Driving Troubleshooting

## Purpose

Use this when an autonomous-driving InternImage workflow fails before or during command planning, data validation, schema conversion, or OpenLane-V2 evaluation. These remedies are self-contained and route to bundled helpers where possible.

## Quick triage

1. Decide which baseline is involved: `occupancy`, `hd-map`, or `openlane`.
2. Generate the command without executing it:

   ```bash
   python <SKILL_DIR>/scripts/build_autonomous_command.py --baseline openlane --mode test --help
   ```

3. If the failure is an OpenLane-V2 submission/schema issue, run:

   ```bash
   python <SKILL_DIR>/scripts/validate_openlanev2_submission.py <submission.json> --json-report
   ```

4. If the failure is DCNv3, CUDA, TensorRT, or OpenMMLab installation rather than autonomous data/schema semantics, route to the sibling deployment guidance.

## Failure map

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: mmdet3d`, `mmcv`, `mmdet`, or `mmseg` | The selected baseline needs an OpenMMLab/mmdet3d stack that was not installed. Version families differ by baseline. | Do not run generated commands until the correct stack is installed. Occupancy is mmdet3d 0.18.x-era; HD map and OpenLane-V2 are mmdet3d 1.0.0rc6-era. |
| `ModuleNotFoundError: DCNv3`, custom op import failure, or CUDA extension build failure | InternImage backbones in these baselines use DCNv3. The compiled extension is missing or incompatible. | Confirm CUDA toolkit/compiler availability and PyTorch CUDA compatibility before building. If the task is only schema validation or command planning, skip model execution and use the bundled scripts. |
| Distributed run hangs at launch or each process reports wrong rank | `--gpus`, `--port`, `--nnodes`, `--node-rank`, or `--master-addr` do not match the actual launch environment. | Regenerate the command with explicit `--gpus`, `--port`, and cluster options. Do not mix Slurm wrappers with `torch.distributed.launch` unless the cluster policy requires it. |
| HD-map config tries to read unavailable annotation/image roots | The selected VectorMapNet config carried site-specific data placeholders in source. | Pass `--cfg-option` overrides in the command builder for train-time config keys, or create a local config copy with correct annotation and image roots. Never assume source placeholder paths are valid. |
| Occupancy config cannot find `occ_infos_temporal_train.pkl` or `occ_infos_temporal_val.pkl` | Occ3D/nuScenes data conversion has not been run, or output names differ from the config. | Prepare the documented `data/occ3d-nus` layout and run the data conversion equivalent before training/evaluation. Then point the config to the produced pickle names. |
| OpenLane-V2 `Collection` raises `Please run the preprocessing first` | The collection pickle named by `meta_root` and `collection` is missing. | Preprocess downloaded OpenLane-V2 split JSON into collection pickle files, then make sure `data_root`, `meta_root`, and `collection` agree. |
| OpenLane-V2 dataset assertion says the first image should be front view | The frame metadata camera order does not begin with `ring_front_center`, but the plugin rendering/evaluation code assumes it. | Inspect generated metadata order and conversion logic before model execution. Do not patch downstream metrics until the data order is correct. |
| `Type of value in key ... should be np.ndarray` from the upstream devkit | Upstream `check_results` expects NumPy arrays, while JSON loaders produce lists. | Use the bundled JSON validator first. Convert JSON lists to arrays only at the stage where a Python pickle submission or devkit evaluation is intentionally produced. |
| Bundled validator reports `topology_lclc` shape mismatch | Lane-lane topology matrix is not `#lanes x #lanes` for that frame. | Count the frame's `lane_centerline` predictions and rebuild the square adjacency matrix in the same order. |
| Bundled validator reports `topology_lcte` shape mismatch | Lane-traffic topology matrix is not `#lanes x #traffic_elements`. | Count lane and traffic predictions after any filtering/sorting. Rebuild rows in lane order and columns in traffic order. |
| Bundled validator reports duplicate IDs | IDs are duplicated across lane and traffic predictions in a frame. | Reassign unique IDs per frame. Source formatting used separate ID ranges for lanes and traffic to avoid collisions. |
| Bundled validator reports country/region invalid | Metadata field is missing, placeholder-like, or not accepted by `iso3166` when available. | Use an ISO 3166 country name or alpha code. If `iso3166` is not installed, the bundled validator performs a conservative fallback check only. |
| `authors` accepted locally but upload fails | The upstream checker caps authors at 10 and requires a list. | Keep `authors` as a list of strings with at most 10 entries. |
| OpenLane-V2 evaluation import fails with `cannot import name 'check_results' from 'openlanev2.preprocessing'` | In the inspected checkout, `openlanev2/evaluation/evaluate.py` imports `check_results` from the preprocessing package initializer, but that initializer is empty. | Work around by importing `openlanev2.preprocessing.check.check_results` directly for validation. For full evaluation, patch/export `check_results` in the package initializer or patch the evaluation import to target `openlanev2.preprocessing.check`; record the patch in experiment notes before comparing metrics. |
| OpenLane-V2 `--eval-options dump=True` does not write `result.pkl` | `dump_dir` was omitted or unwritable, evaluation did not reach dataset.evaluate, or the source formatter still emits dummy metadata that fails the submission check. | Regenerate the openlane test command with `--dump-dir <dir>`, ensure the directory is writable, and patch/fill the submission metadata so `country / region` and other required fields are valid before retrying. |
| Test-set evaluation refused | Some scripts allow formatting test predictions but do not evaluate hidden test labels. | Use `--operation format` for hidden test split workflows and evaluate only validation split outputs locally. |
| Metric values are poor despite valid schema | Shape validation does not verify semantic quality, coordinate frames, camera order, or object ordering. | Check point coordinate convention, lane/traffic ordering, topology confidence thresholding, and whether predictions were sorted/filtered before matrices were built. |

## Known OpenLane-V2 import issue

Environment inspection showed:

- Direct root import of `openlanev2` works.
- Direct import of `openlanev2.preprocessing.check.check_results` works.
- Direct import of `openlanev2.evaluation.evaluate` fails in this checkout because evaluation imports `check_results` from an empty preprocessing package initializer.
- The same empty initializer also breaks the preprocessing helper path that tries to import `collect` from `openlanev2.preprocessing`.

Do not claim full OpenLane-V2 evaluation is verified until this import issue is patched and a small evaluation fixture or real validation subset is run. The bundled validator intentionally avoids this problem by implementing JSON checks without importing OpenLane-V2.

## Data and submission quality checklist

Before expensive GPU execution or upload:

- Metadata fields are present: `method`, `authors`, `e-mail`, `institution / company`, `country / region`, and `results`.
- Each frame has `predictions` with lane, traffic, and both topology matrices.
- Lane points are 3D polylines; traffic points are 2D boxes.
- IDs are unique per frame across lanes and traffic elements.
- Topology matrices match the exact object counts and ordering after final filtering.
- Confidence-like values are finite and normally in `[0, 1]`.
- Country/region metadata is not a placeholder.
- For full evaluation, data collection pickles and image paths exist, and the OpenLane-V2 evaluation import issue has been resolved.

## When to stop

Stop instead of launching a command when required large datasets, checkpoints, CUDA GPUs, DCNv3 build, write permissions, or challenge data-use terms are unresolved. The bundled helpers can still be used for command planning and JSON schema validation under CPU-only conditions.
