---
name: instructvideo
description: "Route InstructVideo reward fine-tuning and inference workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# InstructVideo Sub-skill

Use this sub-skill when a user asks for InstructVideo reward fine-tuning, WebVid reward-list preparation, HPSv2 reward-model setup, LoRA-vs-base InstructVideo evaluation, or the train/eval wrapper commands for this workflow.

Do **not** use this route for DreamVideo subject/motion customization, I2VGen image-to-video inference, or generic text-to-video training unless the user is explicitly comparing those workflows to InstructVideo configs or checkpoints.

## Fast routing

- **Prepare reward fine-tuning data**: read `references/workflows.md`, especially the WebVid/custom list section. Training rows are `relative_video_path|||caption`; evaluation rows are `video_or_placeholder.mp4|||caption|||frame_count`.
- **Set up reward fine-tuning**: read `references/workflows.md` for the required ModelScope assets, HPSv2 reward checkpoint, OpenCLIP asset, and LoRA/partial-DDIM knobs before launching anything.
- **Run reward fine-tuning**: use `sub-skills/instructvideo/scripts/run_train.sh` from the generated skill root. It forwards to the real InstructVideo training config and validates that the target checkout has `train_net.py` plus the config before execution.
- **Run inference/evaluation**: use `sub-skills/instructvideo/scripts/run_eval.sh`. Its presets use the actual eval config filenames in the repo and intentionally correct stale `infer_UNetSD...` spellings from the original source shell snippet.
- **Diagnose failures**: read `references/troubleshooting.md` for missing checkpoints, dependency/import errors, CUDA/NCCL issues, list-format mistakes, LoRA checkpoint mismatches, OOM, and reward over-optimization.

## Required run context

InstructVideo is a CUDA-first workflow. A usable run normally needs:

- A checkout containing the VGen runtime files (`train_net.py`, `inference.py`, `tools/`, `utils/`, and `configs/instructvideo/`).
- CUDA PyTorch plus the verified optional stack used by this route: `xformers`, `open-clip-torch`, `fairscale`, `diffusers`, `transformers`, `piq`, `scikit-image`, and OpenCV with NumPy ABI compatibility.
- InstructVideo/model assets under `models/`: the base ModelScope checkpoint, fine-tuned LoRA checkpoint when evaluating LoRA configs, Stable-Diffusion/OpenCLIP assets, and `HPS_v2.pt` for reward scoring.
- WebVid/custom training videos arranged to match `vid_reward_dataset.data_dir_list`, or a copied config whose list/data roots point at the user's own data.

## Wrapper commands

Always dry-run first when preparing a new machine or checkout:

```bash
sub-skills/instructvideo/scripts/run_train.sh --repo-root /path/to/VGen --dry-run
sub-skills/instructvideo/scripts/run_eval.sh --repo-root /path/to/VGen --dry-run --preset lora-ddim50-in-domain
```When the sub-skill has been imported outside the repository, pass the checkout explicitly:

```bash
sub-skills/instructvideo/scripts/run_train.sh --repo-root /path/to/VGen
sub-skills/instructvideo/scripts/run_eval.sh --repo-root /path/to/VGen --preset lora-ddim20-new-animals
```The wrappers accept extra trailing arguments and pass them through to `train_net.py` or `inference.py`, but prefer copying/editing YAML for typed values such as booleans, integers, lists, and nested dictionaries because the repo config parser treats command-line overrides as raw strings.

## Key configs owned by this route

- Training: `configs/instructvideo/train/reward_webvid_ani45_20_reg_vidldm_LoRA_TSNExp16Diffreward_Partial06_Trunc1_Check_ddim20.yaml`.
- LoRA evals: `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_*.yaml`.
- Base/non-LoRA evals: `configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_*.yaml`.

Do not run the original `configs/instructvideo/eval_generate_videos.sh` directly; its LoRA config names are stale. Use this sub-skill's `scripts/run_eval.sh` presets instead.
