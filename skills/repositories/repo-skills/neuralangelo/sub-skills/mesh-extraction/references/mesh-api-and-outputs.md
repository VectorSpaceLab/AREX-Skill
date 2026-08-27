# Mesh API and Outputs

This reference summarizes the Neuralangelo mesh extraction surface that agents need at runtime.

## Extractor CLI

The extraction entry point is a Python script under the Neuralangelo project tree. It can be launched directly with `python ... --single_gpu` or through `torchrun` for distributed block extraction.

| Flag | Required | Default | Meaning | Planning notes |
| --- | --- | --- | --- | --- |
| `--config` | Yes | none | Training config YAML to load with Imaginaire `Config`. | Prefer the config saved with the checkpoint logs. Runtime config overrides can follow the known `--key=value` style accepted by the config parser. |
| `--checkpoint` | No | empty string | Checkpoint path loaded into the trainer checkpointer with optimizer/scheduler disabled. | In practice, pass an explicit `.pt` checkpoint. Empty means no useful trained surface. |
| `--local_rank` | No | `LOCAL_RANK` or 0 | Distributed local rank. | Usually managed by `torchrun`; do not set manually unless debugging launcher behavior. |
| `--single_gpu` | No | false | Skip distributed initialization. | Use with plain `python` for one-process extraction. Do not combine with multi-process `torchrun`. |
| `--resolution` | No | 512 | Marching-cubes resolution; interval is `2 / resolution`. | Higher means finer sampling and larger/slower meshes. |
| `--block_res` | No | 64 | Block-wise lattice resolution for marching cubes. | Lower reduces peak GPU memory; higher can be faster on large VRAM. |
| `--output_file` | No | `mesh.ply` | PLY output path. | Use a path with a parent directory, such as `mesh_outputs/mesh.ply`, to avoid parent-directory creation pitfalls. |
| `--textured` | No | false | Export mesh with vertex colors from the neural RGB head. | Slower and more memory-intensive; validate geometry first. |
| `--keep_lcc` | No | false | Keep only the largest connected component in each block. | Can remove noise and valid thin/disconnected structures. |

The parser accepts additional config overrides after these flags and applies them through strict recursive config update.

## Runtime data flow

1. Parse CLI flags and config overrides.
2. Load the YAML config.
3. Initialize distributed execution unless `--single_gpu` is supplied.
4. Clear `cfg.logdir` for inference.
5. Build the trainer in inference mode and load the checkpoint.
6. Set the model to eval mode.
7. Set coarse-to-fine SDF levels from the checkpoint evaluation iteration when the hash-grid schedule is enabled.
8. Read `cfg.data.root/transforms.json`.
9. Build normalized sampling bounds.
10. Evaluate the negative SDF on lattice blocks and run marching cubes at isovalue 0.
11. Optionally evaluate RGB vertex colors.
12. Optionally keep largest connected components at block level.
13. Gather blocks from distributed workers.
14. On the master process, concatenate nonempty blocks, print counts, transform vertices back to world coordinates, drop degenerate faces, create the output parent directory, and export PLY.

## Config/checkpoint/output relationships

Use a checkpoint with the config that produced it. Important fields for extraction include:

- `trainer.type`: identifies the trainer module.
- `model.type`: identifies the Neuralangelo model module.
- `model.object.sdf.encoding`: hash-grid/coarse-to-fine settings used to interpret active levels at the checkpoint iteration.
- `model.object.sdf.gradient`: numerical-gradient settings that affect normal epsilon setup.
- `model.appear_embed.enabled`: determines whether texture extraction uses an appearance embedding path.
- `data.type`: dataset module used for inference construction.
- `data.root`: scene root containing `transforms.json` and images.
- `data.val.image_size`, `data.val.batch_size`, and `data.val.subset`: can affect inference data-loader construction even though mesh extraction primarily queries the SDF.

Output guidance:

- Put mesh outputs outside checkpoint directories unless the task specifically wants them there.
- Include resolution/block/texturing/LCC in filenames to preserve provenance, for example `mesh_outputs/scene_r2048_b128_textured.ply`.
- Keep low-resolution smoke outputs and final outputs separate.

## `transforms.json` fields used for mesh extraction

`transforms.json` normally comes from the repository data conversion helpers. Mesh extraction directly uses these fields:

| Field | Required for extraction | Role |
| --- | --- | --- |
| `sphere_center` | Yes | World-space center used to normalize scene coordinates and later restore mesh vertices to world coordinates. |
| `sphere_radius` | Yes | Positive scale used for normalized coordinates and final vertex scaling. |
| `aabb_range` | Optional | 3-by-2 world-space axis-aligned bounds. If present, converted into normalized bounds before sampling. |
| `frames` | Indirect | Used by dataset construction; not directly used for marching cubes but needed by the loaded data pipeline. |
| Camera intrinsics fields | Indirect | Used by dataset construction. |

Normalized bounds calculation when `aabb_range` exists:

```text
normalized_bounds = (aabb_range - sphere_center[:, None]) / sphere_radius
```

Fallback when `aabb_range` is absent:

```text
x, y, z bounds = [-1, 1]
```

Final vertex scaling:

```text
world_vertex = normalized_vertex * sphere_radius + sphere_center
```

The mesh utility also filters out vertices with normalized radius greater than or equal to 1.0 before final scaling.

## Lattice, block, and memory model

For normalized axis bounds `[min, max]` and interval `2 / resolution`, each axis uses a half-open grid similar to:

```text
min, min + interval, min + 2 * interval, ... < max
```

For each block, the code materializes up to `(block_res + 1)^3` xyz samples, sends them through the SDF on CUDA, copies SDF values back to CPU, and runs marching cubes. With `--textured`, extracted vertices also pass through SDF gradient and RGB networks.

Planning heuristics:

- Peak GPU memory scales strongly with `block_res^3` and model activation size.
- Total runtime scales with total lattice samples and texture work.
- Final PLY size scales with the extracted surface complexity and `resolution`, not with `block_res` alone.
- Multi-GPU extraction distributes lattice blocks and gathers Python mesh objects on the master process, so master CPU memory and output write time can still be bottlenecks.

## Output PLY semantics

Expected PLY signals:

- Header starts with `ply` and contains an `element vertex <N>` line.
- Useful geometry should have `N > 0` and `element face <M>` with `M > 0` for most surface reconstructions.
- Textured output should include color properties such as `red`, `green`, and `blue` on vertices.
- Coordinates are world-space after scaling by `sphere_radius` and translation by `sphere_center`.
- Degenerate faces are removed immediately before export.

Recommended filename pattern:

```text
mesh_outputs/<scene>_r<resolution>_b<block_res>[_textured][_lcc].ply
```

## Bundled planner contract

`scripts/plan_mesh_extraction.py` is a static helper. It accepts:

- `--config`
- `--checkpoint`
- `--output-file`
- `--resolution`
- `--block-res`
- `--gpus`
- `--single-gpu`
- `--textured`
- `--keep-lcc`
- `--print-command`
- `--print-json`

It reports path checks, parsed `data.root` when found, `transforms.json` fields, normalized bounds, approximate lattice dimensions, block counts, per-block sample count, and warnings for risky settings.

## Bundled validator contract

`scripts/validate_mesh_file.py` accepts a PLY path plus optional thresholds:

- `--min-vertices`
- `--min-faces`
- `--expect-textured`
- `--use-trimesh`
- `--print-json`

It always performs standard-library header checks. With `--use-trimesh`, it attempts a non-authoritative load check when `trimesh` is installed. Use this as a fast sanity check, not as proof of reconstruction quality.
