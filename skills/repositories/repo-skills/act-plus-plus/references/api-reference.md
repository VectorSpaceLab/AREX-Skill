# API reference

## When to read

Read this when a task asks for module-level behavior, signatures, or how data flows between ACT++ scripts. These facts were checked against source and live imports in the prepared inspection environment.

## Constants and task configuration

- `constants.SIM_TASK_CONFIGS`: maps task names to `dataset_dir`, `num_episodes`, `episode_len`, and `camera_names`.
- `constants.DT = 0.02`, `constants.FPS = 50`: simulation/control timestep facts used by video writers and rollout sleep timing.
- `constants.START_ARM_POSE`: 16-value initial bimanual arm+gripper pose used by both sim envs.
- Gripper normalization helpers convert master/puppet position and joint ranges; use them instead of hand-scaling gripper values.

## Dataset utilities

| API | Contract |
| --- | --- |
| `utils.find_all_hdf5(dataset_dir, skip_mirrored_data)` | Recursively returns `*.hdf5` files, skipping feature files and optionally mirrored episodes. |
| `utils.get_norm_stats(dataset_path_list)` | Computes action/qpos mean/std and action min/max from HDF5 episodes. Appends zero base actions if `/base_action` is absent. |
| `utils.load_data(dataset_dir_l, name_filter, camera_names, batch_size_train, batch_size_val, chunk_size, skip_mirrored_data=False, load_pretrain=False, policy_class=None, stats_dir_l=None, sample_weights=None, train_ratio=0.99)` | Builds train/val dataloaders, normalization stats, and the dataset's sim flag. Diffusion enables image augmentation and action min/max normalization. |
| `utils.EpisodicDataset(dataset_path_list, camera_names, norm_stats, episode_ids, episode_len, chunk_size, policy_class)` | Samples one observation plus a padded future action chunk. Returns `(image_data, qpos_data, action_data, is_pad)`. |
| `utils.sample_box_pose()` / `utils.sample_insertion_pose()` | Return randomized object poses used before sim reset. |
| `utils.compute_dict_mean`, `utils.detach_dict`, `utils.set_seed` | Training loop helpers. |

## Simulation APIs

| API | Contract |
| --- | --- |
| `sim_env.make_sim_env(task_name)` | Creates the joint-space environment. Before resetting transfer/insertion tasks, set `sim_env.BOX_POSE[0]` to a sampled pose. |
| `ee_sim_env.make_ee_sim_env(task_name)` | Creates the end-effector environment used by scripted policies to produce trajectories. It randomizes object poses during reset. |
| `scripted_policy.BasePolicy(inject_noise=False)` | Open-loop policy base. First call generates a trajectory from the first timestep; later calls interpolate waypoints. |
| `scripted_policy.PickAndTransferPolicy` | Generates transfer-cube waypoints using right-hand pickup and left-hand handoff. |
| `scripted_policy.InsertionPolicy` | Generates peg/socket insertion waypoints. |

Observation dictionaries contain `qpos`, `qvel`, `env_state`, and `images`. The joint-space env renders `top`, `left_wrist`, and `right_wrist`; the EE env renders `top` and also exposes `mocap_pose_left`, `mocap_pose_right`, and `gripper_ctrl` for the scripted rollout-to-replay pipeline.

## Policy/model APIs

| API | Contract |
| --- | --- |
| `policy.ACTPolicy(args_override)` | Builds DETR-VAE ACT policy and optimizer. Training call returns `l1`, `kl`, and `loss`; inference returns action chunks. Requires CUDA in repository workflows. |
| `policy.CNNMLPPolicy(args_override)` | Builds a CNN+MLP policy. Training call returns MSE loss; inference returns one action. The source code's CNNMLP internals contain an `action_dim` implementation pitfall, so validate before relying on it. |
| `policy.DiffusionPolicy(args_override)` | Builds robomimic visual encoders plus `ConditionalUnet1D`; training predicts noise residuals, inference denoises action chunks with DDIM scheduler. Requires a robomimic install exposing the expected diffusion policy symbols. |
| `imitate_episodes.make_policy(policy_class, policy_config)` | Dispatches `ACT`, `CNNMLP`, or `Diffusion` to the policy classes. |
| `imitate_episodes.make_optimizer(policy_class, policy)` | Uses the policy's configured optimizer for all supported classes. |
| `imitate_episodes.eval_bc(config, ckpt_name, save_episode=True, num_rollouts=50)` | Loads policy checkpoint and `dataset_stats.pkl`, runs rollouts, and writes a result text file. |
| `imitate_episodes.train_bc(train_dataloader, val_dataloader, config)` | Step-based training loop with periodic validation, eval, checkpoint saves, W&B logging, and best-checkpoint tracking. |
| `detr.main.build_ACT_model_and_optimizer(args_override)` | Builds the ACT DETR-VAE model and AdamW optimizer. Parser defaults are overridden by `policy_config`. |
| `detr.models.latent_model.Latent_Model_Transformer(input_dim, output_dim, seq_len, latent_dim=256, num_head=8, num_layer=3)` | Autoregressive transformer used by `train_latent_model.py` for VQ latent codes. |

## VINN APIs

| API | Contract |
| --- | --- |
| `vinn_cache_feature.main(args)` | Loads a BYOL checkpoint per camera, crops/resizes images to 120, extracts ResNet18 features, and writes `/features/<camera>` HDF5 files. |
| `vinn_select_k.calculate_nearest_neighbors(query_inputs, query_targets, support_inputs, support_targets, max_k)` | Computes softmax-weighted nearest-neighbor MSE for k from `1` to `max_k - 1`. |
| `vinn_eval.calculate_nearest_neighbors(curr_feature, support_inputs, support_targets, k, state_weight)` | Combines visual and state distances to predict action chunks. The source eval script hard-codes real-robot execution. |

## Important import contracts

- The repository uses top-level modules, not a conventional `act` package import. Run from a checkout root or add the checkout root to `PYTHONPATH` when importing modules by name.
- The DETR subpackage expects `detr` and also top-level `models`/`util` import aliases when installed as the repository's `detr` editable package.
- `policy.py` expects `robomimic.algo.diffusion_policy` to export both `replace_bn_with_gn` and `ConditionalUnet1D`; verify this before launching training.
