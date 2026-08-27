# Troubleshooting

## Purpose

Read this for cross-cutting REINVENT4 install, import, CLI, backend, and config failures. Workflow-specific failures live in the nearest sub-skill troubleshooting reference.

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` when importing `reinvent` | Package source is on `PYTHONPATH` but runtime dependencies are not installed. | Install REINVENT4 into a Python 3.11+ environment with a PyTorch wheel matching the backend, then rerun `python scripts/check_reinvent_install.py`. |
| `ModuleNotFoundError: No module named 'scipy'` from `reinvent.runmodes.utils.plot` while running `reinvent --help` | At this snapshot, plotting code imports `scipy.stats.gaussian_kde`, but `scipy` is not declared in the package metadata. | Install `scipy`, rerun `reinvent --help`, and record the metadata gap if preparing a reproducible environment. |
| `pip check` reports Torch/TorchVision conflicts | Torch and TorchVision wheels do not match each other or the selected backend index. | Reinstall matching wheels from the official PyTorch CPU/CUDA/ROCm/XPU/MPS route before reinstalling REINVENT4. |
| RDKit import or molecule parsing fails | Missing or incompatible RDKit wheel/conda package. | Use Python 3.11+ and install a compatible `rdkit` build; prefer conda-forge or the package metadata route when pip wheels are unavailable. |

## Backend And Device Issues

- `--device cpu` overrides config files and is the safest smoke-check default.
- `--device cuda:0` only works when the installed PyTorch build can see a compatible NVIDIA GPU and driver.
- A GPU in the machine is not enough; the PyTorch wheel must match the driver-supported CUDA runtime.
- Do not launch long sampling, TL, RL, or enumeration jobs just to test backend availability. First run `reinvent --help`, then a bundled static validator, then a tiny CPU smoke job.

## Optional Extras

| Optional surface | Requirement | Practical fallback |
| --- | --- | --- |
| OpenEye ROCS | `openeye` extra, OpenEye package index, and license. | Use RDKit or similarity components when ROCS is not licensed. |
| ChemProp v1/v2 | Install exactly one of `chemprop1` or `chemprop2`; they conflict. | Validate scoring config structure and skip actual model scoring until dependencies/model files are available. |
| iSIM tracking | Git-based `isim` extra. | Disable iSIM/TensorBoard similarity tracking when network/git install is not allowed. |
| ExternalProcess, REST, DockStream, Icolos, Maize, Qptuna, SynthSense | External executables, services, config files, credentials, or model artifacts. | Treat as integration work; validate config shape but do not call services without approval. |

## Config Parse Problems

- Use TOML for most tasks; force JSON/YAML with `reinvent -f json config.json` or `reinvent -f yaml config.yaml` only when needed.
- Confirm the top-level `run_type` routes to the intended sub-skill.
- Keep path values relative to the directory where the run will be launched, or use explicit absolute paths in the user's runtime project.
- Validate with bundled scripts before running expensive jobs:
  - `sub-skills/sampling/scripts/validate_sampling_config.py`
  - `sub-skills/scoring/scripts/validate_scoring_config.py`
  - `sub-skills/learning/scripts/check_learning_config.py`
  - `sub-skills/data-pipeline/scripts/validate_data_pipeline_config.py`
  - `sub-skills/enumeration/scripts/validate_seed_files.py`

## When To Stop

Stop and ask before running commands that require proprietary licenses, private model/data downloads, external scoring services, network-heavy installs, GPU-only workloads, or long TL/RL training. Static validation and `--help` checks are safe; full molecular design runs may write files, consume compute, or call external systems.
