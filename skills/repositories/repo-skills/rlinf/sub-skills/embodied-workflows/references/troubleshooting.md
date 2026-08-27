# Embodied troubleshooting

Use this reference for static triage and safe remediation planning. Prefer configuration review, dependency checks, and tiny smoke settings before any expensive training or real robot run.

## Fast triage order

1. Identify task type: `embodied`, `offline`, `sft`, or `embodied_eval`.
2. Identify env family, model family, algorithm/loss, and whether reward/data collection is enabled.
3. Run the bundled config checker on the exact YAML.
4. Confirm dependency environment matches the selected **model + env** pair.
5. Resolve placeholders and environment variables.
6. For hardware, stop at the real-world safety gate before touching controllers.

## Simulator assets and optional dependencies

| Symptom | Likely cause | Safe checks/fixes |
| --- | --- | --- |
| Import error for simulator backend | Optional env package not installed for the selected family | Install only the selected env/model extra, not all extras. Confirm the Python used by Ray workers is the same environment. |
| Asset not found for ManiSkill/LIBERO/RoboTwin/RoboCasa/BEHAVIOR/Polaris | Asset root, cache, or env variable is missing/stale | Check config asset fields and required environment variables; replace `/path/to/...` placeholders; do not hard-code private paths into shared configs. |
| LIBERO path still points to an old install | LIBERO-like packages cache absolute paths on first import | Reset/reinstall the LIBERO asset config in the active environment; ensure Ray is restarted after environment changes. |
| RoboTwin task fails immediately | `ROBOTWIN_PATH`, assets path, or seed file mismatch | Confirm `ROBOTWIN_PATH`, `env.*.assets_path`, and train/eval seed files belong to the same asset version. |
| BEHAVIOR/OmniGibson startup failure | OmniGibson data/key path or Isaac Sim path is missing | Verify `OMNIGIBSON_*`, `ISAAC_PATH`, `EXP_PATH`, `CARB_APP_PATH`, and headless flags before launch. |
| IsaacLab task id error | `env_cfg.init_params.id` not registered | Use a registered task id or route source extension to extension-development. |
| World-model env produces invalid rollouts | Missing world-model checkpoint/init data or mismatched VLA unnormalization | Verify `opensora`/`wan` checkpoint path, initialization dataset, reward model type, and model `unnorm_key`. |

## EGL, MuJoCo, rendering, and videos

Common rendering variables for headless simulator runs:

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
```

Triage:

- If MuJoCo/GL context creation fails, confirm the variables are set **before** Python/Ray workers start.
- If videos are empty or black, verify camera keys, obs mode, and `video_cfg.save_video`/`video_base_dir`.
- If rendering works interactively but fails under Ray, the worker environment likely missed the variables; restart Ray after exporting them.
- If video writing crashes, check `imageio[ffmpeg]`/OpenCV availability in the worker environment and reduce video frequency.

## Action dimension and `ROBOT_PLATFORM`

The embodied helper concept defaults `ROBOT_PLATFORM` to `LIBERO`; other policies may require `ALOHA`, `BRIDGE`, RoboTwin-specific, or real-world action schemas.

Symptoms:

- action tensor shape mismatch,
- gripper dimension mismatch,
- rollout action chunk has wrong final dimension,
- policy normalizes/unnormalizes with the wrong key,
- real robot tries to execute a malformed command.

Safe checks:

```bash
# Set before workers start, using the platform expected by the model/data.
export ROBOT_PLATFORM=<LIBERO|ALOHA|BRIDGE|...>
```

Also verify:

- `actor.model.num_action_chunks` and `env.*.max_steps_per_rollout_epoch` divisibility.
- OpenPI/OpenPI_RLinf normalization stats (`assets_dir`, `asset_id`, `unnorm_key`) match the target embodiment.
- Real-world `no_gripper`, gripper type, dual-arm vs single-arm schema, and action horizon.
- RLT Stage 1/Stage 2 configs use the same feature model and action semantics.

## Ray worker and placement failures

This sub-skill does not own Ray setup syntax, but embodied configs often reveal what to check:

| Symptom | Static/config cause | Next step |
| --- | --- | --- |
| Actor group launches, env group missing | `component_placement.env` absent or points to nonexistent node group | Route placement syntax to setup-and-cluster; ensure env component has an owner. |
| Reward worker never starts | `reward.use_reward_model` true but no reward placement/group/model fields | Add reward placement and model/API config, or disable reward model. |
| Real-world env worker starts on GPU node unexpectedly | `env.node_group` or placement points to the wrong group | Fix component placement before any robot action. |
| Worker imports fail only under Ray | Ray captured old Python/env vars | Restart Ray after activating/installing the intended environment and exporting variables. |
| Async runner hangs | Long-running env/rollout/actor channel mismatch, reward channel issue, or worker exception hidden in per-worker logs | Inspect per-worker logs through operations-evaluation-debugging; statically verify async loss type is supported. |
| Training pipeline raises unsupported error | `runner.use_training_pipeline` with SAC/DAgger/NFT/unsupported async path | Disable pipeline or use a supported PPO/GRPO-style FSDP config. |

## Memory and throughput issues

| Pressure point | Knobs |
| --- | --- |
| GPU OOM in actor | Reduce `actor.micro_batch_size`, sequence length, env count, rollout batch, or enable gradient checkpoint/offload where supported. |
| GPU OOM in rollout/VLM reward | Lower rollout batch, sampling length, reward `infer_micro_batch_size`, or use API reward placement on separate resources. |
| Simulator GPU memory | Reduce `env.train.total_num_envs`, use `env.enable_offload`, separate env from actor placement, disable videos. |
| Slow environment reset | Consider `runner.overlap_env_bootstrap` only when compatible; be aware it can increase memory pressure. |
| Long-tail env latency | `runner.enable_decoupled_mode` can decouple env and rollout workers when `env_world_size >= rollout_world_size` and P2P constraints are satisfied. |
| Large data collection I/O | Use `only_success`, smaller FPS, fewer envs, shorter horizons, and confirm disk capacity. |

## Data collection mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No files written | `data_collection.enabled` false, save dir invalid, episodes never complete | Enable block under the active train/eval env, verify `save_dir`, and ensure `auto_reset`/horizon allows completion. |
| Only success or only failure labels | `only_success` set incorrectly or success key not found | For reward datasets, collect both classes; inspect `info` success keys. |
| LeRobot export fails shape checks | image/state/action dimensions vary across episodes | Use a consistent env/task/camera/action schema or split datasets by schema. |
| VLM Trend preprocessing empty | missing dual-view image keys or window too large | Ensure `main_images` plus `extra_view_images`/`third_view_images` exist and reduce window size only if method still makes sense. |
| Replay buffer not usable for RLPD | missing `intervene_flags` or action schema mismatch | Recollect or convert with explicit schema validation; do not silently train on ambiguous data. |

## Reward model failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| ResNet reward predicts all zeros/ones | class imbalance, threshold too high/low, train split bad | Rebalance preprocessing, verify labels, tune `reward_threshold`, inspect validation accuracy. |
| VLM Trend reward returns interval reward forever | history buffer never reaches `min_history_size` or keys missing | Check `history_size`, `min_history_size`, `input_interval`, `history_keys`, and env observations. |
| VLM parser invalid outputs | prompt/parser mismatch or sampling too stochastic | Use deterministic sampling, stricter parser params, shorter max tokens, and inspect raw answers. |
| API reward fails to connect | `reward.api.api_base` missing or managed server placement invalid | Provide endpoint or route SGLang/router setup to setup-and-cluster. |
| Reward overwhelms env reward | reward scales/weights mismatched | Revisit `reward_weight`, `env_reward_weight`, parser scalar values, and `reward_coef`. |

## Offline/SFT pitfalls

- `runner.task_type: offline` with online embodied assumptions: env/rollout are optional and mostly for eval; dataset fields drive training.
- D4RL task not installed: install D4RL-compatible dependencies for the selected env, or switch dataset type.
- RECAP/STEAM tag mismatch: `returns_tag`/`advantage_tag` must line up across stages.
- CFG data mixes different embodiments or action dimensions: split or normalize consistently before policy optimization.
- OpenPI/DreamZero SFT normalization stats are absent or from a different robot: calculate/check stats before online RL.
- Qwen-VL SFT key mismatch: dataset columns must match prompt/answer/image key fields.

## Real hardware safety triage

If anything unexpected happens during a real-world run:

1. Stop the robot using the operator's normal emergency procedure.
2. Do not retry automatically.
3. Record config name, model checkpoint, robot IP/order, target pose, action schema, and last operator observation.
4. Verify placement and environment variable mapping offline.
5. Reproduce with dummy/simulation if available before returning to hardware.

Never suggest changing target poses, disabling validation, or bypassing controller safety checks to make a run proceed.
