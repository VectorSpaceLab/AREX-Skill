# Troubleshooting matrix

Classify the symptom first. Keep simulator failures separate from static
configuration failures; most fixes below require an Isaac Gym Preview 4 host
and cannot be proven here.

| Symptom | Likely cause | Safe diagnosis / next action |
|---|---|---|
| `ModuleNotFoundError: isaacgym` | Isaac Gym Preview 4 was not installed, its Python path is not active, or the environment is wrong | Use `check_runtime.py`; install the Preview 4 package in its intended environment and rerun an approved Isaac Gym example there. Do not infer simulator readiness from `torch` import. |
| `ModuleNotFoundError` for `params_proto`, `gym`, `ml_logger`, or similar | Repository dependencies are missing or incompatible | Compare the package requirements in `setup.py` with the active environment. Install the repository package separately from Isaac Gym. Avoid changing old pinned versions without recording the compatibility risk. |
| PyTorch imports but `torch.cuda.is_available()` is false | CPU-only wheel, incompatible/missing NVIDIA driver, hidden GPU, or CUDA environment issue | Run `check_runtime.py`; inspect the driver and selected PyTorch wheel on the target machine. This remains a CUDA/backend problem, not proof that Isaac Gym is installed. |
| `isaacgym` imports but environment construction fails | Isaac Gym binary/driver mismatch, unsupported GPU, PhysX/GPU pipeline failure, missing dependency, or bad configuration | Capture the first Isaac Gym error on the target host, reduce `env.num_envs`, use `headless=True`, and check assets. Do not call it a successful install until an approved simulator example and environment smoke test run. |
| CUDA out-of-memory or VRAM exhaustion | Default Go1 settings use 4000 environments; README guidance is about 10 GB minimum and roughly 12 GB for default training | Reduce `Cfg.env.num_envs` for a smoke test, keep actor/privileged/history dimensions unchanged, and use headless mode. This is a runtime tuning step; training/checkpoint changes belong to `training-and-policy`. |
| URDF or mesh not found | Wrong repository root, unresolved `{MINI_GYM_ROOT_DIR}`, broken relative mesh path, or incomplete checkout | Run `check_runtime.py --repo-root ... --strict-assets`; verify `resources/robots/go1/urdf/go1.urdf` and its relative `../meshes` files. Do not “fix” by pointing at an unrelated robot asset. |
| Actuator network asset not found | `control.control_type="actuator_net"` selected without `resources/actuator_nets/unitree_go1.pt` | Use `P` for the documented Go1 configuration if actuator fitting is not the task, or route actuator-network work to `actuator-network`. The static checker reports the optional file. |
| `num_privileged_obs (...) != the number of privileged observations (...)` | Enabled `priv_observe_*` flags and declared `env.num_privileged_obs` disagree; the source builder asserts exact equality | Count only branches actually appended by `compute_observations`, update the declared width and downstream learner together, then run an Isaac Gym-equipped smoke test. The current host cannot execute this assertion. |
| Actor observation size mismatch | A flag such as `observe_vel`, command count, yaw, clock, gait, contact, or previous-action history changed without updating `env.num_observations` and noise-vector assumptions | Recompute the concatenation order from `configuration.md`; validate a JSON summary with `validate_config.py`. Route learner architecture/checkpoint changes to `training-and-policy`. |
| Terrain creation error or bad origins | Invalid `mesh_type`, terrain proportions/dimensions, heightfield bounds, or height measurement with `mesh_type='none'` | Check the terrain fields and choose one of `None`, `plane`, `heightfield`, or `trimesh` as supported by the source. Disable height measurement for `none`; use an Isaac Gym host for actual terrain verification. |
| Terrain appears flat or curriculum is unexpected | `config_go1` explicitly sets `curriculum=False`, `terrain_noise_magnitude=0.0`, and a single final terrain proportion, or non-heightfield terrain disables curriculum in `_parse_cfg` | Inspect the effective config order: base `Cfg`, `config_go1`, then user overrides. Do not assume base defaults survived the Go1 specialization. |
| Viewer does not appear | `headless=True`, no graphics device, missing display forwarding, or viewer/driver issue | First validate headless construction on a supported Isaac Gym machine. For GUI, use a target with display access and `headless=False`; rendering remains unverified here. |
| Headless run fails in a container | Graphics/driver exposure, EGL/display setup, GPU pipeline issue, or camera/video code still active | Use the target environment's approved headless setup, reduce environments, disable video recording where appropriate, and check GPU visibility. Do not run container display scripts from this host. |
| `HistoryWrapper` key or shape failure | Wrapped env did not provide `info["privileged_obs"]`, or actor observation/history dimensions drifted | Verify the exact four-value `VelocityTrackingEasyEnv.step` contract and the history size `num_observation_history * num_obs`; reset history on shape changes. |
| `scripts/test.py` fails before printing `Simulating step` | Missing Isaac Gym, old dependency mismatch, GPU/backend failure, or script-specific effective config | Use static checks first. The README's test is a target-host simulator check and must not be run in this Isaac Gym-absent construction environment. |

## Escalation boundaries

- PPO algorithms, learner observation dimensions, checkpoints, and training
  memory belong to `training-and-policy`.
- Actuator-network assets, fitting, and learned actuator behavior belong to
  `actuator-network`.
- Unitree connection, low-level control, calibration, and physical safety
  belong to `robot-deployment`.
- This sub-skill can explain configuration and prerequisites but cannot certify
  any of those downstream operations.
