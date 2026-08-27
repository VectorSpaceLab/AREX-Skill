---
name: mesh-extraction
description: "Plan, run, and validate Neuralangelo isosurface mesh extraction
  from trained checkpoints with safe resolution, block size, texturing,
  filtering, bounds, and PLY checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Neuralangelo Mesh Extraction

Use this sub-skill when a trained Neuralangelo checkpoint already exists and the task is to extract, tune, or validate an isosurface mesh. It covers the repository's mesh extraction CLI, config/checkpoint/output relationships, marching-cubes resolution planning, block-wise GPU memory tradeoffs, `transforms.json` bounds handling, texturing, largest-connected-component filtering, and PLY sanity checks.

Do not use this sub-skill to prepare images/COLMAP/transforms data or to create checkpoints. Route data conversion, camera poses, `transforms.json` creation, and bounding-sphere adjustment to `data-preparation`. Route training, config generation, checkpoint selection, resume behavior, and training-time quality issues to `training-and-configs`.

## Evidence basis

This operating guidance is distilled from the repository's isosurface extraction guidance, data-processing notes for `transforms.json` and bounding-sphere adjustment, training/config entry points, Neuralangelo base/custom configs, mesh extraction implementation, mesh utilities, dataset coordinate normalization, and verified import/help checks for the relevant Python modules and CLIs. Runtime instructions point to bundled skill helpers; execution still requires a user's target Neuralangelo project root because the project code owns the actual model implementation.

## Load-bearing facts

- Mesh extraction delegates to the target Neuralangelo project root's extraction entry point against a training config and checkpoint; use the root bundled wrapper when invoking it from this skill.
- The config must resolve `cfg.data.root/transforms.json`; the script reads `sphere_center`, `sphere_radius`, and optionally `aabb_range` from that JSON.
- The checkpoint is loaded with optimizer/scheduler state disabled, then the model is placed in eval mode and coarse-to-fine SDF levels are set from the checkpoint evaluation iteration.
- `--resolution` controls global marching-cubes sample spacing (`2 / resolution`); it mainly affects detail, runtime, and output size.
- `--block_res` controls the per-block lattice size; it mainly affects peak GPU memory and block count, not the target detail.
- `--textured` exports vertex colors by evaluating the RGB head at mesh vertices; it is slower and uses more memory.
- `--keep_lcc` filters each extracted block to its largest connected component before final concatenation; it can suppress floating noise but can also remove thin or disconnected structures.
- The final PLY is exported by the master process in world coordinates after multiplying vertices by `sphere_radius` and adding `sphere_center`.

## Standard workflow

1. Confirm the checkpoint/config pair:
   - Prefer the `config.yaml` saved next to the training logs for the checkpoint.
   - Confirm `data.root` in the config points to the intended scene data root.
   - Confirm that data root contains a `transforms.json` with camera frames plus `sphere_center` and `sphere_radius`.
2. Plan resolution and memory:
   - Start with a smoke extraction at low resolution before a production-quality run.
   - Reduce `block_res` first for CUDA out-of-memory; reduce `resolution` when final mesh size/runtime is too large or the scene only needs coarse geometry.
   - Disable `--textured` until geometry is acceptable.
3. Run extraction:
   - Single process: use `python ... --single_gpu`.
   - Multi-GPU: use `torchrun --nproc_per_node=<N>` without `--single_gpu`.
   - Always make `--output_file` include a parent directory, because the bundled extractor creates the parent directory before export.
4. Validate the result:
   - Check console counts for nonzero vertices/faces and, when textured, colors.
   - Run the bundled `scripts/validate_mesh_file.py` on the produced PLY.
   - Inspect whether the mesh is cropped, shifted, hollow, noisy, or missing thin structures before treating it as a final reconstruction.

## Command template

```bash
CONFIG=logs/<group>/<name>/config.yaml
CHECKPOINT=logs/<group>/<name>/<checkpoint>.pt
OUTPUT=mesh_outputs/<scene>_r2048_b128.ply
RESOLUTION=2048
BLOCK_RES=128
GPUS=1

python ../../scripts/run_neuralangelo_entrypoint.py \
  --project-root <neuralangelo-root> \
  --entrypoint extract-mesh -- \
  --config=${CONFIG} \
  --checkpoint=${CHECKPOINT} \
  --output_file=${OUTPUT} \
  --resolution=${RESOLUTION} \
  --block_res=${BLOCK_RES}
```

Add `--textured` only after geometry looks reasonable. Add `--keep_lcc` only when removing floating components is worth the risk of losing thin or disconnected geometry.

## Bundled helpers

- `scripts/plan_mesh_extraction.py` performs a safe, static preflight of config/checkpoint/output/transforms paths, estimates normalized lattice dimensions and block counts, and can print a ready-to-run extraction command. It does not import or execute Neuralangelo.
- `scripts/validate_mesh_file.py` performs basic PLY header validation with the Python standard library and can optionally load the mesh with `trimesh` when installed.

## Reference map

- `references/workflows.md` — preflight, command recipes, resolution/block planning, texturing/LCC guidance, validation workflow, and usability case ideas.
- `references/mesh-api-and-outputs.md` — extractor CLI flags, internal data flow, `transforms.json` coordinate handling, output PLY semantics, and bundled helper contracts.
- `references/troubleshooting.md` — symptoms, likely causes, recovery steps, and escalation/reroute guidance.
