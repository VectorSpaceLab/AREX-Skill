---
name: training-and-evaluation
description: "Train, evaluate, and export HumanoidVerse policies with PPO,
  PPODeltaA, Hydra overrides, simulator selection, motion tracking, locomotion,
  and delta-action workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-and-evaluation

Use this sub-skill when a user asks for HumanoidVerse policy training, checkpoint evaluation, ONNX export, simulator/backend choice, Hydra override selection, phase-based motion tracking, locomotion, open-loop delta-action training, or closed-loop delta-action finetuning.

Run ASAP training/evaluation entry points from the repository checkout root. The bundled helper scripts are skill-root-relative and accept `--repo-root <asap-checkout>`. The repo entry points are scripts, not package modules: `python humanoidverse/train_agent.py ...` and `python humanoidverse/eval_agent.py ...`. Do not use `python -m humanoidverse.train_agent`, because the source imports `utils.config_utils` relative to the `humanoidverse/` script directory.

## Do not use this sub-skill for

- SMPL/AMASS shape fitting, motion retargeting, robot XML fitting, or MuJoCo retargeting visualization. Use [`../motion-retargeting/SKILL.md`](../motion-retargeting/SKILL.md).
- Sim2sim or sim2real runtime control, ROS2/Unitree bridges, joystick control, and live robot deployment. Use [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md).
- Generic PPO theory or unrelated simulator stacks that are not launched through this repository's HumanoidVerse Hydra configs.

## Required reading order

1. Read the root router: [`../../SKILL.md`](../../SKILL.md).
2. Read root install/backend guidance before choosing a simulator: [`../../references/install-and-backends.md`](../../references/install-and-backends.md).
3. Read this sub-skill's command recipes: [`references/workflows.md`](references/workflows.md).
4. Read CLI/config/class behavior before changing Hydra groups or checkpoint/export assumptions: [`references/api-reference.md`](references/api-reference.md).
5. If anything fails, read this sub-skill's predictable failures first: [`references/troubleshooting.md`](references/troubleshooting.md), then root troubleshooting [`../../references/troubleshooting.md`](../../references/troubleshooting.md).

## Safe preflight checks

These checks do not start simulator training:

```bash
# Confirm that Hydra can list config groups.
python humanoidverse/train_agent.py --help
python humanoidverse/eval_agent.py --help

# Build a command without executing it.
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow motion-tracking \
  --motion-file humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl

# Turn a training command into a Hydra composition-only smoke check.
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow motion-tracking \
  --motion-file humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl \
  --cfg-job
```

Run the root doctor script before runtime commands to get a single import/help report:

```bash
python scripts/asap_doctor.py --repo-root <asap-checkout> --section core
```

## Route by prompt

| User asks for | Use | Primary recipe |
| --- | --- | --- |
| "train motion tracking", "imitate this motion", "CR7 policy" | `train_agent.py` with `+exp=motion_tracking` | [`references/workflows.md#motion-tracking-training`](references/workflows.md#motion-tracking-training) |
| "train locomotion" or "test IsaacGym install with locomotion" | `train_agent.py` with `+exp=locomotion` | [`references/workflows.md#locomotion-training-and-smoke-test`](references/workflows.md#locomotion-training-and-smoke-test) |
| "train delta action model" | `train_agent.py` with `+exp=train_delta_a_open_loop` | [`references/workflows.md#open-loop-delta-action-training`](references/workflows.md#open-loop-delta-action-training) |
| "finetune with delta A" or "closed-loop delta action" | `train_agent.py` with `+exp=train_delta_a_closed_loop` and `algo.config.policy_checkpoint=...` | [`references/workflows.md#closed-loop-delta-action-finetuning`](references/workflows.md#closed-loop-delta-action-finetuning) |
| "evaluate checkpoint", "visualize policy" | `eval_agent.py +checkpoint=...` | [`references/workflows.md#checkpoint-evaluation`](references/workflows.md#checkpoint-evaluation) |
| "export ONNX" | `eval_agent.py +checkpoint=...`; export happens before the eval loop | [`references/workflows.md#onnx-export`](references/workflows.md#onnx-export) |
| "which Hydra overrides?" | Choose config groups and scalar overrides from the workflow table | [`references/api-reference.md#hydra-config-groups`](references/api-reference.md#hydra-config-groups) |

## Backend selection rules

- Default to `+simulator=isaacgym` for README-aligned training recipes when IsaacGym Preview 4 is installed and CUDA is available.
- Use `+simulator=isaacsim` only in an IsaacLab/IsaacSim environment with `omni.isaac.lab`; the entry points launch an IsaacSim app before importing Torch.
- Use `+simulator=genesis` only after installing `genesis-world` in the same environment.
- `+simulator=mujoco` is present as a Hydra config, but deployment/control recipes live in [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md); do not infer that every training recipe has been validated on MuJoCo.
- The verified inspection environment had CUDA-capable Torch, Hydra, `humanoidverse`, `asap` distribution metadata, `onnx`, and `onnxruntime`, but did not have IsaacGym, Genesis, or IsaacLab installed. Treat actual simulator launch as backend-gated.

## Common outputs

- Training experiment directory: `logs/<project_name>/<timestamp>-<experiment_name>-<log_task_name>-<robot_type>/`.
- Training checkpoints: `model_<iteration>.pt` in the experiment directory; `PPO.save()` writes actor, critic, optimizer states, iteration, and infos.
- Saved training config: `config.yaml` in the experiment directory; Hydra's own run directory is `<experiment_dir>/.hydra/` and `train.log` is written there.
- Training renderings: `<experiment_dir>/renderings_training/` when the simulator records them.
- Evaluation logs: `logs_eval/<eval_name>/<eval_timestamp>/config.yaml` and `eval.log` under the Hydra eval run directory.
- Evaluation renderings: `<checkpoint_dir>/renderings/ckpt_<N>/`, where `<N>` comes from `model_<N>.pt`.
- ONNX export: `<checkpoint_dir>/exported/model_<N>.onnx`; `eval_agent.py` exports before it enters the infinite evaluation loop.
- Evaluation motion recording with `+opt=record`: `<checkpoint_dir>/motions/<save_note>_<eval_timestamp>.pkl` or `<eval_timestamp>_<dump_motion_name>.pkl`; those dumps include an `action` key useful for delta-action datasets.

## Cross-links

- Root router: [`../../SKILL.md`](../../SKILL.md).
- Root install and backend notes: [`../../references/install-and-backends.md`](../../references/install-and-backends.md).
- Root troubleshooting: [`../../references/troubleshooting.md`](../../references/troubleshooting.md).
- Motion retargeting: [`../motion-retargeting/SKILL.md`](../motion-retargeting/SKILL.md) for producing motion `.pkl` files consumed by motion-tracking training.
- Sim2real deployment: [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md) for using exported ONNX policies in MuJoCo/ROS2/Unitree runtime flows.
