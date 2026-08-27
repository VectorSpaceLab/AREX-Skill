# Model-Based RL Overview

AI-Optimizer's model-based RL collection is a research-code bundle rather than one uniform package. Each algorithm family keeps its own framework version, config style, and dependency stack. Use this overview to choose a family and then follow the nearest workflow reference.

## Collection taxonomy

The collection frames modern MBRL around two questions: how to learn a model and how to use it. It groups algorithms by research purpose rather than by a strict tree, because many methods are orthogonal.

| Direction | Approach in this collection | Algorithms | Best-fit use |
|---|---|---|---|
| Reduce model error | Analytical gradients through a learned latent world model | Dreamer, ED2-Dreamer | Image/control tasks where behavior is learned from imagined latent rollouts. |
| Reduce model error | Dyna-style model-generated rollouts | MBPO, ED2-MBPO | Continuous-control baselines that interleave real data with short synthetic model rollouts. |
| Higher tolerance to model error | Bidirectional Dyna-style rollouts | BMPO | Continuous-control comparisons that use forward and backward models to reduce reliance on only forward predictions. |
| Reduce model error | Planning in latent dynamics | PlaNet | Pixel-control tasks where online planning in a learned latent model is the primary policy mechanism. |
| Faster planning | Learned model + MCTS-style planning | MuZero, Sampled MuZero | Classic-control/game-style environments and planning experiments. Sampled MuZero targets complex action spaces. |
| Scalability/generalization | Context-aware dynamics generalization | CaDM | Dynamics generalization or context-aware PETS-style comparisons. |

## Algorithm map and practical entry points

| Family | Collection location label | Main runtime idea | Primary command shape | Heavy prerequisites and caveats |
|---|---|---|---|---|
| Dreamer | `modelbased-rl/Dreamer/Vanilla_Dreamer` | TensorFlow 2 world model, latent imagination, actor/value learning | `python3 dreamer.py --logdir ... --task dmc_walker_walk` | TensorFlow GPU 2.2 era, TensorFlow Probability, dm_control, rendering stack, long image-control training. |
| ED2-Dreamer | `modelbased-rl/Dreamer/ED2-Dreamer` | Dreamer with environment dynamics decomposition controls | `python -u dreamer.py --model_num ED2_Dreamer --separate_schema ED2 ...` | Similar to Dreamer but README pins TensorFlow GPU 2.1; launcher may start several background GPU jobs. |
| Vanilla MBPO | `modelbased-rl/MBPO/Vanilla-MBPO` | SAC plus short model-generated rollouts from real data | `mbpo run_local ... --config=examples.config.halfcheetah.0` | MuJoCo 1.50, old Gym/Ray/softlearning stack, GPU-oriented conda environment. |
| ED2-MBPO | `modelbased-rl/MBPO/ED2-MBPO` | MBPO with ED2 action-group/dynamics decomposition config | `python -u mbpo.py --config=examples.config.halfcheetah.0 ...` | Same MBPO stack; provided `run.py` launches multiple GPU background jobs. |
| BMPO | `modelbased-rl/BMPO` | Forward and backward dynamics models feeding policy optimization | README command is `python main.py --config=config.hopperNT` | Old TensorFlow GPU 1.13, Ray 0.6.4, Gym 0.12, MuJoCo 1.50. The checkout evidence has `runner.py` but no visible `main.py`; verify or add a launcher before running. |
| MuZero | `modelbased-rl/MuZero` | PyTorch MuZero with classic-control config and Ray workers | `python main.py --env CartPole-v1 --case classic_control --opr train --force` | README says tested on CartPole-v1. Parser accepts atari/box2d, but the checked-in config evidence is classic-control centered. Use bundled command builder first. |
| Sampled MuZero | `modelbased-rl/SampledMuZero` | MuZero-General-derived sampled-action planning | `python muzero.py --env cartpole --seed 666 --num_simulations 50 --training_steps 100000` | Ray/Torch workers; default resource flags can be large. Game configs are per module. |
| PlaNet | `modelbased-rl/PlaNet` | TensorFlow 1 latent dynamics plus online CEM planning from pixels | `python3 -m planet.scripts.train --logdir ... --params '{tasks: [cheetah_run]}'` | TensorFlow GPU 1.13, TensorFlow Probability 0.6, dm_control, Gym, rendering. |
| CaDM | `modelbased-rl/CaDM` | Context-aware/PETS-style dynamics generalization experiments | `python -m run_scripts.run_pets --dataset halfcheetah --policy_type CEM ...` | The visible shell recipes reference `run_cadm_pets`, but the inspected subtree exposes only `run_pets.py`; package imports and dependencies must be verified before execution. |

The collection also mentions unimplemented or absent areas such as TMCL and empty/self-supervised/transfer submodules. Treat them as root-level limitations, not as model-based runtime coverage.

## Choosing a baseline quickly

- **World-model baseline from images:** start with Dreamer when the user wants latent imagination and policy/value learning; use PlaNet when the user explicitly wants online planning with CEM in latent space.
- **Continuous-control Dyna-style baseline:** use MBPO for the vanilla short-rollout baseline; use ED2-MBPO when comparing environment dynamics decomposition; use BMPO when backward rollout/model-error tolerance is central.
- **Planning/game/classic-control baseline:** use MuZero for CartPole/classic-control and MCTS-style planning. Use Sampled MuZero only when sampled actions or complex action spaces are important and Ray resources are acceptable.
- **Dynamics generalization baseline:** use CaDM when the task is about changing dynamics or context-aware generalization. Verify package availability first because the visible subtree is sparse.

## Common config modification points

| Family | Modification surface | Typical changes |
|---|---|---|
| Dreamer/ED2-Dreamer | command-line flags generated from `define_config()` | `--task`, `--logdir`, `--steps`, model sizes, training schedule, `--model_num`, `--separate_schema`, `--gpu_id` for ED2 code. |
| MBPO/ED2-MBPO | Python config modules under environment names | Environment domain/task, rollout schedule, target entropy, model train frequency, rollout batch size, ED2 `action_group`. |
| BMPO | `config.<env>` modules | Domain/task, forward/backward rollout schedules, beta schedule, planning horizon, backward policy variance, log directory. |
| MuZero | CLI flags plus config classes | Environment name, case, train/test operation, result directory, priority flags, target model, value loss coefficient, revisit policy search rate. |
| Sampled MuZero | game-specific `MuZeroConfig` classes plus CLI overrides | Game name, seed, simulations, training steps, resource counts, per-game action space/network/replay settings. |
| PlaNet | `--config default|debug` plus YAML `--params` | Task list, debug mode, model type (`rssm`, `ssm`, `drnn`), planner horizon/amount/top-k/iterations, data collection schedule, action noise, environment isolation. |
| CaDM | `run_pets.py` CLI flags | Dataset, policy type (`CEM` or `RS`), candidate count, horizon, ensemble/particle counts, normalization, deterministic flag, seed. |

## What is intentionally not claimed

- No full training, simulator run, MuJoCo license check, dm_control rendering check, CUDA check, Atari run, or Sampled MuZero Ray cluster run is claimed by this skill.
- No dataset download, D4RL benchmark, Waymo/SMAC/MPE integration, or external paper-result reproduction is included here.
- Commands are recipes; future agents should still probe the target environment, disk space, and hardware before execution.
