# Cross-cutting Troubleshooting

## Import and dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: mmengine`, `mmcv`, or `mmdet` | OpenMMLab base stack missing. | Install with MIM using versions compatible with MMDetection3D 1.4.x. |
| `ImportError` or undefined symbol from `mmcv.ops` | PyTorch, CUDA, and MMCV wheel mismatch. | Reinstall MMCV from the OpenMMLab wheel index for the exact PyTorch/CUDA combination. |
| `ModuleNotFoundError: numba`, `nuscenes`, `open3d`, `lyft_dataset_sdk` | Runtime requirements not installed. | Install MMDetection3D runtime requirements or the public package with dependencies. |
| NumPy ABI warning from PyTorch or compiled deps | Mixed NumPy 2.x with modules built against NumPy 1.x. | Prefer a NumPy version supported by the selected PyTorch/MMCV stack; rerun import checks. |
| `spconv`, MinkowskiEngine, or TorchSparse missing | Selected model config requires optional sparse backend. | Install only the backend required by the config; do not treat a CPU import as proof of backend support. |

## Config/checkpoint/data coupling

- A config, checkpoint, dataset classes/metainfo, coordinate mode, and evaluator must match. Wrong pairings often fail later as tensor shape mismatches, missing keys, wrong class labels, empty predictions, or metric errors.
- If a user changes `data_root`, class names, or annotation paths, also inspect train/val/test dataloaders, evaluator `ann_file`, metainfo, pipelines, and any `db_sampler` paths.
- If `--cfg-options` uses nested values, preserve shell quoting around lists/dicts/tuples.
- If `work_dir` is omitted, MMDetection3D derives one from the config name. Set it explicitly for reproducible jobs.

## Data preparation failures

- Missing `ImageSets`, `velodyne`, `samples`, `sweeps`, `sequences`, or info pickles usually means raw dataset layout and generated annotation layout were confused.
- Full dataset conversion can be slow, storage-heavy, and SDK-specific. Use the data-preparation sub-skill to plan conversion and validate layout before running it.
- Waymo conversion can stall with too many workers or insufficient local disk. Reduce worker count, ensure TensorFlow/Waymo dependencies are installed, and write output to a large enough directory.
- Old v1.0 information pickles may need an update step before using v1.4.x configs.

## Runtime and visualization failures

- On remote servers, do not force interactive visualizers. Save predictions/visualizations to an output directory instead of using `--show`.
- Open3D/GUI errors usually indicate no display, missing GL libraries, or headless runtime constraints. Prefer non-interactive saved outputs.
- Empty or invalid visualizations can come from score thresholds, wrong task type, wrong coordinate mode, or mismatched camera calibration.

## Training/evaluation failures

- CPU training/testing is experimental. Most point-cloud models require CUDA-backed ops; use CPU only for narrow debugging paths.
- Distributed jobs on the same machine need distinct `PORT` values and non-overlapping `CUDA_VISIBLE_DEVICES`.
- `--show`/`--show-dir` evaluation visualization requires the correct visualization task type.
- Waymo, KITTI, NuScenes, and Lyft submission/evaluation outputs use different evaluator fields and artifacts. Use the training-evaluation sub-skill before rendering commands.

## Safe next steps

- Use the root environment checker for import/backend facts.
- Use the configuration checker before changing configs.
- Use dataset layout and command builders before conversion.
- Use command builders before launching long train/test/serve jobs.
- Stop and ask the user before downloads, full conversions, checkpoint-backed inference, GPU training/evaluation, Docker/TorchServe, or Slurm submissions.
