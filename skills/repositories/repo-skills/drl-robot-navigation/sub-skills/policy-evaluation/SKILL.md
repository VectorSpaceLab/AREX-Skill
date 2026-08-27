---
name: policy-evaluation
description: "Evaluate a trained TD3 actor for the Velodyne navigation
  environment with checkpoint, contract, simulator-readiness, and bounded-run
  gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Policy evaluation

Use this skill when the task is to evaluate an already-trained TD3 **actor** for the
Velodyne navigation environment. It is an evaluation and artifact-safety guide, not a
training or ROS setup guide.

## Operating contract

- **Input:** a model directory, a checkpoint base name (normally `TD3_velodyne`), and
  an evaluation request with explicit episode and step bounds.
- **Actor artifact:** `<base>_actor.pth`, a PyTorch `state_dict` for the actor below.
- **Optional companion:** `<base>_critic.pth` is produced by training, but the test
  policy needs only the actor. Treat a missing critic as an incomplete TD3 pair, not as
  an actor failure.
- **Output:** bounded episode records and aggregate metrics, plus the exact checkpoint,
  device, state/action contract, and termination policy used.
- **Hard safety rule:** never load an artifact merely to inspect its name. Run the
  bundled `scripts/check_policy_artifacts.py` first; it does not deserialize tensors
  unless `--load-state-dict` is explicitly requested.

## Policy and environment contract

The evaluator's actor is `24 -> 800 -> 600 -> 2`: `Linear(24,800)`, ReLU,
`Linear(800,600)`, ReLU, `Linear(600,2)`, and `tanh`. The 24-element observation is:

1. 20 Velodyne distance bins (`environment_dim=20`), followed by
2. distance to goal, relative heading, previous/commanded linear velocity, and
   previous/commanded angular velocity (`robot_dim=4`).

The actor returns two normalized values in `[-1, 1]`. Before the environment step, map
only the first value to linear velocity with `(a[0] + 1) / 2`; pass the second unchanged
as angular velocity. Do not feed the environment's `[0, 1]`/`[-1, 1]` command back into
the actor as a replacement for the normalized action. Assert finite numeric state of
length 24 and finite action of length 2 at every step.

The reference evaluator uses seed `0`, waits about five seconds after environment
construction, and caps an episode at **500 transitions**. A simulator `done` must end an
episode earlier; the cap must also end it when the simulator fails to terminate. Reset
before the next episode and reset the per-episode step counter. Preserve the distinction
between a goal/collision termination and a synthetic time-limit termination in metrics.

## Checkpoint gates

1. Resolve the requested model directory and base name without guessing another run.
2. Run the bundled artifact check. Confirm the actor exists, is a regular file, and has
   the exact expected name. Record critic presence separately.
3. For a new or untrusted checkpoint, opt into the bounded `--load-state-dict` check.
   It uses CPU mapping, `weights_only=True` when supported, a file-size limit, and shape
   checks; it must not fall back to unrestricted pickle loading. A missing, corrupt,
   non-tensor, extra-key, or shape-incompatible actor is a hard stop.
4. If the artifact check reports only a critic, stop: a critic cannot produce actions.
   If the critic is present but incompatible, stop the full-pair evaluation or label the
   actor-only run explicitly; never silently substitute or rename it.
5. Instantiate the actor on CPU unless CUDA availability and the requested device have
   been independently checked. The reference `torch.load` call does not set
   `map_location`, so a CUDA-origin checkpoint can fail on a CPU-only host; use the
   safe CPU-mapped validation/load path and record any device remapping. Load the actor
   state dict into the same architecture, call `eval()`, and use inference/no-grad
   execution. Record the actual device.

See `references/checkpoint-format.md` for key and shape expectations.

## Simulator readiness gate

A real run requires an operational ROS Noetic/Gazebo stack, a running ROS master,
the Velodyne and odometry topics, the navigation launch asset, and the services used by
reset, pause, and unpause. The workspace must already be built and sourced by the run
owner. Check readiness before constructing the environment; do not claim a simulator
result from a Python-only import or from a host without ROS/Gazebo/message modules.

The reference environment starts `roscore` and Gazebo in its constructor. The reference
test module constructs that environment at import time and then enters an unbounded
`while True` loop. Therefore do **not** import that module for a smoke test, and do not
start an unconstrained production evaluation. Use a controlled runner that loads the
actor and applies the same distilled contract, with an explicit episode count and a
wall-clock/step watchdog. A safe dry run can stop after artifact and architecture checks
without touching ROS.

## Bounded evaluation workflow

1. **Plan:** choose `N >= 1` episodes, `max_steps <= 500` per episode, a wall-clock
   deadline, and a cleanup/abort action. State whether this is actor-only or a complete
   TD3 artifact evaluation.
2. **Preflight:** run `check_policy_artifacts.py --model-dir ... --name ...`; add
   `--load-state-dict` only after the file-size and provenance decision. Verify simulator
   readiness separately and record failures as blocked, not as poor policy scores.
3. **Load:** build the exact actor, load only the validated actor state dict, switch to
   evaluation mode, and initialize deterministic seeds if reproducibility is desired.
4. **Run:** for each episode, reset the environment, validate the initial 24-value
   state, call the actor without exploration noise, convert the action, step the
   simulator, and record reward, collision/goal flag, and step count. Stop on `done`,
   500 steps, watchdog expiry, or operator abort.
5. **Aggregate:** report per-episode return, length, termination reason, goal count,
   collision count, time-limit count, invalid-state/action count, and timeout/abort
   status. Do not call a truncated run a completed evaluation.
6. **Clean up:** stop the controlled runner and simulator processes according to the
   host's approved procedure. Preserve the checkpoint path/base name and run bounds in
   the result record.

The original program's continuous loop is useful evidence of intended repeated testing,
not an acceptable default for automation. Never omit the bound because the simulator
usually terminates episodes.

## Failure routing

- Artifact or shape failure: fix/select a compatible actor; do not enter ROS.
- Missing ROS/Gazebo, topics, services, or launch asset: mark **environment blocked**;
  do not report zero reward or policy failure.
- State/action contract violation: abort the episode and mark the result invalid.
- Watchdog or operator stop: preserve partial records and label the run incomplete.
- A successful artifact check alone proves checkpoint compatibility only; it proves no
  navigation quality and no simulator behavior.

For predictable cases and recovery actions, use `references/troubleshooting.md`. The
bundled script is the only practical helper in this skill and is intentionally independent
of the original checkout.

## Evidence boundary

This contract was distilled from `TD3/test_velodyne_td3.py`, the actor/save/load portions
of `TD3/train_velodyne_td3.py`, `TD3/velodyne_env.py`, and the README's test procedure.
Those paths are provenance only. Runtime use should rely on this skill and its bundled
script rather than opening or executing source-checkout files.
