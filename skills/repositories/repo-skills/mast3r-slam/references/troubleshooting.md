# Cross-cutting Troubleshooting

## When to read

Read this when the symptom could involve install/build, checkpoints, CUDA,
input data, configs, visualization, or evaluation. Then follow the nearest
sub-skill reference for deeper recovery steps.

## Fast routing table

| Symptom | Likely owner | First action |
| --- | --- | --- |
| `CUDA not found, cannot compile backend!`, missing `mast3r_slam_backends`, or `cuda_runtime.h` missing | `setup-and-backends` | Read `sub-skills/setup-and-backends/references/troubleshooting.md` and verify `nvcc` plus CUDA headers, not just `torch.cuda.is_available()`. |
| `undefined symbol: iJIT_NotifyEvent` while importing torch | `setup-and-backends` | Repair MKL/OpenMP compatibility; do not debug MASt3R-SLAM source first. |
| `ModuleNotFoundError: torch` while building `curope` or another local extension | `setup-and-backends` | Re-run editable third-party install with build isolation disabled after torch is installed. |
| `ModuleNotFoundError: dust3r` in a custom snippet | `setup-and-backends` / `run-slam` | Import `mast3r.utils.path_to_dust3r` before direct Dust3R imports, or use MASt3R-SLAM helpers that do this. |
| Checkpoint filenames missing or `from_pretrained` cannot load weights | `setup-and-backends` | Use the checkpoint manifest; verify three MASt3R retrieval/model assets. |
| `No calibration provided for this dataset!` | `run-slam` | Use a dataset with built-in calibration, provide `--calib`, or switch to a no-calibration config. |
| The process opens no window, crashes on GLFW/OpenGL, or hangs in display-less CI | `run-slam` | Use `--no-viz`; visualization is optional for headless runs. |
| `load_dataset` chose the wrong dataset type | `run-slam` | Check path tokens and layout using `validate_inputs.py`; path substrings drive dataset class selection. |
| `evo_ape` cannot find trajectory or groundtruth files | `evaluation` | Verify the suite log/groundtruth path with `plan_evaluation.py` and `metrics-and-outputs.md`. |
| Download scripts would fetch many large archives | `evaluation` | Use `plan_downloads.py` first and ask for explicit approval before network downloads. |

## Non-substitutable checks

These checks are useful but do not prove the primary SLAM backend:

- `python main.py --help`: proves imports and parser surface only.
- `load_config` / `load_dataset` synthetic folder smoke: proves helper behavior only.
- CPU import of `mast3r_slam`: does not prove MASt3R inference, lietorch, or
  custom CUDA kernels work.

For a full readiness claim, require a CUDA import/allocation and
`mast3r_slam_backends` import, then run a real or approved tiny SLAM case with
checkpoints and input data.

## Safe diagnostic command

Run this bundled script in the target Python environment:

```bash
python scripts/check_install.py --check-cuda
```

Add `--checkpoint-dir <dir>` when diagnosing asset failures. The script reports
missing optional components as warnings, and returns non-zero for failed required
imports or failed CUDA checks.
