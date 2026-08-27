# Neuralangelo Cross-Cutting Troubleshooting

Use this reference for failures that are not clearly owned by a single phase. If a symptom maps cleanly to data preparation, training, or extraction, route to that sub-skill's troubleshooting file.

## Routing Table

| Symptom | First owner | Immediate action |
| --- | --- | --- |
| Cannot import `tinycudann`, CUDA unavailable, PyTorch CPU-only | Root environment | Run `scripts/check_neuralangelo_environment.py --require-cuda`; repair CUDA/PyTorch/tiny-cuda-nn. |
| `Config`, `Model`, `Dataset`, or `Trainer` cannot import | Root environment / training | Confirm target project root is on `sys.path`; check dependency versions. |
| Missing or malformed `transforms.json` | Data preparation | Use the data validator and regenerate/repair metadata. |
| Images named in metadata are absent | Data preparation | Fix image root/subdir or rerun conversion before training. |
| Training launches but data loader fails | Data preparation + training | Validate metadata, inspect config `data.root`, then inspect config summary. |
| CUDA OOM during training | Training | Reduce rays/samples/hash-grid/validation settings; see training troubleshooting. |
| CUDA OOM during extraction | Mesh extraction | Reduce `block_res` first, then resolution; see mesh troubleshooting. |
| Mesh is cropped, shifted, or scaled wrong | Data preparation + mesh | Reinspect `sphere_center`, `sphere_radius`, `aabb_range`, and readjust settings. |
| Mesh has floating components | Mesh extraction | Try `--keep_lcc`; if structure disappears, revisit training/data quality. |
| W&B fails or hangs | Training | Use debug/offline mode or disable online logging for smoke runs. |

## Environment Repair Checklist

1. Confirm the active Python environment:

   ```bash
   python -c "import sys; print(sys.executable); print(sys.version)"
   python -m pip check
   ```

2. Confirm CUDA PyTorch:

   ```bash
   python - <<'PY'
   import torch
   print(torch.__version__, torch.version.cuda)
   print(torch.cuda.is_available(), torch.cuda.device_count())
   if torch.cuda.is_available():
       print(torch.cuda.get_device_name(0))
   PY
   ```

3. Confirm tiny-cuda-nn:

   ```bash
   python - <<'PY'
   import tinycudann
   print('tinycudann ok')
   PY
   ```

4. Confirm Neuralangelo source imports through the root helper:

   ```bash
   python scripts/check_neuralangelo_environment.py --project-root <neuralangelo-root> --json
   ```

If PyTorch CUDA works but tiny-cuda-nn does not, prefer a compatible binary package for the selected Python/CUDA stack. Only attempt a source build when CUDA development headers, compiler, PyTorch ABI, and GPU architecture flags are under control.

## Project Root and Entry-Point Issues

- If the wrapper reports a missing project root, pass the target Neuralangelo source tree explicitly with `--project-root`.
- If the wrapper reports a missing entry point, the target source tree is incomplete or from an incompatible revision.
- If direct execution works but the wrapper does not, compare working directory, Python executable, and `PYTHONPATH`; the wrapper changes into the target project root and prepends it to `sys.path`.
- If `--help` imports heavy packages and fails, repair imports before launching an expensive run.

## Data/Bounds Symptoms

- **Training or extraction reports missing image files**: the `file_path` entries in `transforms.json` do not resolve from the data root. Use the data validator with the correct `--data-dir`.
- **All geometry appears far from origin or cropped**: check `sphere_center`, `sphere_radius`, `aabb_range`, and generated config readjust fields.
- **Indoor scene looks inverted or background dominates**: verify the selected `scene_type` and whether indoor-specific no-background settings are reflected in the config.
- **Object-centric capture has hollow/missing surfaces**: increase capture coverage/parallax before changing model internals.

## Training Symptoms

- **Strict override rejected**: inspect the YAML path before retrying. Typos in overrides should be fixed, not silently added.
- **Existing logdir warning**: use a new logdir for fresh runs or pass the correct resume/checkpoint options.
- **Validation OOMs while training step fits**: lower validation image count/cadence first; full validation can be more memory intensive.
- **Multi-GPU hang**: smoke with one visible GPU, then reintroduce DDP after imports and data loading are proven.

## Extraction Symptoms

- **Empty PLY**: check checkpoint/config pairing, bounds, and whether the trained iteration has usable geometry.
- **OOM despite low resolution**: reduce `block_res`; it controls per-block lattice memory.
- **Huge slow output**: reduce `resolution` or disable texturing until geometry is acceptable.
- **Thin parts disappear with LCC**: rerun without largest-component filtering and filter later with a geometry tool.

## Reporting Blockers

A useful blocker report should include:

- phase (`environment`, `data-preparation`, `training`, `mesh-extraction`);
- exact command or bundled helper used;
- Python/CUDA/PyTorch/tiny-cuda-nn versions if environment-related;
- data root, config, checkpoint, and output paths when relevant;
- first failing traceback/error line and whether it is deterministic;
- what was verified as working before the failure.
