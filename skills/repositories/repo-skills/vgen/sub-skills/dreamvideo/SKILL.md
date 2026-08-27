---
name: dreamvideo
description: "Route DreamVideo subject, motion, and joint customization
  workflows, plus DreamVideo metric calculation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# dreamvideo

Use this sub-skill when a VGen task is about DreamVideo subject personalization, motion personalization, or joint subject-plus-motion composition. It covers the training and inference configs, the adapter checkpoints they produce, and the DreamVideo metric helper.

Do **not** use this route for I2VGen image-to-video, InstructVideo reward fine-tuning, or the generic text-to-video families unless the task is specifically comparing them to DreamVideo.

## Fast route

1. Decide which DreamVideo stage the user wants:
   - **Subject learning**: learn an identity/appearance adapter from `configs/dreamvideo/subjectLearning/*.yaml`.
   - **Motion learning**: learn a motion adapter from `configs/dreamvideo/motionLearning/*.yaml`.
   - **Joint inference**: load both subject and motion configs with `configs/dreamvideo/infer/joint_*.yaml`.
2. Read the config pair first. DreamVideo inference uses `subject_cfg` and/or `motion_cfg` to layer in adapter settings before the main inference config is merged.
3. Check whether the user has the adapter checkpoints the config expects:
   - `identity_adapter_index` or `identity_adapter_path`
   - `motion_adapter_index` or `motion_adapter_path`
4. For customization outputs, confirm the custom list rows are in the DreamVideo `image|||prompt` format and that `test_data_dir` points at the matching image directory.
5. For evaluation, use `scripts/calc_metrics.py` with explicit CLIP and DINO assets. The metric helper is not usable without those extra files.

## What this sub-skill covers

- DreamVideo subject learning and motion learning configs.
- DreamVideo inference configs for subject-only, motion-only, and joint runs.
- Adapter-merging logic, `use_textInversion`, `appearance_guide_strength_*`, and `inverse_noise_strength`.
- DreamVideo custom list files under `data/custom/infer/` and training examples under `data/custom/train/`.
- DreamVideo metric calculation for CLIP-T, CLIP-I, DINO-I, and Temporal Consistency.

## References

- Detailed workflow map, config layering, list formats, and adapter-selection notes: `references/workflows.md`.
- Failure modes and fixes for adapter paths, placeholder checkpoints, metric dependencies, and memory issues: `references/troubleshooting.md`.
- Bundled helpers:
  - `scripts/dump_adapter_keys.py`
  - `scripts/calc_metrics.py`

## Handoff notes for root integration

DreamVideo is the customization route that most clearly needs a reusable adapter-key helper and an explicit metric wrapper. Keep those helpers self-contained and do not depend on the original `test_func/` or `metric/` files at runtime.
