# TD3 workflows

## 1. Model-only smoke (no ROS)

Run the bundled architecture check from the sub-skill directory (or invoke
that script with its absolute path) from any caller project:

```bash
python scripts/td3_model_smoke.py --state-dim 24 --action-dim 2 --batch-size 4 --device cpu
```

The script contains small, side-effect-free Actor/Critic definitions distilled
from the source. It checks output shapes, actor bounds, both critic outputs,
finite values, target-copy equivalence, and a forward/backward pass. It does
not import `train_velodyne_td3.py`, `velodyne_env.py`, `rospy`, or Gazebo. A
CUDA check is optional and should be run only when the selected PyTorch build
reports CUDA availability:

```bash
python scripts/td3_model_smoke.py --device auto --check-cuda
```

This is an architecture gate, not evidence that ROS can launch or that a robot
can train.

## 2. Replay fixture smoke

```bash
python scripts/replay_buffer_smoke.py --capacity 3 --requested-batch 5
```

The deterministic fixture adds four identifiable transitions to a capacity-3
buffer, verifies oldest-entry eviction, verifies that a request larger than the
buffer returns all three entries, checks reward/done column shapes, and checks
that `clear()` resets the count. The fixture mirrors the source behavior and
uses no repository imports.

## 3. Bounded training adaptation

When a researcher needs a training smoke beyond architecture:

1. Keep `state_dim=24`, `action_dim=2`, `max_action=1`; replace only the
   simulator transition provider with a deterministic synthetic/mock provider.
2. Prefill at least `batch_size` transitions, or deliberately use a smaller
   batch only when testing the source's underfill behavior. Avoid accidentally
   interpreting a partial batch as a full batch in benchmark results.
3. Run a fixed, small number of transitions and training calls, for example
   2–5 episodes of at most 8–20 steps, with `max_timesteps` bounded. Use a
   temporary output root and an explicit TensorBoard `log_dir`.
4. Keep the source bootstrap convention: terminal transitions bootstrap with
   zero, while an artificial time-limit transition has `done_bool=0` so it can
   bootstrap. Do not conflate environment `done` with the training mask.
5. Seed Python, NumPy, and PyTorch. Record device, package versions, dimensions,
   hyperparameters, and the synthetic fixture definition.
6. After the run, check that actor/critic state dictionaries load, each actor
   output is `(2,)` for one observation, Q outputs are scalar per batch item,
   TensorBoard event files exist, and the result history is readable as NumPy.

Do not make a synthetic smoke depend on `GazeboEnv`: constructing it starts a
`roscore` subprocess, initializes a ROS node, launches Gazebo, creates ROS
publishers/subscribers, and waits for simulator services. The inspection host
has none of those facilities.

## 4. Full simulator training handoff

A ROS-capable sibling workflow must handle catkin setup, the launch file,
`GazeboEnv`, reset/step services, and process cleanup. Once it supplies a live
environment, use that workflow's approved training adapter and pass
absolute/configured output directories instead of depending on a checkout
working directory. Start TensorBoard against the same explicit run directory.
Full training defaults to millions of steps and can be long-running; require an
explicit user-approved budget before launching.

The source evaluates every 5,000 environment steps, after episode completion,
using 10 episodes with a 501-step loop guard. It saves a checkpoint and NumPy
evaluation history when that cadence is reached, and evaluates/saves once more
at the end. This cadence is owned here only as a training artifact contract;
actual evaluation behavior and simulator launch belong to the cross-linked
sibling skills.

## 5. Artifact layout

The source assumes execution from `TD3`:

```text
pytorch_models/TD3_velodyne_actor.pth
pytorch_models/TD3_velodyne_critic.pth
results/TD3_velodyne.npy
runs/events.out.tfevents....
```

`pytorch_models/description` says the directory holds the two network
parameters, `results/description` says it holds the NumPy result file, and
`runs/description` says it holds TensorBoard files. A safer adaptation should
put all three under one caller-selected output root, create directories before
writing, and avoid writing into the skill installation tree.
