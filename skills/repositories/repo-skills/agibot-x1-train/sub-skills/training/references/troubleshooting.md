# X1 DH training troubleshooting

## Backend and install gates

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `ModuleNotFoundError: isaacgym` | Isaac Gym Preview 4 is not installed or not on `PYTHONPATH` | Mark **BLOCKED_REQUIRED_BACKEND**, install the licensed Preview 4 package, then verify its own example; never stub the import |
| Isaac Gym imports but `make_env` fails in `acquire_gym`, `create_sim`, or PhysX | incompatible CUDA/driver/PhysX or simulator flags | verify the Isaac Gym example, GPU/driver, `--physics_engine`, `--sim_device`, and `--use_gpu_pipeline`; do not call this a PPO failure |
| install resolver cannot satisfy the stack | legacy Python/PyTorch/NumPy mismatch | use the README's Python 3.8, PyTorch 1.13.1/CUDA 11.7, NumPy 1.23 family as a compatibility starting point; record any deliberate deviation |
| `tensorboard` or `wandb` import fails | optional logging package absent | install the package required by the selected runner or use static/CPU checks; do not claim training logging was verified |
| asset file not found | X1 resources are missing or root substitution is wrong | confirm the package checkout includes the X1 URDF/resource layout and that `LEGGED_GYM_ROOT_DIR` resolves to the installed package root; do not substitute MuJoCo files |

`humanoid/envs/x1/x1_dh_stand_env.py`, `BaseTask`, and `LeggedRobot` import
Isaac Gym directly. A successful `training_preflight.py --shape-smoke` does not
clear any of these gates.

## Configuration and command failures

| Symptom | Diagnosis and recovery |
| --- | --- |
| `Task with name: ... was not registered` | use exact `x1_dh_stand`; registration happens in `humanoid.envs.__init__`, which imports the task and registers config instances |
| `KeyError` for a gait name | every `commands.gait` entry must have a matching `commands.gait_time_range` key; use only the known gait helpers or add both the resampling method and range |
| command tensor has unexpected width | raw storage is 4 wide, while `command_input` is 5 wide; actions remain 12 wide. Do not use `env.num_commands=5` as an action dimension |
| CNN `view`/Conv1d or linear mismatch | reconcile `frame_stack`, `num_single_obs`, `short_frame_stack`, `in_channels`, kernels/strides, `lh_output_dim`, and actor input. Default values are 66, 47, 5, 66, `[6,4]`, `[3,2]`, 64, and 3102/302 |
| critic matrix multiplication mismatch | default critic width is 219 and estimator reference is `critic_obs[:,199:202]`; if height measurements are enabled, add `num_height` per privileged frame and recompute both widths/index |
| action shape mismatch | `ActorCriticDH` returns `[batch,12]`; the environment expects `[num_envs,12]`. Do not pass a flattened 12*envs vector |
| unexpected initial behavior | reset randomizes DOF position ±0.1, starts gait phase at 0 or 0.5, clears history, and samples the gait schedule. Check the seed and randomization before changing rewards |
| robot falls immediately | native simulation issue or an incompatible checkpoint/config, not a CPU shape issue. Check asset, PD gains, dt/decimation, action scale, limits, and whether an ablation disabled stabilizing rewards/randomization |

`X1DHStandEnv` uses `heading_command=False`: it writes yaw directly, so do not
interpret `commands[:,3]` as an active heading target in the default task.

## Training, memory, and throughput

- A default rollout stores 24 steps for 4096 environments with 3102-wide actor
  observations plus privileged data and policy statistics. Reduce `--num_envs`
  for a bounded startup test if GPU memory is insufficient; do not change
  dimensions to hide an OOM.
- Use `--headless` for training. Rendering is not a training correctness check
  and can consume resources.
- If CUDA OOM occurs during environment creation, reduce `--num_envs`, ensure
  the GPU pipeline/device choice is intentional, and verify simulator contact
  limits. If OOM occurs during PPO, reduce environment count before changing
  the policy architecture, then report the altered batch size.
- `max_iterations` is policy updates, not simulator steps. Each update collects
  `24 * num_envs` transitions. A one-iteration command is a plumbing smoke,
  not a convergence result.
- If the run is very slow, distinguish Isaac Gym simulation/terrain startup,
  rollout collection, and PPO learning time using the runner's printed timing
  and TensorBoard performance fields.
- If logging crashes while training otherwise starts, inspect `log_dir`,
  TensorBoard availability, and the runner's `writer` initialization. Do not
  delete the last checkpoint before copying or validating it.

## PPO and checkpoint failures

| Symptom | Action |
| --- | --- |
| `Rollout buffer overflow` | runner must add exactly at most `num_steps_per_env=24` transitions before `compute_returns`/`update`; inspect early loop exits or duplicate `process_env_step` calls |
| NaN action/value/loss | check finite observations, command ranges, policy std, reward scale, torque clipping, and domain-randomization ranges; reduce only one factor at a time and keep a fresh run name |
| estimator loss has wrong slice | default reference linear velocity is privileged indices 199:202; the estimator consumes the last 235 actor values and predicts 3 values |
| adaptive KL changes learning rate unexpectedly | inherited `schedule='adaptive'` changes the learning rate when measured KL crosses desired-KL thresholds; log the effective rate before comparing runs |
| checkpoint `KeyError` | a DH checkpoint needs `model_state_dict`; runner saves optimizer and estimator optimizer keys too. Rebuild the same architecture before loading |
| checkpoint loads but outputs are wrong | verify task/config dimensions, normalization, history ordering, default joint angles, and checkpoint provenance; do not mix a policy checkpoint with a changed frame stack |
| resume chooses surprising file | inspect the run directory. The config sentinel `load_run=-1` chooses the sorted last run, but CLI `--load_run` is parsed as a string, so omit it for configured latest behavior or pass an exact run name; `checkpoint=-1` chooses the sorted last filename containing `model`; `exported` is excluded as a run candidate |
| resumed result differs from uninterrupted run | registry resume passes `load_optimizer=False`; optimizer and estimator optimizer states are not restored, even though the checkpoint contains them |
| no final checkpoint after interruption | use the latest complete periodic checkpoint; a final save occurs only after `learn` exits normally |

## Static and CPU alternatives

When Isaac Gym is absent, use:

```bash
python scripts/training_preflight.py --check-config
python scripts/training_preflight.py --shape-smoke
python scripts/training_preflight.py --print-command --num-envs 1 --max-iterations 1
```

A config report can be produced from bundled distilled facts even when importing
`humanoid.envs` is impossible. If a Torch smoke fails, classify the failure as
policy/storage compatibility and preserve the exact traceback; do not try to
make it pass by installing a fake `isaacgym` module. The helper exits nonzero
for failed requested checks, making it suitable for CI/static verification.
