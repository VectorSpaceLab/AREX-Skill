---
name: neuralangelo
description: "Operate Neuralangelo neural surface reconstruction workflows for
  data preparation, training, and mesh extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: "NVlabs/neuralangelo"
  source_commit: "94390b64683c067c620d9e075224ccfe582647d0"
license: NOASSERTION
---

# Neuralangelo Repo Skill

Use this skill for Neuralangelo tasks involving neural surface reconstruction from posed images, including data preparation, custom config generation, CUDA training, checkpoint handling, and mesh extraction. Neuralangelo is a CUDA/PyTorch codebase for neural SDF reconstruction; real training and extraction require a CUDA-capable environment plus a target Neuralangelo project root or installed source tree. This skill is self-contained operating knowledge: use the bundled references and scripts here instead of reopening repository docs or examples.

## Fast Triage

1. **Data is not ready**: route to `sub-skills/data-preparation/SKILL.md` for video/COLMAP/DTU/Tanks-and-Temples preparation, `transforms.json` validation, and custom YAML generation.
2. **Data and config are ready, but training must be launched, debugged, resumed, or tuned**: route to `sub-skills/training-and-configs/SKILL.md`.
3. **A trained checkpoint exists and the user wants a PLY mesh**: route to `sub-skills/mesh-extraction/SKILL.md`.
4. **The task is only about installing or checking the runtime**: read `references/installation-and-environment.md`, then run `scripts/check_neuralangelo_environment.py`.
5. **The task crosses multiple phases**: read `references/cross-skill-workflows.md` first, then open the owning sub-skill for the current blocking phase.

## Required Runtime Reality

- CUDA is required for Neuralangelo model training and production mesh extraction because the SDF hash-grid path depends on `tinycudann`/tiny-cuda-nn and CUDA tensors.
- CPU-only checks are still useful for YAML/config parsing, command planning, `transforms.json` validation, and bundled script tests.
- A target Neuralangelo project root is needed when executing the actual training or extraction entry points. The bundled scripts can validate or plan safely without importing project code unless the user explicitly asks for a runtime environment check.
- Prefer a Conda-style environment with compatible `torch`, `torchvision`, `tinycudann`, `numpy`, `PyYAML`, image/mesh packages, and optional W&B. See `references/installation-and-environment.md` for proven constraints and fallbacks.

## Repo-Level Helpers

Use these scripts from the generated skill directory, or resolve the script path from wherever the agent is running:

```bash
python scripts/check_neuralangelo_environment.py --project-root <neuralangelo-root> --json
```

This imports core runtime modules, checks CUDA, reports package versions, and verifies whether `Config`, `Model`, `Dataset`, and `Trainer` are importable from the target source tree.

```bash
python scripts/run_neuralangelo_entrypoint.py --project-root <neuralangelo-root> --entrypoint train -- --help
python scripts/run_neuralangelo_entrypoint.py --project-root <neuralangelo-root> --entrypoint extract-mesh -- --help
```

This wrapper lets agents invoke the Neuralangelo project entry points through a bundled script, keeping runtime instructions anchored inside the generated skill tree while still using the user's target source tree for the implementation.

## Sub-Skill Routing

### Data Preparation

Open `sub-skills/data-preparation/SKILL.md` when the user mentions raw video, frame extraction, COLMAP, camera poses, `transforms.json`, DTU, Tanks and Temples, scene bounding boxes, `scene_type`, `aabb_scale`, `sphere_center`, `sphere_radius`, image dimensions, exposure/white-balance embeddings, or custom YAML generation.

Key helpers:

- `sub-skills/data-preparation/scripts/plan_preprocessing_commands.py`
- `sub-skills/data-preparation/scripts/validate_transforms_json.py`
- `sub-skills/data-preparation/scripts/generate_config_from_images.py`

### Training and Configs

Open `sub-skills/training-and-configs/SKILL.md` when the user mentions launching training, `torchrun`, `--config`, `--logdir`, strict YAML overrides, `max_iter`, validation cadence, checkpoints, resume, W&B, CUDA OOM, DDP, model/data/trainer APIs, or debugging a run before extraction.

Key helpers:

- `sub-skills/training-and-configs/scripts/plan_training_command.py`
- `sub-skills/training-and-configs/scripts/inspect_config_summary.py`
- `scripts/check_neuralangelo_environment.py`

### Mesh Extraction

Open `sub-skills/mesh-extraction/SKILL.md` when the user mentions extraction, isosurface, marching cubes, PLY, `--resolution`, `--block_res`, `--textured`, `--keep_lcc`, checkpoint/config pairing, bounds, cropped meshes, shifted meshes, or validating output geometry.

Key helpers:

- `sub-skills/mesh-extraction/scripts/plan_mesh_extraction.py`
- `sub-skills/mesh-extraction/scripts/validate_mesh_file.py`
- `scripts/run_neuralangelo_entrypoint.py`

## Operating Guardrails

- Do not run full training, dataset downloads, COLMAP reconstruction, or high-resolution extraction unless the user explicitly asks and the needed data/checkpoints/resources are present.
- For expensive workflows, first plan a smoke command with low iteration counts or low extraction resolution, then ask/confirm before long runs if the user did not grant permission.
- Keep prepared-data handoffs explicit: dataset root, image subdirectory, `transforms.json` status, `scene_type`, bounds, generated config, and unresolved warnings.
- Keep training handoffs explicit: config path, logdir, GPU count, overrides, resume/checkpoint choice, W&B mode, expected outputs, and remaining blockers.
- Keep extraction handoffs explicit: config, checkpoint, output PLY, resolution, block size, texturing/LCC choice, bounds source, validation result, and memory risks.
- If the user is editing generic PyTorch or unrelated 3D vision code rather than Neuralangelo-specific workflows, do not force this skill; route to a broader repo or framework skill.

## References

- `references/repo-provenance.md`: source snapshot, evidence scope, verification baseline, and refresh signals.
- `references/installation-and-environment.md`: environment preparation, dependency constraints, CUDA/tiny-cuda-nn notes, and safe checks.
- `references/cross-skill-workflows.md`: phase-spanning recipes and handoff contracts.
- `references/troubleshooting.md`: cross-cutting installation, import, data, training, and extraction failure routing.
- `references/repo-routing-metadata.json`: structured router metadata for this generated repo skill.
