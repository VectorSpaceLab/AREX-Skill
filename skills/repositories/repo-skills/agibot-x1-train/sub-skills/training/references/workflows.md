# X1 DH training workflows

## 1. Classify the request and backend

Use this route when the task is about `x1_dh_stand` training or the PPO/config
contract. First separate three cases:

| Request | Route | Backend requirement |
| --- | --- | --- |
| Read dimensions, flags, checkpoints, or algorithm shapes | training | CPU/static inspection is sufficient |
| Construct `X1DHStandEnv`, run `train.py`, or validate terrain/asset behavior | training | **BLOCKED_REQUIRED_BACKEND** until Isaac Gym Preview 4 + compatible CUDA/PhysX is verified |
| Drive a trained policy interactively | `../playback/SKILL.md` | Isaac Gym native playback |
| Export JIT/ONNX | `../export/SKILL.md` | checkpoint plus export dependencies; native policy contract still matters |
| Compare a checkpoint in MuJoCo | `../sim2sim/SKILL.md` | MuJoCo route, not training verification |

Do not infer native success from a config import or a CPU policy smoke. Isaac
Gym is imported by the environment package and by `BaseTask`; the X1 task also
loads an URDF and builds a trimesh simulation.

## 2. Install in a clean, compatible environment

The repository README describes a legacy stack:

```bash
# Python 3.8 environment (choose the user's environment manager)
conda create -n <env> python=3.8
conda activate <env>
conda install pytorch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 \
  pytorch-cuda=11.7 -c pytorch -c nvidia
conda install numpy=1.23

# after obtaining Isaac Gym Preview 4 from its distribution channel
cd <isaacgym-root>/python
pip install -e .
cd <repo-root>
pip install -e .
```

The package metadata additionally names `tensorboard`, `opencv-python`,
`mujoco==2.3.6`, `mujoco-python-viewer`, and `matplotlib`. Those are not a
substitute for the Isaac Gym package. Keep the Isaac Gym install separate and
verify its own example before attempting the X1 environment. Do not paste
machine-specific paths into generated commands; use placeholders as above.

Safe checks before a native run:

```bash
python scripts/training_preflight.py --help
python scripts/training_preflight.py --check-config
python scripts/training_preflight.py --print-command --num-envs 1 --max-iterations 1
python scripts/training_preflight.py --shape-smoke
```

The helper is intentionally non-launching. The shape smoke uses only PyTorch
and validates policy/storage arithmetic. `--check-config` reports whether the
Isaac Gym import gate is present; a missing package is a blocker, not a reason
to create a stub module.

## 3. Build a bounded native command

From the repository root, the source launcher is:

```bash
python humanoid/scripts/train.py \
  --task=x1_dh_stand \
  --run_name=<run_name> \
  --headless \
  --num_envs=<small_verified_count> \
  --max_iterations=<small_trial_count> \
  --seed=<integer> \
  --rl_device=cuda:0
```

`--task`, `--resume`, `--experiment_name`, `--run_name`, `--load_run`,
`--checkpoint`, `--headless`, `--horovod`, `--rl_device`, `--num_envs`,
`--seed`, and `--max_iterations` are custom flags. Isaac Gym's `gymutil`
parser supplies simulator options such as physics engine, compute device,
GPU pipeline, and thread settings. Run `python humanoid/scripts/train.py
--help` only after the required backend is installed; the generic parser itself
comes from Isaac Gym.

For a first native trial, use a small environment count and iteration count,
keep `--headless`, and choose a unique run name. Do not describe a one-iteration
run as learning quality evidence: it only checks startup, one rollout, update,
and checkpoint plumbing. Restore the intended 4096 environments and 20000
iterations only after startup and memory behavior are understood.

The call chain is:

1. `train.py` calls `task_registry.make_env(name=args.task, args=args)`.
2. The registry retrieves `X1DHStandEnv`, `X1DHStandCfg`, and
   `X1DHStandCfgPPO`, applies CLI overrides, seeds RNGs, parses simulator
   parameters, and constructs the Isaac Gym environment.
3. `make_alg_runner` converts config objects to dictionaries, builds
   `DHOnPolicyRunner`, initializes `ActorCriticDH`, `DHPPO`, and rollout
   storage, and chooses the log directory.
4. `train.py` calls `learn(max_iterations, init_at_random_ep_len=False)`.

## 4. Checkpoint and resume workflow

Default log construction is equivalent to:

```text
<project-root>/logs/<experiment_name>/exported_data/<timestamp><run_name>/
```

For this task `<experiment_name>` defaults to `x1_dh_stand`. The runner writes:

- `model_0.pt` at iteration 0 because `0 % save_interval == 0`.
- `model_<iteration>.pt` every 100 iterations by default.
- `model_<final_iteration>.pt` after the loop completes.
- TensorBoard event files in the same run directory when `log_dir` is set.

The saved dictionary has `model_state_dict`, `optimizer_state_dict`,
`es_optimizer_state_dict`, `iter`, and `infos`. Inspect both filename and stored
`iter`: the periodic save uses the loop index for both, but the final filename
uses `current_learning_iteration` after it is incremented while the saved
`iter` remains `self.it`, the last zero-based loop index. A normal 20,000-update
run can therefore write `model_20000.pt` whose stored `iter` is 19999. Resume
uses the stored field, not the filename.

The registry resume path calls `get_load_path(log_root, load_run, checkpoint)`,
prints the selected path, and calls `runner.load(..., load_optimizer=False)`.
Thus resume restores model weights and the stored iteration but intentionally
does not restore optimizer states through this path. Call this out in
reproducibility notes.

Example resume command (use an actual run directory name):

```bash
python humanoid/scripts/train.py \
  --task=x1_dh_stand --headless --resume \
  --load_run=<timestamp><run_name> --checkpoint=<N> \
  --run_name=<new_or_existing_name> --rl_device=cuda:0
```

In the config object, `load_run=-1` means the last run, and
`checkpoint=-1` means the last model. Be careful with the CLI: the source
parser declares `--load_run` as `str`, while the helper compares the value to
integer `-1`. Therefore passing the literal `--load_run=-1` can be treated as a
literal directory name rather than the sentinel. To request the configured
latest run, omit `--load_run`; otherwise pass the exact run directory name.
`--checkpoint=-1` is an integer CLI sentinel and selects the last filename
containing `model` after the helper's sort. Inspect the directory before
resuming; do not assume a timestamp, run name, or model iteration from memory.
A stale `exported` directory is explicitly removed from the run-directory
candidate list by `get_load_path`.

Resume creates a new timestamped `log_dir` before loading the selected model,
so the resumed run's TensorBoard/checkpoint output may be in a new run
 directory even when it loads from an older `--load_run` directory.

## 5. Observe a run without changing its semantics

The runner collects `num_steps_per_env=24` transitions per policy update across
`num_envs` environments, computes GAE returns, performs two epochs over four
mini-batches, logs losses and episode summaries to TensorBoard, and saves at
its interval. Each iteration therefore collects `24 * num_envs` transitions.
The logged fields include value, surrogate, and state-estimator losses,
learning rate, policy noise standard deviation, FPS, collection/learning time,
mean reward, mean episode length, and 47 observation means/stds. Episode info
comes from environment extras (`rew_*`, terrain level, max command x, and
optional timeout data).

Use TensorBoard against the run directory if the command completed, but avoid
interactive playback as a training check. If a run is interrupted, inspect the
latest complete `.pt` file and its `iter`; do not treat a partially written
file as valid.
