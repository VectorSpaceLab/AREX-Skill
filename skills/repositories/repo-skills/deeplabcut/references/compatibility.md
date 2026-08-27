# DeepLabCut compatibility notes

Read this before choosing a backend, optional extra, or execution device.

## Engine selection

DeepLabCut 3.x defaults to the PyTorch engine. The public compatibility layer routes high-level APIs such as `train_network`, `evaluate_network`, `analyze_videos`, and `export_model` to either PyTorch or TensorFlow based on the project's shuffle metadata or an explicit `engine` argument.

Use PyTorch for new projects unless the user has a legacy TensorFlow project or a documented TensorFlow-only requirement.

## PyTorch backend

Use PyTorch for:

- standard single-animal projects;
- multi-animal projects including top-down, bottom-up, and CTD/BUCTD workflows;
- modern model architectures and configuration through `pytorch_config.yaml`;
- most new training, evaluation, and video analysis.

Common device choices:

| Device | Use when | Notes |
| --- | --- | --- |
| `cpu` | Config checks, tiny tests, package inspection, or machines without accelerators. | Real training/video analysis is usually slow. |
| `cuda:0` or another CUDA device | NVIDIA GPU training/inference. | Verify `torch.cuda.is_available()` and memory before real runs. |
| `mps` | Apple Silicon PyTorch workflows. | Support depends on installed PyTorch and operation coverage. |
| `auto` | Some Model Zoo workflows. | Still confirm what backend was selected before assuming performance. |

## TensorFlow legacy backend

TensorFlow support remains for legacy projects but should be treated as optional and version-sensitive. Install exactly one TensorFlow extra per environment. Do not combine `tf`, `tf-cu11`, `tf-cu12`, `tf-latest`, or `apple_mchips`.

Before changing a TensorFlow environment, confirm:

- Python version;
- operating system;
- CUDA/driver/cuDNN or macOS Metal expectations;
- whether the project has existing TensorFlow model outputs under `dlc-models/`;
- whether PyTorch packages in the same environment would be downgraded or made incompatible.

## GUI and headless mode

The GUI requires the `gui` extra. Headless installs are valid for API and scripted workflows but `python -m deeplabcut` or `dlc` will print a lite notice instead of launching the GUI if GUI dependencies are absent.

Use GUI only when the task actually involves interactive project management, labeling, refinement, or visual inspection. For automation, prefer Python API recipes from the sub-skills.

## Model Zoo and FMPose3D

SuperAnimal inference can use pretrained weights and may require network/model-cache access unless the user provides local checkpoints. FMPose3D is an optional monocular 3D path that needs the `fmpose3d` extra and model-specific requirements; it is separate from DeepLabCut's ordinary multi-camera 3D triangulation.

## OpenVINO

The `openvino` extra supports OpenVINO-related inference paths. Confirm the user's OpenVINO runtime, platform, and `use_openvino` expectations before installing or promising acceleration.

## W&B logging

W&B logging is optional. Do not enable or configure it without user approval because it may require credentials, project names, network access, and experiment tracking policy.

## Data and output compatibility

DeepLabCut projects may contain both legacy TensorFlow and PyTorch output trees:

- `dlc-models/` for TensorFlow model outputs.
- `dlc-models-pytorch/` for PyTorch model outputs.
- `training-datasets/` for generated train/test datasets and metadata.
- analyzed video prediction files as `.h5` and optional `.csv`.
- filtered predictions with filtered suffixes.
- tracklets/stitched tracks for multi-animal workflows.

Do not mix outputs from different engines, shuffles, track methods, or model prefixes unless the workflow reference explicitly explains the handoff.
