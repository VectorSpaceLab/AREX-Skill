# Mesh Extraction Workflows

This reference helps an agent plan and validate Neuralangelo isosurface extraction without relying on the original repository documentation. It assumes a trained checkpoint already exists.

## Inputs and ownership

Required inputs:

- Training config YAML, usually the `config.yaml` saved in the same log directory as the checkpoint.
- Checkpoint `.pt` file from the same run or a compatible run.
- Scene data root referenced by `data.root` in the config.
- `transforms.json` under that data root, containing at least `sphere_center`, `sphere_radius`, camera frames, and preferably `aabb_range`.
- Output path ending in `.ply` with an explicit parent directory.

Reroute boundaries:

- Missing or wrong `transforms.json`, camera pose conversion, image extraction, COLMAP, or bounding sphere authoring belongs to `data-preparation`.
- Missing checkpoint, checkpoint naming, training schedule, config generation, resuming, or training-time quality belongs to `training-and-configs`.

## Static preflight

Before running a GPU extraction, check:

1. The config exists and is the config that belongs to the checkpoint run.
2. The checkpoint exists and has a plausible `.pt` suffix.
3. `data.root` can be resolved from the config.
4. `data.root/transforms.json` exists.
5. `transforms.json` contains:
   - `sphere_center`: 3 numbers.
   - `sphere_radius`: positive number.
   - `aabb_range`: optional 3-by-2 numeric bounds; if absent, extraction uses normalized `[-1, 1]` bounds on all axes.
6. `--output_file` contains a directory component such as `mesh_outputs/scene.ply`, not just `scene.ply`.
7. The requested `resolution` and `block_res` are positive integers, and `resolution >= block_res` for ordinary production runs.

Use the bundled planner:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/plan_mesh_extraction.py \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output-file mesh_outputs/<scene>_r2048_b128.ply \
  --resolution 2048 \
  --block-res 128 \
  --gpus 1 \
  --print-command
```

The planner is safe: it reads text/JSON metadata only and never imports Neuralangelo, CUDA, Torch, or the checkpoint.

## Extraction command recipes

Prefer the bundled root wrapper for executable examples; it changes into the user's target Neuralangelo project root and delegates to the implementation there.

Single-process smoke test:

```bash
python skills/disco/neuralangelo/scripts/run_neuralangelo_entrypoint.py \
  --project-root <neuralangelo-root> \
  --entrypoint extract-mesh -- \
  --single_gpu \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output_file mesh_outputs/<scene>_smoke_r512_b64.ply \
  --resolution 512 \
  --block_res 64
```

Single-GPU production template:

```bash
python skills/disco/neuralangelo/scripts/run_neuralangelo_entrypoint.py \
  --project-root <neuralangelo-root> \
  --entrypoint extract-mesh -- \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output_file mesh_outputs/<scene>_r2048_b128.ply \
  --resolution 2048 \
  --block_res 128
```

Multi-GPU template: use the planner's `--print-command` output when distributed launch is needed, then run the printed command from the target project root after review. The wrapper is intentionally single-Python-process; distributed runs are clearer when the generated `torchrun` command is reviewed explicitly.

Textured extraction after geometry is acceptable:

```bash
python skills/disco/neuralangelo/scripts/run_neuralangelo_entrypoint.py \
  --project-root <neuralangelo-root> \
  --entrypoint extract-mesh -- \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output_file mesh_outputs/<scene>_textured_r2048_b96.ply \
  --resolution 2048 \
  --block_res 96 \
  --textured
```

Noise-suppressed extraction:

```bash
python skills/disco/neuralangelo/scripts/run_neuralangelo_entrypoint.py \
  --project-root <neuralangelo-root> \
  --entrypoint extract-mesh -- \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output_file mesh_outputs/<scene>_lcc_r2048_b128.ply \
  --resolution 2048 \
  --block_res 128 \
  --keep_lcc
```

## Choosing `resolution`

`resolution` sets the normalized sample interval as `2 / resolution`. Higher values increase geometric detail, runtime, memory pressure outside the per-block model pass, and final mesh size.

Typical progression:

| Goal | Starting value | What to check |
| --- | ---: | --- |
| CLI/config smoke | 256-512 | Nonzero PLY, checkpoint/config compatibility, no obvious coordinate shift. |
| Geometry diagnosis | 768-1024 | Bounds, surface continuity, thin structures, major holes. |
| Production baseline | 1536-2048 | Final detail and mesh size on a capable GPU. |
| Very high detail | >2048 | Use only with enough runtime/storage and after a successful lower-resolution run. |

Lower `resolution` when the output PLY is too large, extraction takes too long, the scene does not need high-frequency geometry, or the GPU/host memory fails even with conservative `block_res`.

## Choosing `block_res`

`block_res` sets the per-block lattice length. The per-block sample count is approximately `(block_res + 1)^3`, before model activations and optional texture evaluation. Lower values reduce peak GPU memory but increase the number of blocks and overhead.

Typical progression:

| GPU/memory situation | Starting `block_res` | Notes |
| --- | ---: | --- |
| Smoke or low VRAM | 32-64 | Slower, safer. Useful for diagnosing OOM. |
| Moderate VRAM | 64-96 | Good default when unsure. |
| High VRAM / faster pass | 96-128 | README examples use 128 for high-quality extraction. |
| OOM during textured pass | 32-64 | Texturing adds neural RGB and gradient work; reduce first. |

Reduce `block_res` before reducing `resolution` when the desired detail is correct but extraction runs out of GPU memory. Reduce `resolution` when final mesh detail/size is itself too high.

## Bounds and coordinate workflow

`transforms.json` defines the scene coordinate normalization used by extraction:

1. If `aabb_range` is present, it is converted to normalized bounds by subtracting `sphere_center` and dividing by `sphere_radius`.
2. If `aabb_range` is absent, extraction samples the normalized cube `[-1, 1]` along x/y/z.
3. Marching cubes runs in normalized coordinates.
4. Mesh blocks are filtered to vertices whose normalized radius is less than 1.0.
5. The final master-process mesh vertices are transformed back to world coordinates with `vertex * sphere_radius + sphere_center`.

Implications:

- A too-small `aabb_range` or sphere can crop the mesh.
- A too-large bound increases sample count and may add floating artifacts.
- The unit-sphere filter can remove geometry outside the sphere even when the AABB includes it.
- If the training config used non-default `data.readjust.center` or `data.readjust.scale`, treat extraction coordinates as a high-risk audit item: the extractor reads raw `sphere_center` and `sphere_radius` from `transforms.json` for final scaling.

## Texturing behavior

`--textured` attaches vertex colors by evaluating the trained RGB network at extracted vertices. It is useful for visual inspection and downstream textured PLY workflows, but it costs extra runtime/memory and can hide geometry issues.

Guidance:

- First extract untextured geometry.
- Once geometry is acceptable, run a textured pass at the same or slightly lower `block_res`.
- If appearance embeddings were enabled during training, the extractor uses a zero appearance vector during texture extraction; color may represent a neutral/default appearance rather than a specific training frame.
- Validate textured output by checking for vertex color properties in the PLY header and the console `colors:` count.

## Largest connected component behavior

`--keep_lcc` is a noise-removal option. In the implementation it is applied inside each marching-cubes block before blocks are concatenated, so it is not a single global largest-component pass over the final mesh.

Use it when:

- Floating noise or small disconnected pieces dominate the output.
- The target object should be one compact component.

Avoid or compare against a no-LCC run when:

- The scene has thin structures, separate parts, railings, cables, branches, or small detached components.
- Block boundaries may split a valid structure.
- You need all observed geometry for later post-processing.

## Post-extraction validation

Minimum checks:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/validate_mesh_file.py \
  mesh_outputs/<scene>_r2048_b128.ply \
  --min-vertices 1000 \
  --min-faces 1000
```

For textured output:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/validate_mesh_file.py \
  mesh_outputs/<scene>_textured_r2048_b96.ply \
  --expect-textured \
  --min-vertices 1000 \
  --min-faces 1000
```

Optional `trimesh` load check when installed:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/validate_mesh_file.py \
  mesh_outputs/<scene>_r2048_b128.ply \
  --use-trimesh \
  --print-json
```

Validation signals:

- PLY header is parseable and declares nonzero vertices/faces.
- Textured runs declare red/green/blue or equivalent color properties.
- Optional mesh load succeeds without producing an empty mesh.
- Bounding box is plausible for the scene scale implied by `sphere_center` and `sphere_radius`.
- A visual inspection shows no severe cropping, coordinate shift, or block-wise loss of thin structures.

## Hard usability case ideas

- **Bounds stress case:** construct a tiny synthetic `transforms.json` metadata file with `sphere_center`, `sphere_radius`, and an asymmetric `aabb_range`; run the planner at two resolutions and assert that normalized bounds, grid counts, and warnings change as expected without reading images or a checkpoint.
- **Textured/LCC validation case:** create minimal ASCII PLY fixtures for untextured, textured, empty, and header-corrupt meshes; assert that `validate_mesh_file.py --expect-textured` accepts only the textured fixture and that minimum vertex/face thresholds fail correctly.
