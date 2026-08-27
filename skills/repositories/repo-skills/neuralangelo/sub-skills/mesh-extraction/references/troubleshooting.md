# Mesh Extraction Troubleshooting

Use this reference after static preflight fails, extraction crashes, or the resulting PLY is unusable.

## Fast triage

1. Does the config belong to the checkpoint?
2. Does the config's `data.root` contain the intended `transforms.json`?
3. Does `transforms.json` contain a positive `sphere_radius` and plausible `sphere_center`?
4. Does `aabb_range` include the expected subject, and is it not much larger than necessary?
5. Does the output path include a parent directory?
6. Are `resolution` and `block_res` appropriate for available GPU memory?
7. Was `--textured` or `--keep_lcc` enabled before an untextured/no-LCC baseline succeeded?
8. Did the console report nonzero vertices and faces?

## Symptoms, causes, recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `transforms.json` not found | `data.root` in config points at the wrong scene root, or data preparation did not finish. | Fix `data.root` or reroute to `data-preparation` to create/repair transforms metadata. |
| Checkpoint load errors or missing model keys | Checkpoint/config mismatch, wrong model settings, or incomplete checkpoint. | Use the config saved with the checkpoint. If the checkpoint is missing or incompatible, reroute to `training-and-configs`. |
| Output path error before export | `--output_file` has no directory component, so parent-directory creation receives an empty string. | Use `mesh_outputs/<name>.ply` or another path with a parent directory. |
| CUDA out of memory early in block evaluation | `block_res` too high, textured pass too expensive, or model hash-grid settings require high VRAM. | Lower `block_res` first. Disable `--textured`. Try a low-resolution smoke run. If still failing, reduce `resolution` or use a larger GPU. |
| CUDA out of memory near finalization | Output mesh or gathered block meshes are too large for master CPU/GPU workflow. | Lower `resolution`, narrow overly large bounds, avoid texturing, or split scene/workflow if appropriate. |
| Empty PLY or zero vertices/faces | Wrong checkpoint, untrained model, wrong config, iso-surface outside sampled bounds, too-low resolution, or invalid normalization. | Confirm checkpoint/config pair, run low-resolution smoke then moderate resolution, inspect `sphere_center`/`sphere_radius`/`aabb_range`, and verify training produced a meaningful SDF. |
| Mesh is cropped | `aabb_range` or bounding sphere is too small; unit-sphere filtering removed valid geometry. | Reroute to `data-preparation` to adjust bounds/sphere, then retrain or re-extract according to how the bounds were changed. Compare with fallback/wider bounds only as a diagnostic. |
| Mesh is shifted or scaled incorrectly | `sphere_center`/`sphere_radius` mismatch between data conversion, training, and extraction; non-default `data.readjust` needs audit. | Confirm the exact metadata used during training. Inspect a smoke mesh against cameras/known scale. Treat non-default readjust settings as a coordinate-risk item. |
| Mesh has many floating fragments | Bounds too broad, noisy SDF, low-quality training, or insufficient observations. | Try `--keep_lcc` for compact objects, compare against no-LCC, improve training/data if artifacts are part of the learned field. |
| Thin structures disappear | `--keep_lcc` removed valid small/disconnected pieces, resolution too low, or bounds/sphere crop the structure. | Disable `--keep_lcc`, increase `resolution`, and verify bounds. Post-process externally if a true global component filter is needed. |
| Textured mesh has poor or uniform colors | Geometry pass is not good, appearance embeddings default to a zero appearance vector, or texture extraction is under-resolved. | Validate untextured geometry first. If appearance embeddings were enabled, interpret colors as a neutral/default appearance. Consider task-specific rendering/visualization instead of relying on vertex colors. |
| Multi-GPU run hangs or rank errors | Distributed launch/environment issue, wrong `--single_gpu` usage, or NCCL problem. | For one GPU, use plain `python ... --single_gpu` or `torchrun --nproc_per_node=1` without `--single_gpu`. For multiple GPUs, use `torchrun --nproc_per_node=N` and let it set ranks. |
| PLY validator says header is not textured | `--textured` was not passed, exporter did not attach vertex colors, or the PLY uses unexpected color property names. | Re-run with `--textured`; check console `colors:` count; inspect header. |
| PLY is enormous | `resolution` too high or bounds too broad. | Lower `resolution`, fix bounds, or export a lower-resolution diagnostic mesh for downstream tasks. |

## Recovery order for failed runs

1. Run the planner with the exact config/checkpoint/output/resolution/block settings.
2. If planner reports missing files or invalid transforms metadata, fix those before GPU work.
3. Run an untextured smoke extraction at `resolution=512`, `block_res=64`.
4. Validate the smoke PLY header and nonzero counts.
5. Increase `resolution` while keeping `block_res` conservative.
6. Increase `block_res` only when memory headroom is clear and runtime matters.
7. Add `--textured` after geometry is acceptable.
8. Compare `--keep_lcc` and no-LCC outputs before discarding geometry.

## When to reroute

- Reroute to `data-preparation` when the root issue is image/COLMAP conversion, bad/missing `transforms.json`, bounding sphere authoring, or camera pose reliability.
- Reroute to `training-and-configs` when the root issue is no checkpoint, wrong checkpoint, incompatible config, undertrained SDF, appearance embedding setup, or training hyperparameters.
- Stay in `mesh-extraction` when the root issue is resolution, `block_res`, texturing, LCC filtering, output PLY validation, or extraction command construction.

## Safe diagnostic commands

Planner:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/plan_mesh_extraction.py \
  --config logs/<group>/<name>/config.yaml \
  --checkpoint logs/<group>/<name>/<checkpoint>.pt \
  --output-file mesh_outputs/<scene>_debug.ply \
  --resolution 512 \
  --block-res 64 \
  --print-command
```

PLY header validation:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/validate_mesh_file.py \
  mesh_outputs/<scene>_debug.ply \
  --min-vertices 1 \
  --min-faces 1
```

Textured PLY validation:

```bash
python skills/disco/neuralangelo/sub-skills/mesh-extraction/scripts/validate_mesh_file.py \
  mesh_outputs/<scene>_textured.ply \
  --expect-textured
```

## Known limitations and gaps

- The bundled planner parses common YAML patterns for `data.root` with standard-library text scanning; it is not a full YAML interpreter.
- Header validation proves that a PLY is structurally plausible, not that it is a high-quality reconstruction.
- Full extraction remains a CUDA/checkpoint-dependent operation; the safe checks here do not prove that a particular GPU has enough memory for a chosen high-resolution run.
- `--keep_lcc` is block-local in the implementation. If a downstream task requires a true global largest connected component, perform a separate mesh post-processing step after export.
