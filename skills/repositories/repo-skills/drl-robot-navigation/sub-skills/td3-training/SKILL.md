---
name: td3-training
description: "Guide TD3 model construction, bounded training adaptations,
  replay-buffer use, checkpoints, and TensorBoard outputs for the DRL
  robot-navigation implementation without requiring ROS or Gazebo for model
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TD3 training

Use this skill when a researcher needs to understand or adapt the repository's
TD3 training contract. It is an operating guide, not a simulator launcher and
not an evaluation-loop guide. Keep ROS/Gazebo startup and policy evaluation in
the repository's corresponding sibling skills; use the cross-links supplied by
the top-level router rather than duplicating them here.

## Operating contract

- The intended observation has 20 Velodyne bins followed by four robot values:
  distance to goal, relative heading, linear action, and angular action. The
  model therefore uses `state_dim=24` and `action_dim=2`.
- Actor outputs are normalized actions in `[-1, 1]^2`. Before the environment
  step, convert them to `[linear=(a0+1)/2, angular=a1]`; do not store this
  converted pair as the replay action.
- Training is off-policy TD3 over transitions
  `(state, normalized_action, reward, done_for_bootstrap, next_state)`.
- The implementation assumes a process working directory containing
  `pytorch_models/`, `results/`, and `runs/`. Treat those as configurable
  output locations in any safe adaptation, rather than relying on a checkout
  path.

Read the focused references before changing behavior:

- [api-reference.md](references/api-reference.md) — architecture and method
  contracts, including source quirks.
- [workflows.md](references/workflows.md) — bounded model smoke, training
  adaptation, artifacts, and TensorBoard workflow.
- [hyperparameters.md](references/hyperparameters.md) — exact defaults and
  the distinction between method defaults and training-call values.
- [troubleshooting.md](references/troubleshooting.md) — predictable failures
  and diagnosis without launching the simulator.

## Safe use sequence

1. Establish the required state/action dimensions and selected device. Run the
   bundled `scripts/td3_model_smoke.py` first; it reimplements only the Actor
   and Critic shape contract and never imports ROS, Gazebo, or repository
   modules.
2. Validate replay semantics with
   `scripts/replay_buffer_smoke.py`. In particular, verify eviction, the
   underfilled-batch behavior, done flags, and the state/action array shapes.
3. For real training, provide a ROS/Gazebo-capable environment through the
   separate simulator workflow. This skill does not claim that simulator
   execution is available on a CPU-only inspection host.
4. Preserve normalized actions in the buffer, use a separate environment-action
   conversion, and preserve the time-limit bootstrap convention described in
   the references.
5. Keep training bounded during development: use a small step/episode budget,
   a prefilled synthetic or mock transition source, an explicit log directory,
   and a temporary checkpoint/result directory. Do not use the repository's
   multi-million-step defaults for a smoke test.
6. Check the resulting actor/critic state-dict shapes and output files before
   attempting any evaluation. Evaluation cadence and ROS launch belong to the
   sibling evaluation/simulator skills.

## Algorithm decisions to preserve

The actor is `24 -> 800 -> 600 -> 2`, with ReLU on the two hidden layers and
`tanh` on the output. The critic has two independent Q branches. Each branch
projects state through `24 -> 800`, combines a 600-wide state projection with a
600-wide action projection, and emits one scalar. Actor and critic targets are
initialized from their online networks. Adam is used with PyTorch's implicit
constructor defaults.

Each critic update forms a target action from the actor target, adds Gaussian
policy noise clipped to `[-noise_clip, noise_clip]`, clamps the action to
`[-max_action, max_action]`, and uses the smaller target Q. The critic minimizes
the sum of two MSE losses. On every `policy_freq`-th local iteration, the actor
is updated through the first critic Q and both target networks receive a soft
update. The source resets this local iteration at each call to `TD3.train`, so
record that quirk when reproducing cadence.

Exploration adds Gaussian noise to the normalized actor action and clips it.
When enabled, the near-obstacle branch can hold one random angular action for
8–14 steps while forcing normalized linear action to `-1`. See the exact slice
and probability conditions in the hyperparameter reference; do not silently
replace this with environment-space noise.

## Outputs and compatibility

Training creates actor and critic state-dict files under `pytorch_models`, a
NumPy evaluation history under `results`, and scalar events under `runs`.
Names, relative-path assumptions, missing optimizer state, and load-device
compatibility are intentional review points. A portable adaptation should use
`map_location` when loading, validate state-dict keys/shapes, and pass an
explicit TensorBoard `log_dir`.

The checked host lacks ROS Noetic, Gazebo, `roscore`, `roslaunch`, `catkin_make`,
and ROS message modules. Therefore only CPU model/replay checks (and optional
CUDA tensor checks when independently available) are in scope here. Never
report a successful simulator training run based on these bundled smokes.

## Evidence anchors

The operating contract is distilled from the repository `README.md`,
`TD3/train_velodyne_td3.py`, `TD3/replay_buffer.py`, and the output-directory
notes in `TD3/runs/description` and `TD3/pytorch_models/description`.
`TD3/test_velodyne_td3.py` was used only to confirm the actor checkpoint-loading
shape contract. These paths are provenance, not runtime dependencies.

## Handoff checklist

Before handing a TD3 adaptation to another skill, report:

- state/action dimensions and device;
- whether transitions were normalized and whether the buffer was sufficiently
  populated;
- exact bounded iteration/episode budget and random seeds;
- actor/critic output and checkpoint shape checks;
- TensorBoard and result paths, with no accidental checkout-path dependency;
- any unresolved ROS/Gazebo or PyTorch serialization limitation.
