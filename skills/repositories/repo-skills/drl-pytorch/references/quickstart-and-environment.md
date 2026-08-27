# Quickstart and Environment

Read this when a task needs a reproducible DRL-Pytorch runtime plan before choosing an algorithm-specific sub-skill.

## Repository shape

DRL-Pytorch is a collection of standalone algorithm directories rather than an installable Python distribution. Each algorithm directory contains its own `main.py`, implementation module, and often a local `utils.py`. The launchers rely on the current working directory for imports, checkpoints (`model/`), and TensorBoard logs (`runs/`).

For future tasks, treat the DRL-Pytorch checkout as an explicit input. The generated skill provides the command matrix, scripts, and troubleshooting; it does not bundle the original algorithm source or pretrained checkpoint binaries.

## Baseline dependencies

The repository READMEs document this common baseline for current Gymnasium-based workflows:

```text
python 3.11.x
gymnasium==0.29.1
numpy==1.26.1
torch==2.1.0
tensorboard==2.15.1 when using --write True
matplotlib==3.8.2 for C51 rendering helpers
```

A CPU-only PyTorch install is sufficient for safe import, object-construction, and zero-step smoke checks. Several launchers default to CUDA (`--dvc cuda` or `--device cuda`), so set CPU explicitly when the runtime has no usable GPU or when you are only validating command construction.

## Optional dependency gates

| Workflow | Extra dependency gate | What to verify before real execution |
|---|---|---|
| LunarLander and LunarLanderContinuous | `gymnasium[box2d]` | `gymnasium.make("LunarLander-v2")` or `gymnasium.make("LunarLanderContinuous-v2")` works. |
| Humanoid and HalfCheetah | `mujoco` or `gymnasium[mujoco]` | MuJoCo imports and `gymnasium.make("Humanoid-v4")` / `HalfCheetah-v4` works. |
| BipedalWalker | `gymnasium[box2d]` | `gymnasium.make("BipedalWalker-v3")` works. |
| Atari NoFrameskip | `gymnasium[atari]`, `gymnasium[accept-rom-license]`, accepted ALE ROMs, `opencv-python` | The wrapper imports and the target Atari environment can be created. Do not download ROMs silently. |
| Actor-Sharer-Learner | `envpool`, Atari env support, multiprocessing-capable platform | EnvPool imports, target env spec exists, and device/process settings are safe. |
| CUDA acceleration | CUDA-capable torch wheel and compatible driver | `torch.cuda.is_available()` and a tiny CUDA tensor allocation succeed. |

Do not treat optional dependency failures as failures of the CPU-safe core workflows. Route dependency-specific recovery to the owning sub-skill's troubleshooting reference.

## Safe smoke strategy

Use smoke checks before training:

1. Run the self-contained matrix helper to choose a route:

   ```bash
   python scripts/drl_pytorch_algorithm_matrix.py --format table
   ```

2. If a checkout is available, run bundled no-training diagnostics:

   ```bash
   python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite all
   ```

3. If you only need one area, select a suite:

   ```bash
   python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite value
   python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite policy
   python scripts/drl_pytorch_safe_smoke.py --repo-root <DRL-Pytorch-checkout> --suite atari
   ```

The bundled smokes import modules and run tiny CPU object/network checks. They do not run long training loops, create optional Box2D/MuJoCo/Atari environments, render, write checkpoints, start EnvPool workers, or download ROMs.

## Zero-step launcher checks

Most `main.py` launchers support `--Max_train_steps 0`. Running from the selected algorithm directory with CPU flags validates parser, environment construction, model construction, and checkpoint/log path setup without training.

Examples:

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

PER launchers lack `--dvc`; for CPU-only validation on CUDA-visible machines, hide CUDA:

```bash
CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write False --render False --Max_train_steps 0
```

Atari and ASL launchers are not zero-step-safe substitutes for dependency checks because environment creation needs ROM/OpenCV/EnvPool gates and ASL launches multiple processes. Use the Atari/ASL bundled smoke first.

## Training safety

Training is stochastic and can be long. Before removing `--Max_train_steps 0`, confirm:

- selected algorithm and `EnvIdex` match the action space;
- optional environment extras are installed;
- device flags point to a usable backend;
- `model/` and `runs/` writes are acceptable in the target checkout;
- rendering is permitted by the display/session;
- checkpoint `ModelIdex` matches the algorithm's filename convention.
