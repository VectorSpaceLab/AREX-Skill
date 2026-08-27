# Model-Based RL Troubleshooting

Use this reference before running any AI-Optimizer model-based RL workflow. Most failures are environment/version/resource issues rather than algorithm-code issues.

## Cross-cutting safety checklist

1. Confirm the algorithm family and read its workflow reference.
2. Generate or write the exact command without launching long training first.
3. Probe imports for the selected framework stack in an isolated environment.
4. Confirm simulator licenses/rendering and GPU availability when relevant.
5. Choose a bounded log/result directory and enough disk space.
6. Avoid background launchers (`nohup`, shell loops, multi-GPU loops) until a single foreground command works.

## Common failure matrix

| Symptom | Likely cause | Applies to | Recovery |
|---|---|---|---|
| TensorFlow wheel cannot install or import | Old TensorFlow GPU pin is incompatible with current Python/CUDA/cuDNN | BMPO, MBPO, ED2-MBPO, PlaNet, Dreamer/ED2-Dreamer | Use an environment with the documented era of Python/CUDA, or switch to CPU-compatible wheels only if the code path supports them. Do not treat CPU import as proof of GPU training. |
| `mujoco-py` build/import errors | MuJoCo 1.50 runtime or license missing; compiler/GL dependency mismatch | MBPO, ED2-MBPO, BMPO, Gym MuJoCo tasks, some CaDM datasets | Install the matching MuJoCo runtime/license and system GL dependencies. Verify `mujoco-py` import before running training. |
| dm_control rendering errors, EGL/GL failures, blank frames | Renderer/backend setup incomplete | Dreamer, ED2-Dreamer, PlaNet | Verify dm_control can create and render the selected task. Select the correct EGL/OSMesa/GL backend for the machine. |
| Ray crashes, resource deadlocks, or object-store allocation errors | Old Ray version, too many workers, large object-store memory, incompatible Python | MuZero, Sampled MuZero, MBPO/ED2-MBPO/BMPO | Start with minimal CPUs/GPUs, lower object-store memory for Sampled MuZero, and avoid multi-GPU launchers until a single worker command succeeds. |
| Gym environment not found | Gym version mismatch or missing extras/MuJoCo/Box2D/Atari packages | MuZero, Sampled MuZero, MBPO, BMPO, PlaNet Gym tasks | Install the exact Gym era and extras required by the algorithm. For MuZero, prefer `CartPole-v1` + `classic_control` first. |
| MuZero test cannot find model | Train/test flags derive different result paths or no `model.p` exists | MuZero | Reconstruct train and test commands with identical result root, case, env, seed, priority, target-model, value-loss, and revisit-rate flags. |
| MuZero command rejects revisit rate | Rate outside `[0, 1]` | MuZero command helper and source CLI | Use a float in `[0, 1]` or omit the flag to use config default. |
| MuZero command rejects `--use-max-priority` | Max-priority flag only makes sense with prioritized replay enabled | MuZero command helper | Add `--use-priority` or remove `--use-max-priority`. |
| MuZero Atari/Box2D command import fails | Parser accepts case but matching config/dependency stack may be absent | MuZero | Treat as an extension task. Add/verify config modules and dependencies before running. |
| BMPO README command cannot find `main.py` | Visible evidence has `runner.py` and algorithm/config files but no launcher | BMPO | Verify the target checkout. If missing, create a small launcher around `ExperimentRunner` and `config.<name>.params` before running. |
| ED2-MBPO or ED2-Dreamer starts many background jobs | Provided launcher loops over GPUs and uses `nohup` | ED2-MBPO, ED2-Dreamer | Replace launcher with a single explicit command during validation; only use loops after resource approval. |
| PlaNet `--params` parsing fails | YAML dictionary quoting error or lowercase boolean mismatch | PlaNet | Quote the full params string and use Python-style booleans in CLI flags where the parser expects `True`/`False`. |
| CaDM import fails with `No module named cadm` | Visible subtree only exposes run scripts; package source/dependencies may be absent in the target runtime | CaDM | Verify the package code and dependency installation before running. Treat `run_test.sh` as a recipe, not a verified runnable command. |
| Logs/results appear in unexpected locations | Algorithm defaults write to relative paths, `~/ray_mbpo`, `./logdir`, `./results`, `./data`, or per-domain log folders | All | Choose explicit log/result roots where the CLI supports them. Record defaults before running. |

## Algorithm-specific cautions

### Dreamer and ED2-Dreamer

- TensorFlow GPU versions differ between variants: Vanilla Dreamer README uses TensorFlow GPU 2.2.0; ED2-Dreamer README uses 2.1.0.
- DMControl task names in README recipes use `dmc_<domain>_<task>` naming. A mistyped task may fail deep in environment construction.
- ED2 code exposes `--gpu_id`, `--model_num`, and `--separate_schema`; inconsistent values can silently compare the wrong variant.
- Plotting expects scalar names such as `step` and `test/return`; missing summaries can produce empty plots or `nan` rows.

### MBPO, ED2-MBPO, and BMPO

- These workflows are tightly coupled to old softlearning/Ray/Gym/MuJoCo stacks. Avoid mixing modern Gymnasium/MuJoCo bindings with these configs unless you are deliberately porting the code.
- Dotted config paths must match the current working directory and Python path.
- For new MBPO environments, a static termination function is required; otherwise rollouts may fail or train against incorrect termination semantics.
- BMPO forward/backward rollout schedules and beta schedule are coupled; changing one without the others can make comparisons meaningless.

### MuZero and Sampled MuZero

- `--render` is primarily a test-time option. Rendering during train may be irrelevant or unsupported.
- `--force` can overwrite previous results; prefer a fresh result root for experiments you want to preserve.
- Sampled MuZero defaults to large Ray resources. Lower `--num_cpus`, `--num_gpus`, and `--object_store_memory` when probing locally.
- Game-specific `MuZeroConfig` classes define observation shapes and action spaces; invalid game wrappers cause shape/action failures during self-play.

### PlaNet

- Use `--config debug` for code-path probes, not as performance evidence.
- `--params` is YAML-like, so shell quoting matters: `--params '{tasks: [cheetah_run], planner_iterations: 2}'`.
- Environment isolation can matter: switch `isolate_envs` between `thread` and `process` when multiprocessing/threading fails.
- CEM planner values (`planner_amount`, `planner_topk`, `planner_iterations`, `planner_horizon`) have large runtime impact.

### CaDM

- The visible `run_test.sh` references commands such as `run_cadm_pets`, while the inspected subtree exposes `run_pets.py`; do not assume both exist.
- `run_pets.py` supports datasets `cartpole`, `pendulum`, `halfcheetah`, `cripple_halfcheetah`, `ant`, and `slim_humanoid`; missing simulator dependencies are likely for MuJoCo-style datasets.
- Policy type is limited to `RS` or `CEM` by source validation.

## Minimal non-training checks

Use these checks before asking for a heavy run:

- For MuZero: run `python scripts/build_muzero_command.py --help` and generate the intended train/test command.
- For PlaNet: parse the planned `--params` string with a tiny YAML parser or a shell-quoted echo before running.
- For MBPO/BMPO: verify the requested config module name exists in the target runtime and inspect its domain/task fields.
- For Dreamer: generate a direct single-run command with explicit `--logdir`, `--task`, `--steps`, and variant flags.
- For CaDM: confirm the `cadm` package imports and the selected dataset is implemented before launching.
