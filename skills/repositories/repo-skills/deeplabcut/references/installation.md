# DeepLabCut installation and entry points

Read this when a task is about installing DeepLabCut, choosing extras, verifying the package, or understanding why a launcher did not show the GUI.

## Python and base install

DeepLabCut 3.0.1 declares Python support for 3.10 through 3.12. Use an isolated environment for real projects because DeepLabCut pulls in compiled scientific, video, PyTorch, and optional GUI/backend packages.

Typical headless install for API workflows:

```bash
pip install deeplabcut
python - <<'PY'
import deeplabcut
print(deeplabcut.__version__)
PY
```

GUI install when the user needs the Project Manager or labeling/refinement GUI:

```bash
pip install "deeplabcut[gui]"
python -m deeplabcut
```

For GPU acceleration, install a PyTorch build compatible with the user's CUDA driver or platform before or alongside DeepLabCut, following the official PyTorch selector. A CPU install can inspect configs and run small checks, but real training and video analysis are usually slow without a GPU.

## Optional extras

| Extra | Use when | Notes |
| --- | --- | --- |
| `gui` | Project Manager, frame labeling, refinement GUI, or napari integration. | Adds Qt/PySide-related dependencies; headless installs print a lite message. |
| `tf` | Legacy TensorFlow engine with default supported TensorFlow range. | TensorFlow is legacy and planned for deprecation; do not install unless the project needs it. |
| `tf-cu11` | Legacy TensorFlow pinned for older CUDA 11-era stacks. | Do not combine with other TensorFlow extras. |
| `tf-cu12` | Legacy TensorFlow pinned for CUDA 12-era stacks. | Do not combine with other TensorFlow extras. |
| `tf-latest` | Experimental/newer TensorFlow. | Not the default recommendation. |
| `apple_mchips` | Older macOS Apple Silicon TensorFlow workflows. | Prefer `tf` for new TensorFlow installs when supported. |
| `openvino` | OpenVINO inference path. | Requires OpenVINO-specific compatibility checks. |
| `fmpose3d` | FMPose3D monocular 3D model-zoo path. | Optional and not needed for ordinary DLC 3D triangulation. |
| `wandb` | Weights & Biases logging. | Requires user/project logging policy. |

## Entry points and launchers

- `python -m deeplabcut` and the installed `dlc` console script use the GUI/lite launcher path.
- If GUI dependencies are present, the launcher starts the DeepLabCut GUI.
- If GUI dependencies are missing, the launcher prints a lite-install message telling the user to install the GUI extra.
- The package also has a `deeplabcut.cli` click command group with workflow commands such as `create-new-project`, `extract-frames`, `train-network`, `evaluate-network`, and `analyze-videos`; however, this click group is not the package's installed `dlc` console entry point in this version.
- For automation, prefer the Python API shown in the sub-skills unless the user's installation exposes and verifies a CLI command for the desired action.

## Safe verification checklist

Use the bundled root script for a no-side-effect probe:

```bash
python scripts/check_deeplabcut_install.py --check-torch
```

Expected signs of a usable headless install:

- `import deeplabcut` succeeds.
- `deeplabcut.__version__` is visible.
- Core exports such as `create_new_project`, `create_training_dataset`, `train_network`, `evaluate_network`, and `analyze_videos` are present.
- PyTorch imports if the task will use the default DeepLabCut 3.x engine.
- CUDA, MPS, or CPU backend status is explicit before training or inference is planned.

## When to stop and ask

Ask before installing or changing packages if:

- the user provided an existing environment that might be broken by upgrades or downgrades;
- the task requires a TensorFlow extra but the desired CUDA/Python version is unclear;
- the task requires GUI or model downloads on a headless/offline machine;
- a GPU workflow is required but no compatible backend is visible;
- the user wants OpenVINO, FMPose3D, or W&B integration and has not approved the additional dependency or credential expectations.
