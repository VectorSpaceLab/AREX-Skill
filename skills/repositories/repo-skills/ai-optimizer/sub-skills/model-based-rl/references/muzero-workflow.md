# MuZero and Sampled MuZero Workflows

Use this reference for AI-Optimizer tasks about MuZero, Sampled MuZero, learned-model planning, CartPole/classic-control planning, and safe train/test command construction.

## MuZero route

The MuZero implementation is a PyTorch/Ray implementation based on DeepMind's MuZero pseudocode. The README evidence says it has only been tested on `CartPole-v1` and would require config-folder modifications for other environments.

### Safe command construction

Use the bundled helper to print a command without importing Ray/Torch or starting training:

```bash
python scripts/build_muzero_command.py --env CartPole-v1 --case classic_control --opr train --force --no-cuda --result-dir ./results
```

Example output:

```bash
python main.py --env CartPole-v1 --case classic_control --opr train --seed 0 --result_dir ./results --no_cuda --force
```

For testing an existing model:

```bash
python scripts/build_muzero_command.py --env CartPole-v1 --case classic_control --opr test --no-cuda --test-episodes 5 --render
```

The helper accepts user-friendly hyphenated options such as `--result-dir`, `--value-loss-coeff`, and `--use-target-model`, then emits the underscore option names used by the source CLI (`--result_dir`, `--value_loss_coeff`, `--use_target_model`).

### Source CLI options captured by the helper

| Option accepted by helper | Source CLI emitted | Meaning |
|---|---|---|
| `--env` | `--env` | Required Gym environment name, for example `CartPole-v1`. |
| `--case {classic_control,atari,box2d}` | `--case` | Required domain selector. Classic-control is the concrete checked-in path evidenced by config source. |
| `--opr {train,test}` | `--opr` | Required operation. `train` starts training; `test` loads a model from the derived result path. |
| `--result-dir PATH` | `--result_dir PATH` | Optional result root. Source default is a `results` directory under the current working directory. |
| `--no-cuda` | `--no_cuda` | Force CPU device selection even if CUDA is available. |
| `--debug` | `--debug` | Add additional logs such as gradients and target/reward details. |
| `--render` | `--render` | Render the environment during test; generally meaningful for `--opr test`. |
| `--force` | `--force` | Allow overriding previous results in the source utility. Use carefully. |
| `--seed INT` | `--seed INT` | Seed NumPy and Torch; default `0`. |
| `--test-episodes INT` | `--test_episodes INT` | Evaluation episode count; default `10`, must be positive. |
| `--value-loss-coeff FLOAT` | `--value_loss_coeff FLOAT` | Override the value-loss scaling; otherwise loaded from config. |
| `--revisit-policy-search-rate FLOAT` | `--revisit_policy_search_rate FLOAT` | Override target policy re-estimation rate; helper enforces `[0, 1]`. |
| `--use-priority` | `--use_priority` | Enable prioritized replay sampling. |
| `--use-max-priority` | `--use_max_priority` | Assign max priority to new data. Helper requires `--use-priority` because the source marks it valid only with priority enabled. |
| `--use-target-model` | `--use_target_model` | Use target model for bootstrap value estimation. |

### Result layout and model path

The MuZero config computes an experiment path from the result root, case, environment, revisit-policy rate, value-loss coefficient, target-model flag, priority flags, max-priority flag, and seed. The source expects a trained model at `model.p` inside that experiment path for `--opr test`.

A train command with `--result_dir ./results --case classic_control --env CartPole-v1 --seed 0` and default priority/value flags will write under a nested layout equivalent to:

```text
./results/classic_control/CartPole-v1/revisit_rate_0/val_coeff_1/no_target/no_prio/no_max_prio/seed_0/
```

Testing uses the same derived layout, so keep train/test flags consistent.

### Classic-control configuration facts

The checked-in classic-control configuration uses:

- `training_steps=20000`, `test_interval=100`, `test_episodes=5`, `checkpoint_interval=20`.
- `max_moves=1000`, `discount=0.997`, `num_simulations=50`, `batch_size=128`, `num_actors=32`.
- A discrete support of `[-20, 20]` for value and `[-5, 5]` for reward.
- A `ClassicControlWrapper` that stacks 4 observations and returns legal actions from the Gym discrete action space.
- A fully connected MuZero network with representation, dynamics, reward, policy, and value heads.

The main parser accepts `atari` and `box2d`; however, the source evidence for this checkout is classic-control oriented. Treat Atari/Box2D as config-extension tasks unless a matching config module and dependencies are present in the target runtime.

## Recommended MuZero workflow

1. Confirm the operation: train or test.
2. Confirm the environment and case. Prefer `CartPole-v1` with `classic_control` for a first smoke-level command.
3. Decide whether CPU safety is required. Use `--no-cuda` for CPU-only or when CUDA availability is uncertain.
4. Choose a result root and keep train/test flags consistent so model lookup paths match.
5. Generate the command with `build_muzero_command.py`; inspect it before running.
6. Before execution, probe Python version and dependencies (`torch`, `ray`, `gym`, `tensorboard`) in the intended environment. Do not treat command generation as training verification.

## Sampled MuZero route

Sampled MuZero is a separate MuZero-General-derived implementation that samples actions for complex action spaces. It uses Ray workers and per-game config classes.

README command recipe:

```bash
python muzero.py --env cartpole --seed 666 --num_simulations 50 --training_steps 100000
```

Important CLI options:

| Option | Default | Meaning |
|---|---:|---|
| `--env` | required | Game module name, for example `cartpole`, `lunarlander`, `gridworld`, or an Atari-style module if dependencies exist. |
| `--seed` | `0` | Random seed. |
| `--num_simulations` | `50` | MCTS simulations. |
| `--training_steps` | `100000` | Number of weight-update steps. |
| `--num_gpus` | `1` | GPUs exposed to Ray. Set to `0` for CPU-only experimentation if the code path supports it. |
| `--num_cpus` | `20` | CPUs exposed to Ray. |
| `--object_store_memory` | `21474836480` | Ray object-store memory default is about 20 GiB; lower it deliberately on small machines. |

Game-specific config classes define observation shape, action space, network shape, replay buffer, self-play workers, optimizer, training steps, and GPU flags. For a new game, create or adapt a game module with both `MuZeroConfig` and `Game` implementations.

## When to choose MuZero versus Sampled MuZero

| User asks for | Prefer | Why |
|---|---|---|
| A safe CartPole/classic-control command | MuZero | Concrete README-tested path and bundled command builder. |
| Testing a saved model from a known MuZero result directory | MuZero | Source test operation loads `model.p` from the derived experiment path. |
| Complex discrete action spaces or sampled-action planning | Sampled MuZero | The implementation is explicitly designed around sampled actions. |
| Atari-scale planning | Either only after dependency/config verification | MuZero parser and Sampled MuZero games mention Atari, but this is heavy and dependency-sensitive. |

## Known MuZero omissions

- The bundled helper does not execute training, create result directories, import Torch/Ray, or inspect model checkpoints.
- Full MuZero training, Ray worker startup, CUDA behavior, Gym rendering, and Atari/Box2D cases remain unverified heavy runtime tasks.
- The visible Sampled MuZero CLI has a large Ray memory default and a config override key that may not override `results_path` as intended without inspection or patching in the target code.
