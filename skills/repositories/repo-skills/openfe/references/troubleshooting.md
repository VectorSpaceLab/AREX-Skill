# Cross-Cutting Troubleshooting

Read this before routing into a workflow-specific troubleshooting page when the symptom spans install, import, CLI startup, OpenMM, CUDA, logging, or analysis warnings.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: openfe` | OpenFE is not installed in the active environment. | Install or activate a conda/OpenFE environment, then run the minimal import check in [Installation and Environment](installation-and-environment.md). |
| `ModuleNotFoundError` for chemistry packages | A required or optional dependency family is missing. | Use the documented OpenFE conda environment or container route; do not try to repair compiled chemistry stacks with ad hoc pip installs unless the user explicitly accepts that risk. |
| `openfe: command not found` but imports work | Console script is missing from PATH or the package was not installed as an application. | Run `python -m pip show openfe` and reinstall in the intended environment, or call Python APIs directly for planning tasks. |
| CLI starts but subcommands are missing | Plugin loading or `openfecli` installation issue. | Reinstall OpenFE in a clean environment and run `openfe --help`; if editing a checkout, confirm editable install completed after dependency environment creation. |

## OpenMM and GPU Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CUDA_ERROR_UNSUPPORTED_PTX_VERSION` or CUDA module load errors | OpenMM CUDA toolkit/wheel is incompatible with the host driver. | Recreate the environment with a CUDA/OpenMM build compatible with the target compute node; validate on the node that will run the job. |
| OpenMM platform not found | The selected platform is unavailable in the environment. | Use the [protocols](../sub-skills/protocols/SKILL.md) guidance to inspect platform settings and choose a supported platform or fix the environment. |
| Job works on login node but fails in scheduler | Login and compute nodes differ in driver, GPU, modules, or container visibility. | Validate inside the submitted job context; prefer containerized OpenFE on heterogeneous HPC systems. |
| Slow or noisy debug logging | Debug logging is enabled for production simulation. | Use debug logging only while diagnosing failures and return to normal logging for production runs. |

## PyMBAR and JAX Warnings

OpenFE sets `PYMBAR_DISABLE_JAX=TRUE` by default unless the user already set it. This avoids suspected memory issues in PyMBAR/JAX analysis. A JAX warning about a GPU or CPU fallback concerns PyMBAR analysis, not necessarily OpenMM simulation platform selection.

If a user asks to enable PyMBAR JAX acceleration, make them aware that it can increase memory risk and should be tested on the target hardware.

## Logging

For `quickrun`, the logging config is a global OpenFE CLI option and must appear before the subcommand:

```bash
openfe --log debug_logging.conf quickrun transformation.json -d workdir -o results.json
```

Route cache/resume behavior to [cli-workflows](../sub-skills/cli-workflows/SKILL.md), protocol/backend details to [protocols](../sub-skills/protocols/SKILL.md), planning-data failures to [network-planning](../sub-skills/network-planning/SKILL.md), and missing result estimates or partial gathers to [results-analysis](../sub-skills/results-analysis/SKILL.md).

## Safe Diagnostic Helper

Use [check_openfe_environment.py](../scripts/check_openfe_environment.py) for a local, read-only environment report. It imports packages, checks CLI help, reports OpenMM platforms when available, and detects common optional dependency gaps without running simulations or uploading data.
