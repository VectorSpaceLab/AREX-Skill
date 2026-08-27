# Install and environment guidance

## Purpose

Read this before choosing an RL Baselines3 Zoo command form, installing optional extras, or debugging import/backend issues. This reference is public runtime guidance; it deliberately omits private inspection-environment details.

## Package identity

- Public distribution name: `rl_zoo3`.
- Import package: `rl_zoo3`.
- Console entry point: `rl_zoo3` with subcommands such as `train`, `enjoy`, `plot_train`, `plot_from_file`, and `all_plots`.
- Python requirement: Python 3.10 or newer.
- Core runtime stack: Stable-Baselines3, SB3-Contrib, Gymnasium, PyTorch, Optuna, PyYAML, Hugging Face SB3 helpers, Rich/TQDM, PyTableWriter, and Shimmy.

## Install profiles

Use the smallest profile that matches the task.

| Profile | Command pattern | Use when | Notes |
| --- | --- | --- | --- |
| Package install | `pip install rl_zoo3` | User wants published package workflows | Good for installed-package use; exact version depends on package index. |
| Source editable core | `pip install -e .` | Working from a checkout or development clone | Enough for `python -m rl_zoo3.train` and `python -m rl_zoo3.enjoy` style workflows. |
| Console + plotting | `pip install -e .[plots]` or install `seaborn`, `pandas`, `scipy`, `rliable` | User needs `rl_zoo3` console router or plot commands | The console router imports plotting modules even for train/enjoy subcommands. |
| Extra simulator stack | install only the package for the selected environment family | Atari, MuJoCo, Box2D, PyBullet, highway, Minigrid, robotics, or custom envs | Do not install every optional simulator stack just for CartPole/Pendulum smoke tests. |
| Full optional environment | project-style full requirements | Reproducing broad repo test/example coverage | Can include network, compiled packages, ROM/data, W&B, video, or simulator dependencies. Avoid unless selected. |

## Command form decision

Prefer module commands for core train/evaluate tasks:

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1 --n-timesteps 1000
python -m rl_zoo3.enjoy --algo ppo --env CartPole-v1 -f logs --exp-id 0 --no-render
```

Use the console router when its optional imports are installed and the workflow expects subcommands:

```bash
rl_zoo3 train --algo ppo --env CartPole-v1 --n-timesteps 1000
rl_zoo3 plot_train --help
```

If `rl_zoo3 train --help` fails before showing train flags because plotting dependencies are missing, switch to `python -m rl_zoo3.train` or install the plotting profile.

## Minimal import and CLI smoke checks

Run these from the target Python environment:

```bash
python - <<'PY'
from importlib.metadata import version
import rl_zoo3, gymnasium, stable_baselines3, sb3_contrib, optuna, torch
print('rl_zoo3', version('rl_zoo3'), rl_zoo3.__version__)
print('algos', sorted(rl_zoo3.ALGOS))
print('torch', torch.__version__, 'cuda available:', torch.cuda.is_available())
PY

python -m rl_zoo3.train --help
python -m rl_zoo3.enjoy --help
```

For the console router and plotting workflows:

```bash
rl_zoo3 train --help
rl_zoo3 plot_train --help
```

The bundled root script [../scripts/check_rl_zoo3_install.py](../scripts/check_rl_zoo3_install.py) performs similar checks without network, training, or mutation.

## Optional backends and services

- **CPU** is sufficient for package inspection, command building, CartPole/Pendulum smoke runs, config validation, artifact inspection, and plotting command construction.
- **CUDA/accelerators** are optional for RL Zoo unless the user explicitly asks for accelerator training or an environment/model path requires it. Validate PyTorch device availability before long runs, then pass `--device cuda` or `--device auto` deliberately.
- **Simulator families** are registered by their own packages. A missing env id is usually an install/registration issue, not a train command issue.
- **Atari ROMs/data** may require separate accepted-license downloads. Do not trigger ROM/data downloads during ordinary skill-guided checks.
- **Hugging Face Hub and W&B** require network and often credentials. Plan them through the integrations sub-skill.
- **Video rendering** can require `render_mode="rgb_array"`, a display or offscreen backend, and `ffmpeg` for GIF/concatenation workflows.

## Evidence-backed install caveat

During environment preparation, the plotting extra resolved to a `pandas 3.x` version that caused an import failure in `rliable`/`arch` (`deprecate_kwarg() missing ...`). If console or plotting imports fail with an `arch`/`pandas` compatibility trace, install a compatible `pandas` 2.x line, for example:

```bash
python -m pip install 'pandas>=2.2,<3'
```

This satisfies the RL Zoo plotting requirement (`pandas>=2.2`) while avoiding the observed `rliable`/`arch` incompatibility.

## Route map after install

- Training or resume command: `sub-skills/training-cli/SKILL.md`.
- Config/hyperparameter YAML/Python grammar: `sub-skills/config-hyperparams/SKILL.md`.
- Optuna HPO: `sub-skills/tuning-optimization/SKILL.md`.
- Local artifact/evaluation inspection: `sub-skills/evaluation-and-artifacts/SKILL.md`.
- Custom envs, wrappers, callbacks, SBX/custom registry patching: `sub-skills/custom-components/SKILL.md`.
- Hub/W&B/video: `sub-skills/integrations-hub-tracking/SKILL.md`.
- Plotting and benchmark outputs: `sub-skills/plotting-benchmarking/SKILL.md`.
