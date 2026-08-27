# RL training and evaluation workflows

## Purpose

Use this reference for the complete policy workflow. It distills the public
training package's Hydra/RSL-RL behavior into commands that do not require
opening or executing a source-checkout script. The commands are intentionally
not a replacement for the Isaac Gym prerequisite: the current handoff has no
importable `isaacgym` package, so execution remains blocked until that
required backend is supplied.

Set these user-owned paths before planning a run:

```bash
PROJECT_COPY=/path/to/current/project-copy
RSL_RL_REPO=/path/to/current/rsl_rl-repository
RUN_ROOT=/path/to/user/run-root
CHECKPOINT=/path/to/user/checkpoints/Aliengo/model_100.pt
```

Install the current package/repository copy through its public interface:

```bash
python -m pip install --no-deps -e "$RSL_RL_REPO"
python -m pip install -e "$PROJECT_COPY"
```

Use the bundled `scripts/run_training.py` launcher from this sub-skill. It
resolves the installed `RL_Environment/train.py` entry point, runs it from the
installed package directory so its Hydra config is available, and keeps the
source checkout out of the runtime instruction. It is a dry run unless
`--run` is supplied. Keep logs under a user-owned `RUN_ROOT`.

## Preflight

1. Use the setup/diagnostics route to establish Python 3.8, PyTorch 1.10 with
   CUDA 11.3, the pinned RSL-RL revision, the compiled `mpc_osqp` extension,
   and the official Isaac Gym Preview 4 SDK.
2. From the installed `rl-training` sub-skill directory, run the bundled
   planner/checker:

   ```bash
   python scripts/validate_rl_config.py --task Aliengo --num-envs 1
   ```

   For a checkpoint, pass the user-owned absolute path:

   ```bash
   python scripts/validate_rl_config.py --task Aliengo --num-envs 1 \
     --test --checkpoint "$CHECKPOINT"
   ```

   This checks task names, scalar override values, and an explicitly supplied
   checkpoint path. It does not import Isaac Gym, allocate a GPU, run a
   simulator, or deserialize a checkpoint.
3. Decide whether the request is training, evaluation, or resume. Do not use
   `test=True` as a training smoke test: evaluation constructs the full
   simulator and then runs ten maximum episode horizons.

## Start a new training run

Choose a user-owned launch/run directory before invoking the public command.
The inspected implementation writes task-specific logs relative to its launch
context; do not allow that context to be a construction checkout. After
replacing the placeholder with the package's documented public command:

```bash
python scripts/run_training.py --run --run-root "$RUN_ROOT" -- \
  task=Aliengo headless=True
```

Replace `Aliengo` with `A1` or `Go1` for the other supported task names. A
viewer-enabled run is the documented default:

```bash
python scripts/run_training.py --run --run-root "$RUN_ROOT" -- \
  task=Aliengo headless=False
```

Useful safe-to-plan overrides include:

```bash
python scripts/run_training.py --run --run-root "$RUN_ROOT" -- \
  task=Aliengo headless=True num_envs=4 sim_device=cuda:0 \
  rl_device=cuda:0 seed=42 max_iterations=5000
```

All assignments are Hydra overrides separated by spaces. There is no custom
argparse `--task` or `--checkpoint` interface in the inspected public training
entry point. `task` is a Hydra config-group selection; `task_name` is derived
from the selected task's `name` field. `max_iterations` changes the PPO
runner's update count, while `num_envs` changes the vectorized environment
count through the task resolver.

The training entry point enables `Parameters.bridge_MPC_to_RL` before
launching. Each policy action therefore goes through the MPC-weight bridge and
produces controller torques; it is not a direct joint-position policy. See
[api-reference](api-reference.md) before changing that contract.

## Evaluate a checkpoint

Use an explicit user-owned checkpoint rather than an implicit latest-run
fallback:

```bash
python scripts/run_training.py --run --run-root "$RUN_ROOT" -- \
  task=Aliengo checkpoint="$CHECKPOINT" test=True num_envs=4
```

Preflight the same artifact from the installed sub-skill directory:

```bash
python scripts/validate_rl_config.py --task Aliengo --num-envs 4 --test \
  --checkpoint "$CHECKPOINT"
```

The loader first attempts the explicit checkpoint. If it fails, the inspected
implementation asks its run utility for the latest model under the configured
task run root. That fallback is convenient but not deterministic enough for a
reported experiment: it can select an unintended artifact or fail if no model
exists. Prefer an explicit checkpoint and record its absolute path.

The checker only verifies that the file is present and regular. It does not
load untrusted pickle-based checkpoint data. A `test=True` run with no
checkpoint still enters the loader path and relies on the configured latest-run
fallback; it is valid only when a suitable prior model is intentionally
available under the user-owned run root.

Evaluation obtains `ppo_runner.get_inference_policy(device=env.device)`, reads
`env.get_observations()`, and repeatedly calls `env.step(actions)`. It does not
write a separate metric report in the entry point. The loop count is
`10 * env.max_episode_length`; the task defaults imply a 20-second episode at
`dt=0.01`, so this is a substantial simulator run.

## Resume or continue training

To load a known model and continue learning, keep `test=False` and supply the
same user-owned checkpoint:

```bash
python scripts/run_training.py --run --run-root "$RUN_ROOT" -- \
  task=Aliengo checkpoint="$CHECKPOINT" test=False headless=True \
  num_envs=4 max_iterations=1000
```

The runner loads `model_state_dict`, `optimizer_state_dict`, and the saved
iteration counter. The subsequent `learn` call runs the configured number of
additional iterations. If `test=False` and no checkpoint is supplied, a new
runner starts from an uninitialized policy; it does not discover a checkpoint
implicitly.

## Run layout and checkpoint semantics

The inspected implementation creates a task-specific log root below the
launch context and a timestamped run directory beneath it. It writes the
resolved Hydra config as `config.yaml` in that experiment directory. The
RSL-RL runner saves files named like `model_0.pt`, `model_100.pt`, and a final
`model_<iteration>.pt` at its log location, with save checks every 100
iterations by default.

A documentation example using a task/`nn`/checkpoint hierarchy is a usable
*path shape* only when that artifact has actually been produced. It is not the
normal filename written by this version of `OnPolicyRunner`. Do not infer
compatibility from a `.pth` or `.pt` suffix. A loadable file must contain the
RSL-RL checkpoint keys listed in [api-reference](api-reference.md), and its
policy dimensions must match the selected task.

## TensorBoard

RSL-RL creates TensorBoard event files when `learn` starts and a log directory
is supplied. Point TensorBoard at the user-owned run root:

```bash
tensorboard --logdir "$RUN_ROOT"
```

The runner records tags including `Loss/value_function`, `Loss/surrogate`,
`Loss/learning_rate`, `Policy/mean_noise_std`, `Perf/*`, and `Train/*`; episode
metrics are recorded when the environment supplies them. A test-only run does
not call `learn`, so it should not be expected to create a new training event
stream.

## Policy-to-MPC deployment handoff

The runtime `WeightPolicy` loads an RSL-RL actor and converts its 12 outputs to
MPC weights. The interactive controller route owns the viewer/gamepad and
low-level FSM; use [mpc-control](../../mpc-control/SKILL.md) for that side. The
high-level deployment sequence is:

1. Verify the checkpoint was trained with the same task, observation ordering,
   policy dimensions, and action-to-weight scale.
2. Set the controller bridge policy according to the controller route; the
   documented policy-launch path uses the controller's policy mode.
3. Supply the user-owned task-specific checkpoint explicitly.
4. Validate one observation/action cycle before enabling hardware or an
   interactive run. The current environment handoff cannot perform this
   Isaac-Gym-dependent validation.

Do not bundle weights or a long training/deployment wrapper in this skill.
