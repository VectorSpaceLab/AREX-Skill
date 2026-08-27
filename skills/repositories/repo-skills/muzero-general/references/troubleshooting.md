# MuZero General Troubleshooting

## Bundled-source import model

Symptom:

```text
ModuleNotFoundError: No module named 'muzero'
ModuleNotFoundError: No module named 'games'
```

MuZero General is not packaged with `pyproject.toml`/`setup.py`, so this skill bundles the required source snapshot under `runtime/source/`. The skill-owned helpers add that bundled source to `sys.path` automatically when `--repo-root` is omitted. Use `--repo-root <staged-muzero-source>` only when validating an editable staged copy or another target checkout.

## Dependency versions and installation

Documented install uses:

```bash
pip install -r runtime/source/requirements.lock
```

The lock file is Python 3.7-era. On modern Python, exact historical pins may not resolve or may require compatibility adjustments. The core runtime surfaces are:

- `torch` for networks/training.
- `ray` for actors/workers.
- `gym` plus `pygame` for classic-control CartPole on newer Gym wheels.
- `numpy` for arrays.
- `tensorboard` for logging.
- `nevergrad` for HPO.
- `seaborn`/`matplotlib` for diagnostics.

Install optional game dependencies only when their game is selected.

## Gym warnings

Gym may warn that it is unmaintained or that `env.seed(seed)` is deprecated. The source uses legacy Gym APIs. Treat warnings as non-fatal when game reset/step/shape checks pass. When adapting Gymnasium/new-Gym environments, normalize reset/step output in the `Game` wrapper.

## Ray warnings and lifecycle

Ray starts during `MuZero.__init__`. Common operational issues include port/address warnings, object-store memory warnings, dependency serialization errors, stale workers, or dashboard startup issues.

Recovery:

1. Run `scripts/check_muzero_environment.py --smoke --json` from the skill root to check the bundled source snapshot.
2. Keep smokes CPU-safe and small.
3. Ensure scripts call `ray.shutdown()` unless leaving Ray alive is intentional.
4. Reduce `num_workers`, `num_simulations`, and training scale before debugging algorithm behavior.
5. Route training-specific Ray failures to `sub-skills/training-and-cli/references/troubleshooting.md`.

## Optional dependency matrix

| Optional surface | Missing symptom | Action |
| --- | --- | --- |
| LunarLander | missing `box2d-py`/SWIG message | Install only if LunarLander is required; ask before host SWIG/compiler changes. |
| Atari/Breakout | `Please run "pip install gym[atari]"` or missing OpenCV/ALE/ROM assets | Install Atari/OpenCV/assets only with approval; do not use as default smoke. |
| MiniGrid | `Please run "pip install gym_minigrid"` | Install only for `gridworld`. |
| OpenSpiel | message asking for `open_spiel`/`pyspiel` | Install only for `spiel`; beware heavier binary dependency. |
| Graphviz diagnostics | `Please install graphviz to get the MCTS plot.` | Needed only for PDF MCTS plots; not needed for checkpoint inspection. |

## CPU/GPU boundaries

CPU fully verifies the selected core semantics: imports, game contracts, FC/ResNet construction, MCTS, Ray task startup, and checkpoint inspection. GPU support is optional for speed and scheduling.

- CPU-safe config: `max_num_gpus=0`, `train_on_gpu=False`, `selfplay_on_gpu=False`, `reanalyse_on_gpu=False`.
- Do not set `max_num_gpus=0` while any GPU flag is true.
- Do not claim multi-GPU performance or scheduling has been verified unless a CUDA-capable PyTorch/Ray environment and an explicit GPU smoke were run.

## Long-running defaults

Many built-in configs default to 10,000 through 1,000,000 training steps. Atari defaults to very large worker/training settings. Always set a bounded override for smoke or testing.

## Where to debug next

- Install/import/Ray high-level failure: root checker first, then `training-and-cli` troubleshooting.
- Game shape/action/dependency failure: `games-and-configs` troubleshooting.
- Tensor/support/MCTS failure: `models-and-mcts` troubleshooting.
- Checkpoint/replay/plot failure: `checkpoints-and-diagnostics` troubleshooting.
