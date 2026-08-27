# Task-specific MDP patterns

Built-in task families demonstrate how mjlab combines reusable MDP terms with
robot/task-specific command and reward logic.

## Cartpole

Cartpole tasks are the smallest examples for learning the config pattern:

- one XML-wrapped entity
- an `XmlActuatorCfg` motor
- one effort action
- actor/critic observation groups with cart position, pole angle, and velocities
- a smooth reward matching the swingup/balance objective
- PPO runner config under experiment name `cartpole`

Use cartpole when you need a compact reference for custom environment authoring
or CLI parsing without a complex robot.

## Velocity locomotion

Velocity tasks combine locomotion commands, foot/contact sensors, terrain, and
robot posture rewards.

Common ingredients:

- `UniformVelocityCommandCfg` for twist commands.
- command observations via `generated_commands`.
- tracking rewards for linear and angular velocity.
- upright/posture, angular momentum, joint limits, action-rate, foot-air-time,
  foot-clearance, foot-slip, and soft-landing terms.
- terrain curricula on rough-terrain tasks.
- foot height/contact/self-collision sensors.

Use velocity tasks as templates for command-conditioned locomotion.

## Motion tracking

Tracking tasks imitate reference motions:

- `MotionCommandCfg` loads motion data from a local file or registry artifact.
- observations compare motion anchor/body states with robot states.
- rewards penalize global anchor pose, relative body pose, body velocities,
  self-collision, and joint limits.
- custom runner logic can register or resolve motion artifacts.

Use tracking tasks when the user has motion data, a local checkpoint, or W&B
motion artifacts. Validate motion file format before blaming the policy.

## Manipulation

Manipulation/lift tasks use object/goal commands and optional camera
observations:

- `LiftingCommandCfg` or multi-cube lifting commands.
- `JointPositionActionCfg` for arm control.
- staged position and bring-object rewards.
- object/goal distance observations.
- camera RGB/depth/segmentation observations for vision variants.
- contact sensors for ground/object interaction.

Use manipulation tasks as templates for command-conditioned object interaction
and vision observations.

## Porting from another task

1. Start from the nearest built-in task family.
2. Replace the entity/asset first and keep observation/action dimensions small.
3. Validate `SceneEntityCfg` target names.
4. Add rewards/terminations one group at a time.
5. Run `play --agent zero` or config/help checks before training.
6. Increase `scene.num_envs` and GPU count only after the tiny task is stable.
