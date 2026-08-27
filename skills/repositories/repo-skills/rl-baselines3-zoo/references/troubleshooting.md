# Cross-cutting troubleshooting

## Purpose

Use this page when an RL Baselines3 Zoo failure happens before a more specific sub-skill is selected, especially install/import, optional dependency, backend, and command-entry-point issues.

## Quick triage

1. Verify the package imports:
   ```bash
   python - <<'PY'
   import rl_zoo3
   print(rl_zoo3.__version__)
   print(sorted(rl_zoo3.ALGOS))
   PY
   ```
2. Prefer module command checks first:
   ```bash
   python -m rl_zoo3.train --help
   python -m rl_zoo3.enjoy --help
   ```
3. If console commands fail, diagnose optional plotting imports before changing train/evaluate logic.
4. If an environment id is missing, diagnose Gymnasium registration or optional simulator packages before changing RL algorithms.
5. If the problem is workflow-specific, route to the nearest sub-skill troubleshooting page.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'rl_zoo3'` | Package not installed in the active Python environment. | Install `rl_zoo3` into the target environment, then rerun `python -m rl_zoo3.train --help`. |
| `python -m rl_zoo3.train --help` works but `rl_zoo3 train --help` fails on `seaborn`, `rliable`, `scipy`, or `pandas` imports | The console router imports plotting modules even for train/enjoy subcommands. | Use module commands for train/enjoy, or install plotting extras (`.[plots]`) if the console router is required. |
| Trace contains `arch`, `rliable`, `pandas`, or `deprecate_kwarg()` during console/plot imports | Incompatible plotting dependency resolution; a `pandas 3.x` line can break the `rliable`/`arch` stack. | Install a compatible pandas 2.x release: `python -m pip install 'pandas>=2.2,<3'`, then rerun plot/console help. |
| `ENV_ID not found in gym registry, you maybe meant ...?` | Typo, Gymnasium version suffix mismatch, custom registration module not imported, or missing optional env package. | For custom envs, use `--gym-packages`. For optional simulator families, install the package that registers the env. For command-level fixes, route to `sub-skills/training-cli/SKILL.md`; for registration components, route to `sub-skills/custom-components/SKILL.md`. |
| Optional simulator import failure | Core RL Zoo install does not include every Atari/MuJoCo/Box2D/PyBullet/highway/Minigrid/robotics dependency. | Install only the environment family needed for the task, or use CartPole/Pendulum for smoke tests. |
| CUDA requested but PyTorch reports no device | Host or environment lacks a compatible accelerator runtime, or the process cannot see the GPU. | Use `--device cpu` for portable checks. If accelerator training is required, validate PyTorch CUDA/MPS/ROCm before launching long runs. |
| W&B tracking fails | `wandb` package, network, or credentials are missing. | Remove `--track` for local training or route to `sub-skills/integrations-hub-tracking/SKILL.md` before enabling W&B. |
| Hub download/upload fails | Network, credentials, permissions, remote file layout, or destination folder collision. | Do not retry blindly. Route to `sub-skills/integrations-hub-tracking/SKILL.md` and use the bundled layout checker before live transfer. |
| Video creation fails or output is empty | Missing display/offscreen render support, environment does not support video frames, or `ffmpeg` is missing. | Use `--no-render` for evaluation-only checks. Route video-specific work to `sub-skills/integrations-hub-tracking/SKILL.md`. |
| Plotting commands show an empty graph/table | Missing monitor/evaluation files, too few episodes for rolling window, or mismatched env/algorithm labels. | Route to `sub-skills/plotting-benchmarking/SKILL.md` and check input file formats before rerunning experiments. |
| Long command starts training unexpectedly | A helper command was confused with a real RL Zoo command. | Bundled helper scripts are non-executing command builders or inspectors. Commands beginning with `python -m rl_zoo3.train`, `rl_zoo3 train`, `python -m rl_zoo3.enjoy`, or Hub/video modules perform real work. |

## Root install checker

Use the bundled root checker for non-mutating import and optional dependency probes:

```bash
python scripts/check_rl_zoo3_install.py --check-plots --check-cuda
```

The checker does not train, upload, download, render, or require the original repository checkout.

## Sub-skill troubleshooting pages

- Training/resume/checkpoint callback issues: `sub-skills/training-cli/references/troubleshooting.md`.
- YAML/Python config and override grammar: `sub-skills/config-hyperparams/references/troubleshooting.md`.
- Optuna HPO and study reuse: `sub-skills/tuning-optimization/references/troubleshooting.md`.
- Local model/artifact evaluation: `sub-skills/evaluation-and-artifacts/references/troubleshooting.md`.
- Custom envs, wrappers, callbacks, SBX/custom registry: `sub-skills/custom-components/references/troubleshooting.md`.
- Hub, W&B, and video: `sub-skills/integrations-hub-tracking/references/troubleshooting.md`.
- Plotting and benchmark output: `sub-skills/plotting-benchmarking/references/troubleshooting.md`.
