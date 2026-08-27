# RL, policy, and MPC bridge API reference

## Purpose

Use this reference for tensor shapes, policy construction, checkpoint format,
and the conversion between a policy action and the controller's MPC weights.
It intentionally omits low-level finite-state-machine and solver details; use
[mpc-control](../../mpc-control/SKILL.md) for those APIs.

## Hydra/RSL-RL construction

The training workflow follows this object sequence:

1. Hydra composes the root/task configuration.
2. The selected task class is instantiated with the resolved task dictionary,
   `sim_device`, `graphics_device_id`, and `headless`.
3. The PPO class config is converted from the `LeggedCfgPPO` class hierarchy to
   a dictionary and updated from `seed`, `task_name`, and `max_iterations`.
4. `OnPolicyRunner(env, train_cfg_dict, log_dir, cfg.rl_device)` creates an
   `ActorCritic` with `env.num_obs`, `env.num_privileged_obs` (or `env.num_obs`),
   and `env.num_actions`.
5. Training calls `learn(num_learning_iterations=runner.max_iterations,
   init_at_random_ep_len=False)`.
6. Evaluation calls `get_inference_policy(device=env.device)`, obtains
   `env.get_observations()`, then calls `env.step(actions)`.

The runner's `load(path)` expects a serialized mapping with
`model_state_dict`, `optimizer_state_dict`, `iter`, and `infos`; it restores
both model and optimizer by default. The inference policy switches the actor
to evaluation mode and exposes `act_inference`.

## Simulator task interface

The vector task exposes the usual operations used by RSL-RL:

- `get_observations()` -> observation tensor shaped `[num_envs, 48]`;
- `get_privileged_observations()` -> `None` for these tasks;
- `step(actions)` -> observation, privileged observation, rewards, reset flags,
  and an extras mapping;
- `reset()` -> initial observation/privileged-observation pair;
- `num_envs`, `num_obs`, and `num_acts` properties.

`step` clips the incoming action tensor to the configured action bound,
performs `controlFrequencyInv` physics steps (default 1), refreshes the state,
and returns tensors on the configured RL device. It also exposes timeout info
in `extras["time_outs"]`.

## Observation builders

The simulator task's 48-value ordering is:

```text
base position (3)
body-frame linear velocity * linearVelocityScale (3)
body-frame angular velocity * angularVelocityScale (3)
[command_x, command_y, command_yaw] * [lin, lin, ang] (3)
(dof_pos - default_dof_pos) * dofPositionScale (12)
dof_vel * dofVelocityScale (12)
actions (12)
```

The task source keeps this order identical for A1, Aliengo, and Go1. The
policy-side bridge has a deliberate-looking but important difference:
`WeightPolicy.compute_observations(dof_states, se_result, _commands,
_actions)` creates:

```text
vBody * linearVelocityScale (3)
omegaBody * angularVelocityScale (3)
-ground_normal_yaw (3)
commands * [lin, lin, ang] (3)
dof_states["pos"] * dofPositionScale (12)
dof_states["vel"] * dofVelocityScale (12)
_actions (12)
```

Both total 48, but they are not interchangeable. The bridge's `StateEstimate`
fields must supply `vBody`, `omegaBody`, and `ground_normal_yaw`; the DOF state
mapping must supply 12 position and 12 velocity values; commands must be three
values; and `_actions` must be the previous 12-value MPC-weight action.

## WeightPolicy

`WeightPolicy(task="Aliengo", checkpoint="/path/to/user/checkpoints/Aliengo/model.pt",
num_envs=1)`:

- registers the same Hydra resolver family as training and composes the task;
- reads the task normalization scales;
- constructs `ActorCritic(48, 48, 12, **policy_cfg)` on CUDA;
- loads `loaded_dict['model_state_dict']` and sets the actor to evaluation mode;
- keeps a one-agent `[1, 48]` observation tensor; and
- exposes `compute_observations(...)` followed by `step()`.

`step()` runs `act_inference` under `torch.no_grad()`, clips the action to
`[-1,1]`, affine-maps it with the MPC parameters, and returns a CPU NumPy
array of shape `(12,)`. `Parameters.policy_print_time` controls optional
inference timing output.

The loader first tries the supplied checkpoint. On any exception it falls back
to the latest model chosen under the task run root. This broad exception path
can hide a malformed explicit checkpoint, so validate the path and checkpoint
identity before relying on fallback behavior. The training entry point
normalizes its Hydra `cfg.checkpoint`, but `WeightPolicy` calls `torch.load`
with the constructor argument itself; pass a path resolved from the actual
launch directory when constructing `WeightPolicy` directly.

## Action-to-MPC mapping

The common affine transform is:

```text
mapped = action * [4,4,4, 20,20,20, 1,1,1, 1,1,1]
                 + [5,5,5, 50,50,50, 1,1,1, 1,1,1]
```

After clipping, the ranges are `[1,9]` for the first three values,
`[30,70]` for the next three, and `[0,2]` for the last six. These values are
passed as MPC parameters, not torques. In the vector environment, each
parallel controller receives `[command_x, command_y, command_yaw]`, the 12
mapped values, and one appended zero, for 16 values total. The controller's
command layer interprets the first three as motion commands and the remaining
13 as non-negative MPC weights.

In the standalone policy runner, the same 12 values are stored as the first
12 MPC weights and the controller command object appends the thirteenth zero.
Changing the scale/constant arrays changes the meaning of every existing
checkpoint and should be treated as a retraining boundary.

## Checkpoint safety and compatibility

Before loading a checkpoint, verify all of the following without executing
untrusted model code:

- the path exists and is a regular file;
- the task identity matches the checkpoint's training task;
- the serialized artifact is from the RSL-RL runner family and contains
  `model_state_dict` (and, for resume, optimizer/iteration state);
- the actor expects 48 observations and 12 actions;
- the hidden dimensions and activation match the current policy config; and
- the observation ordering and action-to-MPC mapping have not changed.

The bundled checker performs only the first item and validates the requested
configuration. It intentionally does not deserialize checkpoints because
PyTorch checkpoints use pickle semantics. Use a trusted, isolated environment
and an approved artifact inspection procedure for the remaining checks.
