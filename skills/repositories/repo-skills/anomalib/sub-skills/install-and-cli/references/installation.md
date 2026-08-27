# Installation

## Purpose

Read this when deciding how to install Anomalib, whether to use `anomalib install`, and how to choose between CPU and OpenVINO support.

## When to read

- A user wants the smallest command that gives them CPU plus OpenVINO support.
- A user asks whether to use `anomalib install` or a direct `pip`/`uv` install.
- A user wants an editable source install for local development.
- A user is confused by `full`, `core`, `dev`, `loggers`, `notebooks`, or `openvino`.

## Verified install paths

| Situation | Recommended command | Why |
| --- | --- | --- |
| Fresh CPU runtime from PyPI | `uv pip install "anomalib[cpu]"` or `pip install "anomalib[cpu]"` | Installs the package with the CPU torch/torchvision wheel set. |
| Fresh CPU + OpenVINO runtime from PyPI | `uv pip install "anomalib[cpu,openvino]"` or `pip install "anomalib[cpu,openvino]"` | Smallest runnable install for CPU inference plus OpenVINO export/inference. |
| Editable source install on CPU | `uv sync --extra cpu` or `pip install -e ".[cpu]"` | Best for local edits and contributor workflows. |
| Editable source install on CPU + OpenVINO | `uv sync --extra cpu --extra openvino` or `pip install -e ".[cpu,openvino]"` | Keeps the checkout editable while enabling OpenVINO paths. |
| Add optional bundles inside an already working environment | `anomalib install --option openvino` | Adds optional packages after Anomalib is already installed. |

## Direct package install versus `anomalib install`

Use `pip` or `uv` when you need to bootstrap a new environment or choose the backend wheel.

Use `anomalib install` when Anomalib is already installed and you want to add an optional bundle such as:

- `full` for the broad optional feature set;
- `dev` for docs and test tooling;
- `loggers` for experiment tracking;
- `notebooks` for notebook support;
- `openvino` for OpenVINO packages.

Do not treat `anomalib install` as the backend selector. The backend selector is the package extra you choose during `pip`/`uv` installation.

## Backend selection notes

- `cpu` is the default backend route for runnable CPU setups.
- `openvino` should usually be combined with `cpu` for a fresh install: `anomalib[cpu,openvino]`.
- If you need a different hardware backend, choose the matching package extra from the project metadata rather than relying on `anomalib install`.
- `full` and `dev` are bundle extras; pair them with the hardware extra that matches the host.

## Common install choices

- `pip install anomalib` or `uv pip install anomalib`: general-purpose package install when you are happy with the installer defaults.
- `pip install "anomalib[cpu]"` or `uv pip install "anomalib[cpu]"`: explicit CPU runtime.
- `pip install "anomalib[cpu,openvino]"` or `uv pip install "anomalib[cpu,openvino]"`: CPU runtime plus OpenVINO support.
- `pip install -e ".[cpu]"`: editable source install for contributors.
- `pip install -e ".[cpu,openvino]"`: editable source install with OpenVINO support.
- `anomalib install -v`: verbose install logging, not help verbosity.

## What the install options mean

| Install option | Meaning | Notes |
| --- | --- | --- |
| `full` | Broad optional dependency bundle | Large footprint; useful when you need most extras. |
| `core` | Core package dependencies | Not a backend selector; do not use it instead of `cpu`. |
| `dev` | Full bundle plus docs/test tooling | Best for local development environments. |
| `loggers` | Logging integrations | Adds experiment tracking packages. |
| `notebooks` | Notebook support | Adds Jupyter-related packages. |
| `openvino` | OpenVINO packages | Adds OpenVINO, NNCF, ONNX, and ONNXScript. |

## Bundled helper

- Run [scripts/cli_recipes.sh](../scripts/cli_recipes.sh) with the `install` section to print copyable install commands without mutating the environment.
