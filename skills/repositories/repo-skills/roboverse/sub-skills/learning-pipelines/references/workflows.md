# Learning Workflow Decision Guide

## Select the stack

| Need | Route | Main contract |
|---|---|---|
| Compact on-policy/off-policy baseline | CleanRL PPO/SAC/TD3 | Gym-like task registration, vector observations/actions, explicit seeds and logging |
| High-throughput off-policy control | FastTD3 | task class from registry, normalized observations, replay buffer, actor/critic checkpoint |
| Standard library baseline | Stable-Baselines3 PPO | Gymnasium-compatible environment/wrapper |
| Locomotion/tracking | RSL-RL | vectorized task wrapper, runner config, usually GPU-scale execution |
| Image/action imitation | IL dataset + policy + runner | dataset keys/shapes, normalizer, policy config, checkpoint/output directory |
| OpenVLA/SmolVLA/pi0 | VLA adapter/evaluator | external model/checkpoint, processor, camera/image/action convention, often credentials/downloads |
| RL-to-demo or warm start | fusion pipeline | trajectory conversion, demo contract, BC checkpoint, then RL stage |

## Common preflight

1. Register/import the task and reset one environment.
2. Record observation/action names, shapes, ranges, dtype, device, and camera
   ordering. Separate actor observations from privileged/critic observations.
3. Run one zero/bounded action and validate reward, terminated, truncated, and
   `info` shapes.
4. For datasets, validate one episode/window without augmentations.
5. Instantiate policy and optimizer on CPU with a tiny batch and run one forward
   (and, when safe, one backward) pass.
6. Move to the requested GPU/backend only after the CPU contract passes.
7. Add rendering, WandB, compilation, distributed training, and large batch sizes
   one feature at a time.

## FastTD3-specific facts

The FastTD3 implementation resolves the task class from MetaSim's registry and
updates its scenario with `robots`, `sim`, `num_envs`, `headless`, and cameras.
Configuration includes device selection, normalization, replay, actor/critic
sizes, update cadence, evaluation, saving, and optional rendering. GPU requests
fail clearly if neither CUDA nor MPS is available. AMP is active only when the
configured accelerator is available.

Observation normalization is stateful. Keep normalizers in training mode for
new rollout observations and freeze them while normalizing replay samples so
statistics are not double-counted. Persist actor, critics, target critic,
normalizer states, config, and global step together.

## IL and VLA progression

- Install a policy's exact dependency set in an isolated environment when it
  conflicts with the broad `learn`/`vla` extras.
- Convert data only after fixing units, frame conventions, image channel order,
  action dimension/range, episode boundaries, and train/validation split.
- VLA adapters often add TensorFlow datasets, LeRobot, Transformers, model hubs,
  or policy-specific repositories. Treat tokens, network, model weights, and
  disk/VRAM as explicit prerequisites.
- Evaluation must name the simulator, robot, task, checkpoint, camera keys,
  normalization and action-unscaling path. Do not imply cross-simulator policy
  transfer from an observation-only check.
