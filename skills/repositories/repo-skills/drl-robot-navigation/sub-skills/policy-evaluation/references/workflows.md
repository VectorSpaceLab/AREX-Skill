# Bounded policy-evaluation workflows

These workflows separate artifact compatibility from simulator execution. They are
plans for a downstream controlled runner; they are deliberately not a setup script and
do not invoke the source checkout.

## Workflow A: artifact-only gate

Use when ROS/Gazebo is unavailable, when reviewing a submitted checkpoint, or before
allocating simulator time.

1. Choose the exact model directory and base name from the run request.
2. Run the bundled checker in inventory mode:

   ```text
   python scripts/check_policy_artifacts.py --model-dir <model-dir> --name <base>
   ```

3. Require an actor file. Treat a critic-only directory as a hard failure.
4. For a checkpoint that has not been trusted or produced by the current run, repeat
   with `--load-state-dict`. Keep the default byte limit unless a documented artifact
   review approves a different bound.
5. Record actor status, critic status, expected architecture, and any loader limitation.
   Stop here if the actor is absent or incompatible.

This workflow can establish that a file set is structurally usable; it cannot establish
that ROS messages, Gazebo physics, or navigation behavior work.

## Workflow B: one bounded simulator evaluation

Before starting, the run owner must provide a simulator with the required ROS master,
launch resources, Velodyne and odometry topics, reset/pause/unpause services, and a
clean process-termination plan. The environment constructor in the source evidence
starts processes and the source test has import-time side effects, so a controlled runner
must avoid importing that test module as a library.

Use explicit values, for example:

```text
episodes = 3
max_steps_per_episode = 500
wall_clock_deadline = explicitly recorded
exploration_noise = 0
seed = 0 (if deterministic comparison is desired)
```

For each episode:

1. Reset and require a finite 24-element state.
2. Run the actor in evaluation/no-grad mode.
3. Require a finite two-element normalized action in `[-1, 1]` (allow only a tiny,
   documented numerical tolerance if the framework exposes one).
4. Convert to the environment command `[ (a0 + 1) / 2, a1 ]` and step once.
5. Accumulate reward and record `goal`, `collision`, `sim_done`, or `time_limit`.
6. Stop at the first simulator termination or at step 500, whichever comes first.
7. Abort on invalid state/action, simulator service failure, process timeout, or operator
   stop. Preserve partial data and mark the episode/run incomplete.

Do not use exploration noise or random-near-obstacle actions for actor evaluation. Those
are training behaviors and would make a deterministic policy score incomparable.

## Workflow C: repeated bounded comparison

For comparing two or more actor checkpoints, keep the following fixed: environment
build and launch assets, episode count, 500-step maximum, seed policy, observation/action
validation, action conversion, and metric definitions. Run artifact checks for all
models before starting any simulator. Do not interleave an incompatible model with a
valid run merely to obtain a score.

Minimum report per checkpoint:

- base name and immutable artifact identity (for example, size and digest recorded by
  the caller),
- device and architecture contract,
- completed and incomplete episode counts,
- per-episode return and length,
- goal/collision/time-limit counts,
- invalid-state/action and watchdog counts,
- simulator readiness failures, if any.

A comparison is inconclusive if checkpoints used different bounds, if any run was
truncated without being labeled, or if the environment gate was not satisfied.

## Pseudocode contract

```text
artifact = check_artifacts(model_dir, base, optional_safe_load=True)
require artifact.actor.compatible
require simulator_ready()
for episode in range(episodes):
    state = env.reset()
    require finite(state) and len(state) == 24
    for step in range(1, 501):
        normalized = actor(state, no_grad=True, eval=True)
        require finite(normalized) and len(normalized) == 2
        command = [(normalized[0] + 1) / 2, normalized[1]]
        next_state, reward, done, target = env.step(command)
        record(reward, done, target, step)
        if done: break
        require finite(next_state) and len(next_state) == 24
        state = next_state
    else:
        record_termination("time_limit")
```

The `while True` behavior in the reference test is intentionally absent from this
contract. An evaluator must have both an episode bound and an external watchdog.
