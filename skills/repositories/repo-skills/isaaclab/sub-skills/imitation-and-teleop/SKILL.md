---
name: imitation-and-teleop
description: "Use imitation-and-teleop for Isaac Lab teleoperation,
  demonstration capture, Mimic annotation, SkillGen-style synthetic generation,
  and Cosmos-based visual augmentation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Imitation and Teleoperation

Use this sub-skill when the task is about collecting demonstrations, annotating subtask signals, synthesizing new demos, or using teleoperation and XR devices in Isaac Lab.

## Route here for

- Recording demonstrations from a teleoperated task.
- Choosing between native teleop, SpaceMouse, keyboard, or Isaac Teleop / CloudXR paths.
- Annotating demonstrations for Mimic-style replay and data generation.
- Generating synthetic demonstrations with Mimic or SkillGen.
- Converting HDF5 demonstrations to MP4 and back for visual augmentation.
- Building Cosmos prompts and merging dataset variants.

## Use other subskills for

- Launching the simulator, picking a backend, or setting camera/visualizer options: `../simulation-core/SKILL.md`.
- Asset selection for the robot or sensor being teleoperated: `../assets-and-sensors/SKILL.md`.
- Environment discovery or preset selectors used by the task: `../tasks-and-presets/SKILL.md`.

## Working references

- `references/teleop-and-data-collection.md` covers human demonstrations, devices, and recording preconditions.
- `references/mimic-and-skillgen.md` covers annotation, synthetic generation, and skill-local signal requirements.
- `references/cosmos-augmentation.md` covers HDF5/MP4 conversion, prompt generation, and visual augmentation.
- `references/dataset-formats.md` records file-layout and naming conventions.
- `references/troubleshooting.md` covers device, dependency, and data-format failures.
- `scripts/inspect_imitation_workflow.py` prints a safe phase summary and prerequisite checklist.
- `scripts/generate_cosmos_prompt.py` adapts the prompt-template generator used in the augmentation workflow.
- `scripts/merge_hdf5_datasets.py` adapts the dataset merge helper for Isaac Lab-style `data/demo_*` HDF5 files.

## Acceptance checks

- Name the required device family or augmentation backend for the requested workflow.
- State whether the task needs manual subtask start/termination annotation or only terminal completion signals.
- Identify the expected dataset naming/layout before a conversion or merge step.
- Call out Linux-only, XR-only, or GPU-only constraints when the workflow requires them.
