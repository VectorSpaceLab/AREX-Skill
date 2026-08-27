# MDP component troubleshooting

## Action dimension mismatch

- Count matched actuator/tendon/site targets in the order used by the action
  term.
- Use `preserve_order=True` when policy output order is externally defined.
- Check whether the action is joint-, tendon-, or site-based.
- Confirm `scale`, `offset`, and `clip` mappings use names that actually match
  the action targets.

## Robot does not move or moves too much

- `XmlActuatorCfg` preserves XML behavior; check gear, control range, and
  command field in the MJCF.
- Built-in position/PD actuators need sensible stiffness/damping and effort
  limits.
- Explicit PD/DC actuators need saturation/velocity limits tuned to the robot.
- `JointPositionActionCfg` with `use_default_offset=True` makes zero policy
  output hold the default pose; this is often desired for locomotion.
- `RelativeJointPositionActionCfg` makes zero output hold the current pose.

## Reward signs or scaling look wrong

- Penalties should usually have negative weights.
- `scale_rewards_by_dt=True` changes cumulative scale when `decimation` or
  timestep changes.
- Log individual reward terms before judging the total.
- Check whether a task-specific reward returns an exponential tracking reward,
  a penalty, or a shaped multiplicative score.

## Command observations are missing

- Add the command generator to `env.commands`.
- Add an observation term that reads the same command name.
- For tracking tasks, provide a local motion file or a registry artifact before
  expecting command data to exist.
- Custom command terms must handle per-env reset/update so partial resets do
  not corrupt every environment.

## Event or randomization runs at the wrong time

- Use `reset` for episode initial state.
- Use `startup` for persistent per-world randomized fields.
- Use `interval` for mid-episode pushes or slowly wandering parameters.
- Use `step` only for cheap operations.
- Route MuJoCo model-field randomization to the domain-randomization reference
  because field expansion and graph recapture can matter.

## Learned actuator file problems

`LearnedMlpActuatorCfg` loads a TorchScript network file. If initialization
fails:

- verify the file exists in the user's project or package assets
- check that it was saved for the current torch version/device expectations
- confirm `input_order`, `history_length`, and scaling match the model training
- test on a tiny environment before using thousands of worlds

## Target regex failures

If an actuator/action/term cannot find targets, debug names in this order:
entity key, local joint/body/geom/site name, composed scene name, regex scope,
then ordering. Avoid broad `.*` patterns for action dimensions until the target
set is known.
