# Experiment families

## Mimic

Use Mimic for direct reference-motion imitation. Typical configs include flat terrain and complex terrain variants, with rewards for global body position/rotation, velocities, root height, power, contact matching, and action smoothness. It is the best starting point for motion tracking.

## ADD

ADD uses adversarial differential discriminators to balance tracking errors dynamically. Use it when the task asks about adversarial tracking objectives or reward balancing without manual tracking-weight tuning.

## AMP

AMP learns a style prior from motion data while optimizing task rewards. Use it for stylized motion control or when the task is not strict frame-by-frame tracking.

## ASE

ASE learns a latent skill space from diverse motion data. It is unsuitable for single-clip tasks because the latent space needs varied behaviors.

## MaskedMimic

MaskedMimic controls motion through masked/inpainted future-motion observations. It requires a pretrained Mimic expert and is appropriate when sparse keyframes, partial motion control, or generative policy behavior is central.

## GPC and PEFT

GPC trains a discrete latent prior from tracker FSQ tokens and adapts that prior with PEFT. Use the dedicated GPC reference for checkpoint and staged-training rules.

## Steering and path-following

Steering and path-following tasks combine task control components with motion priors or tracking components. Use these when the user asks for target direction/speed, path following, keyboard target control, or task reward wiring.

## Choosing an experiment

- Need to imitate a MotionLib: start with Mimic.
- Need terrain robustness: choose a complex-terrain or domain-randomized variant.
- Need sim2real/sim2sim G1 tracker: choose a BeyondMimic/domain-randomized G1 tracker-style config.
- Need a reusable motion prior: staged GPC/PEFT.
- Need new observations/rewards: implement pure tensor kernels and wire them as `MdpComponent` instances.

## Experiment-file contract

An experiment file typically provides:

- `terrain_config(args)`;
- `scene_lib_config(args)`;
- `motion_lib_config(args)`;
- `env_config(robot_cfg, args)`;
- optional `configure_robot_and_simulator(robot_cfg, simulator_cfg, args)`;
- optional `agent_config(robot_cfg, env_cfg, args)`;
- optional `apply_inference_overrides(...)`.

This Python-first config design replaced Hydra/YAML inheritance and makes config logic explicit and inspectable.
