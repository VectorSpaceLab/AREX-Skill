# Cross-cutting DeepLabCut troubleshooting

Start here for install, import, launcher, backend, and path problems. Then route to the workflow-specific troubleshooting file named by the relevant sub-skill.

## Import or install fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: deeplabcut` | Package is not installed in the active environment. | Install with `pip install deeplabcut` in the environment that will run the workflow, then run the root install check script. |
| Dependency resolver downgrades torch or TensorFlow unexpectedly | Optional extras or backend variants conflict. | Install only the required extra. Do not mix TensorFlow extras. Prefer a fresh environment for TensorFlow legacy projects. |
| Python version error or wheel not found | Python is outside supported range or a compiled dependency lacks wheels. | Use Python 3.10, 3.11, or 3.12. Avoid Python versions newer than the package metadata supports. |
| Import succeeds in a checkout but not elsewhere | Current directory is shadowing the installed distribution. | Re-run import checks from a neutral directory and inspect distribution metadata. |

## GUI or launcher confusion

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dlc --help` prints a lite install message instead of command help | In this version, `dlc` invokes the GUI/lite launcher path, not the click command group. | Use the Python API recipes in the sub-skills, or verify any CLI entry point exposed by the user's install before relying on it. |
| `python -m deeplabcut` says GUI cannot be used | GUI dependencies such as PySide6 are missing. | Install `deeplabcut[gui]` only if GUI work is required. Headless API workflows can continue without it. |
| GUI fails on a remote or headless machine | No display/Qt backend or GUI extra unavailable. | Use API workflows, notebooks with appropriate display support, or run GUI on a workstation. |

## Backend and performance problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training/inference is extremely slow | CPU backend is being used for a real workload. | Verify PyTorch device availability and choose `device="cuda:0"`, `mps`, or another supported backend if available. |
| `torch.cuda.is_available()` is false on a GPU machine | CPU-only torch, incompatible driver/wheel, or container GPU passthrough missing. | Install a PyTorch wheel compatible with the driver and confirm the device with a tiny tensor allocation before DeepLabCut training. |
| TensorFlow and PyTorch packages conflict | Legacy TensorFlow extra pinned incompatible torch/toolkit versions. | Use a separate environment for TensorFlow workflows or stay on PyTorch for new projects. |
| GPU out-of-memory | Batch size, detector batch size, image size, model, or video count is too large. | Lower `batch_size`, `detector_batch_size`, input sizes, or run fewer videos in parallel; use model-specific troubleshooting in the PyTorch sub-skill. |

## Project path and data problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Project config path points to an old location | Project was moved or copied. | Use the project setup summary script to inspect mismatch, then edit `project_path` only after confirming the intended project root. |
| Video path no longer exists | Original videos were symlinked or moved. | Decide whether to restore source videos, update `video_sets`, or copy videos into the project. On Windows, symlink creation may need administrator privileges. |
| `labeled-data` or trainset files are missing | Frame extraction/labeling/trainset creation has not run or wrote to another project path. | Route to `data-labeling-and-training-datasets` and validate the folder/table layout before training. |
| Analyzed `.h5` exists but post-processing cannot find it | Wrong `destfolder`, `shuffle`, `trainingsetindex`, `modelprefix`, `track_method`, or filtered/unfiltered expectation. | Route to `postprocessing-3d-video-exports` or `multi-animal-tracking` and align all naming parameters. |

## Safe next diagnostic

Run the root check script for an environment-level snapshot:

```bash
python scripts/check_deeplabcut_install.py --check-torch --check-launcher
```

Run the project setup summary script for a project-level snapshot:

```bash
python sub-skills/install-and-project-setup/scripts/summarize_dlc_project.py /path/to/project-or-config.yaml
```

Both scripts are read-only.
