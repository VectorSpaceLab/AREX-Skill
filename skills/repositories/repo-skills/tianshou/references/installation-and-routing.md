# Installation and Routing

## Package Identity

- Distribution/import name: `tianshou`
- Version covered by this skill: `2.0.1`
- Core stack: Python 3.11, PyTorch, Gymnasium, NumPy/Pandas, Matplotlib, TensorBoard, PettingZoo, and Tianshou's core runtime dependencies.
- Public install checks should use package imports and metadata, not local editable paths.

## Install Checks

Use a fresh environment with Python 3.11 and install Tianshou through a public package source or a local editable checkout when doing repo development. Then run:

```bash
python - <<'PY'
import importlib.metadata as md
import tianshou
print(tianshou.__version__)
print(md.version("tianshou"))
PY
```

For a broader smoke without training:

```bash
python skills/tianshou/scripts/check_tianshou_install.py
```

## Optional Extras

Tianshou documents optional extras for environment engines and evaluation. Install only the extras needed for the task:

| Extra/task family | Use when |
| --- | --- |
| `atari` | Atari examples or wrappers need ALE/AutoROM/OpenCV/Shimmy support. |
| `box2d` | Box2D examples such as LunarLander or BipedalWalker are requested. |
| `classic_control` | Classic-control rendering or pygame-backed tasks need extra support. |
| `mujoco` | MuJoCo continuous-control examples or benchmarks are requested. |
| `envpool` | EnvPool integration or high-throughput vectorized environments are explicitly requested. |
| `robotics` | Gymnasium robotics tasks are requested. |
| `vizdoom` | VizDoom examples require the VizDoom package and game assets. |
| `argparse` | High-level example scripts that expose JSONArgParse/docstring-parser CLIs are used. |
| `eval` | rliable/arch/joblib/scipy evaluation utilities and benchmark reports are used. |

Do not install all extras by default. Optional engines often need external assets, compilers, display support, or long downloads.

## API-Level Decision

Use high-level APIs when the user wants fast application code for an existing algorithm:

- `ExperimentConfig`
- `EnvFactoryRegistered`
- `OffPolicyTrainingConfig` or `OnPolicyTrainingConfig`
- algorithm-specific builders such as `DQNExperimentBuilder`
- algorithm params dataclasses such as `DQNParams`, `PPOParams`, `SACParams`

Use procedural APIs when the user needs control over:

- custom Gymnasium/PettingZoo env factories
- `Net`, actor, critic, policy, and algorithm construction
- replay buffer and collector details
- trainer parameter dataclasses
- custom algorithms or policies

Use the specialized routes for buffers, envs, offline/specialized RL, and evaluation rather than overloading high-level or procedural guidance.

## Bounded Defaults

For first-pass generated examples:

- Use CPU unless the user explicitly asks for GPU.
- Use `DummyVectorEnv` before subprocess/Ray workers.
- Disable rendering/watch in headless or CI contexts.
- Disable persistence/log files for pure construction smokes.
- Keep `max_epochs`, `epoch_num_steps`, `buffer_size`, and collection steps tiny until object wiring passes.
- Avoid benchmark, D4RL/Atari download, MuJoCo training, VizDoom, and multi-seed launchers as smoke tests.
