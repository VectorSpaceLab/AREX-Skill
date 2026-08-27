---
name: refinement-and-export
description: "Operate Make-It-3D refinement, test rendering, multi-view
  generation, point-cloud/mesh export, and output troubleshooting after coarse
  training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Refinement and Export

Use this sub-skill after a coarse Make-It-3D workspace exists, or when a user asks about `--refine`, `--test`, videos, checkpoints, multi-view images, point clouds, OBJ mesh export, or export-specific dependencies.

## What This Sub-Skill Covers

- Refinement command construction and the source control-flow quirk around `--final --refine`.
- Test rendering from checkpoints and output locations.
- Mesh export with `--save_mesh` and its `xatlas`/`nvdiffrast` requirements.
- Point-cloud/multi-view/refine utilities and PyTorch3D/Open3D dependencies.
- Output validation and troubleshooting after partial/interrupted runs.

Setup/input issues belong to [environment-and-inputs](../environment-and-inputs/SKILL.md). Coarse command generation belongs to [coarse-training](../coarse-training/SKILL.md).

## Required Reads and Scripts

- Read [references/workflow.md](references/workflow.md) for refine/test/export command flow.
- Read [references/outputs-and-export.md](references/outputs-and-export.md) for workspace files, videos, OBJ/texture outputs, and dependency ownership.
- Read [references/troubleshooting.md](references/troubleshooting.md) for common refine/export failures.
- Run [scripts/build_refine_export_commands.py](scripts/build_refine_export_commands.py) to generate copyable commands.

## Command Pattern

```bash
python /path/to/skill/sub-skills/refinement-and-export/scripts/build_refine_export_commands.py \
  --workspace NAME --ref-path REF_ALPHA.png --text "object prompt" --save-mesh
```

The helper emits:

- a refine command using `--final --refine` to satisfy the inspected source nesting;
- a test render command with `--test`;
- an optional mesh export command with `--test --save_mesh`.

## Safety and Verification

- Do not start refinement unless the coarse workspace has checkpoints and the user accepts additional GPU time.
- Do not promise OBJ texture export until `xatlas` and `nvdiffrast` import in the runtime environment.
- Treat PyTorch3D/Open3D/contextual-loss import errors as refinement/export blockers, not generic Python issues.
- Check generated outputs before deleting or rerunning a workspace. Interrupted training can still leave useful checkpoints.
