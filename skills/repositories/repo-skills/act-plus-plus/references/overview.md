# ACT++ overview

## When to read

Read this when you need a compact map of ACT++ repository workflows before choosing a sub-skill.

## Public workflow map

| Workflow | Main inputs | Main outputs | Owning sub-skill |
| --- | --- | --- | --- |
| Simulated scripted data generation | Task name (`sim_transfer_cube_scripted`, `sim_insertion_scripted`), dataset directory, episode count | `episode_<idx>.hdf5` files with qpos/qvel/action/images | [simulation-data](../sub-skills/simulation-data/SKILL.md) |
| Episode visualization / replay | Existing episode HDF5 dataset | MP4 videos, qpos plots, replay videos | [simulation-data](../sub-skills/simulation-data/SKILL.md) |
| Mirroring / compression / truncation | Existing uncompressed or compressed HDF5 episodes | `mirror_episode_<idx>.hdf5`, compressed dataset directories, truncated dataset directories | [simulation-data](../sub-skills/simulation-data/SKILL.md) |
| ACT / CNNMLP / Diffusion training | HDF5 episode dataset selected through task config, policy class, checkpoint directory, CUDA backend | `config.pkl`, `dataset_stats.pkl`, `policy_step_*`, `policy_last.ckpt`, `policy_best.ckpt`, eval summaries | [policy-training](../sub-skills/policy-training/SKILL.md) |
| ACT eval / rollout | Policy checkpoint + `dataset_stats.pkl`, task config, sim or real env | success/return summaries and optional rollout videos | [policy-training](../sub-skills/policy-training/SKILL.md) |
| ACT VQ latent model training | A trained VQ ACT checkpoint and dataset | `latent_model_*` checkpoints and latent loss plots | [policy-training](../sub-skills/policy-training/SKILL.md) |
| VINN feature caching | BYOL/ResNet checkpoint path using `DUMMY` camera placeholder, dataset directory | `byol_features_seed<seed>_episode_<idx>.hdf5` or `byol_cotrain_features_seed<seed>_episode_<idx>.hdf5` | [vinn-offline](../sub-skills/vinn-offline/SKILL.md) |
| VINN k selection | HDF5 episodes + matching feature files | k-selection plot and minimum validation loss report | [vinn-offline](../sub-skills/vinn-offline/SKILL.md) |

## Task names and camera sets

`SIM_TASK_CONFIGS` defines the simulated/data routing defaults:

| Task name | Intended source | Episode length | Cameras |
| --- | --- | --- | --- |
| `sim_transfer_cube_scripted` | scripted sim demos | 400 | `top`, `left_wrist`, `right_wrist` |
| `sim_transfer_cube_human` | human sim demos | 400 | `top` |
| `sim_insertion_scripted` | scripted sim demos | 400 | `top`, `left_wrist`, `right_wrist` |
| `sim_insertion_human` | human sim demos | 500 | `top` |
| `sim_transfer_cube_scripted_mirror` | mirrored scripted transfer cube | 400 | `top`, `left_wrist`, `right_wrist` |
| `sim_insertion_scripted_mirror` | mirrored scripted insertion | 400 | `top`, `left_wrist`, `right_wrist` |
| `all` | non-sim Mobile ALOHA datasets | task-dependent | `cam_high`, `cam_left_wrist`, `cam_right_wrist` |

Real-world task names are not defined in this repository; the code imports them from an external Mobile ALOHA runtime when the task name does not start with `sim_`.

## Backend model

- Sim rendering: DM Control + MuJoCo, with an offscreen GL backend. Use `MUJOCO_GL=egl` when running headless on an EGL-capable host.
- Training/eval/VINN: CUDA is required by the repository code because tensors and models call `.cuda()` directly.
- CPU-only workflows: HDF5 schema inspection, compression/truncation, and plotting/visualization when the episode already contains image frames.

## Boundaries

This skill is for operating ACT++ workflows and understanding the repository's data/model contracts. It does not verify servo communication, Interbotix robot control, ROS launch/setup, or external Mobile ALOHA deployment.
