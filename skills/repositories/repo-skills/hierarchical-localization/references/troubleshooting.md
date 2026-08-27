# Cross-cutting HLoc troubleshooting

Use this reference for install/import, optional dependency, backend, pycolmap/COLMAP, model-download, and artifact-path failures that can affect multiple sub-skills. For workflow-specific failures, load the nearest sub-skill troubleshooting file.

## Fast public diagnostics

Run the bundled environment helper in the user's active Python environment:

```bash
python scripts/check_hloc_environment.py --check-cli
python scripts/check_hloc_environment.py --json --check-cli
```

Expected healthy signals:

- `hloc` imports and reports version `1.5` or the user's installed version.
- `pycolmap`, `torch`, `cv2`, `h5py`, `kornia`, and optional `lightglue` imports are visible when the selected workflows need them.
- Core parser checks such as `python -m hloc.extract_features --help` and `python -m hloc.reconstruction --help` exit successfully.
- CUDA may be available, but HLoc does not require CUDA for parser/import/data-format checks. CUDA mainly accelerates learned feature extraction and matching.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'hloc'` | Package is not installed in the active environment. | Install the distribution in the environment used by the agent/task: `python -m pip install -e <checkout>` for local development, or the user's chosen package source. Then rerun `python -c "import hloc; print(hloc.__version__)"`. |
| `hloc requires pycolmap>=...` warning or `No module named 'pycolmap'` | Missing or old pycolmap. | Install/upgrade `pycolmap` compatible with the user's Python/platform. Parser checks for reconstruction/localization require `pycolmap`; full mapping/localization needs it. |
| `No module named 'lightglue'`, `kornia`, `gdown`, or extractor-specific imports | Optional learned frontend dependency missing or not installed from runtime requirements. | Use a built-in config whose dependencies are installed, install the missing runtime dependency, or export external HDF5 features/matches and route to `custom-interop`. |
| `pip check` reports broken requirements | Mixed package versions or an interrupted install. | Repair in an isolated environment rather than mutating a shared environment. Verify imports and CLI help after repair. |

## Model weight and network failures

Learned extractors/matchers can download model weights on first use. Symptoms include HTTP errors, cache permission errors, or long stalls before any image processing.

Recovery:

1. Confirm the task actually requires learned model execution rather than parser/config inspection.
2. If network is unavailable, use already-cached weights, a config whose weights are present, a classical feature config such as `sift`/`sosnet` when appropriate, or external HDF5 artifacts.
3. If a download was interrupted, clear only the corrupted cache file, not unrelated user caches.
4. Do not run dataset-scale extraction as a smoke test. Use CLI `--help`, config inspection, and tiny user-provided fixtures first.

## CPU/GPU backend confusion

HLoc chooses `cuda` for many learned models only when `torch.cuda.is_available()` is true; otherwise it uses CPU. This means:

- A CPU-only environment can still validate parser/import/data contracts and can run small operations, but learned extraction/matching may be slow.
- CUDA availability is a performance/backend capability, not proof that dataset pipelines will succeed.
- CUDA import errors often come from an incompatible torch wheel, missing driver passthrough, or mismatched CUDA runtime. Use `python scripts/check_hloc_environment.py --json` to record torch and CUDA facts before changing packages.
- If the user explicitly requests GPU-speed extraction/matching, verify a tiny tensor allocation and a tiny model-specific run with available weights before launching a large pipeline.

## pycolmap and COLMAP model failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `assert reference_model.exists()` or missing `images.bin`/`cameras.bin` | Wrong SfM model folder or text/binary conversion mismatch. | Confirm the model directory contains a pycolmap-readable reconstruction. For mapping inputs, route to `mapping-localization` data contracts. |
| `No images found` during reconstruction import | `image_dir` is empty or image names in lists do not match files. | Validate image directories and lists before importing. Avoid absolute image names inside lists unless the user intentionally uses them. |
| Unknown option in `--image_options` or `--mapper_options` | Option key does not exist in the pycolmap options object or value type is wrong. | Use `python -m hloc.reconstruction --help` to list available option keys and pass values as `key=value`; booleans must be Python literals such as `False`. |
| Geometric verification or mapping returns no reconstruction | Too few/poor matches, bad pairs, wrong camera intrinsics, incompatible image names, or scene not reconstructible. | Validate features/matches/pairs; try better pairs, different matcher config, known intrinsics, or inspect match inliers before rerunning expensive mapping. |

## Artifact naming failures

HLoc uses the same relative image names across image lists, HDF5 groups, pair files, COLMAP models, and pose outputs. Common issues:

- Image names contain spaces, but parsers split on whitespace.
- Feature files use `folder/image.jpg`, while pair files use `image.jpg`.
- Match group names use the wrong pair separator or legacy format.
- Query list names do not match retrieval pairs.
- Retrieved database images are absent from the reference model.

Use the validators in `sub-skills/mapping-localization/scripts/` and `sub-skills/custom-interop/scripts/` before rerunning feature extraction, matching, or localization.

## Dataset-scale safety

Aachen, InLoc, 4Seasons, 7Scenes, CMU, Cambridge, and RobotCar workflows require external datasets, large output folders, and often downloaded model weights. Do not launch these pipelines as a routine verification step. Load `sub-skills/dataset-pipelines/` to plan prerequisites, expected files, outputs, and safe parser checks.
