# Refinement, Rendering, and Export Workflow

## Refine Stage

README command:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --phi_range 135 225 --refine --text "object prompt"
```

Source quirk: in the inspected `main.py`, refinement is executed inside the `if opt.final:` block after the training/test path. If `--refine` alone does not run refinement, use:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --phi_range 135 225 --final --refine --refine_iters 3000 --text "object prompt"
```

The refine path creates a multi-view loader (`type='gen_mv'`), saves generated multi-view images under `results/NAME/mvimg`, creates a test loader, and calls `trainer.refine(...)`.

## Test Rendering

For a trained workspace:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --test --text "object prompt"
```

The test path builds a `NeRFDataset` with `type='test'`, `H=opt.H`, `W=opt.W`, and writes a video through `trainer.test(..., write_video=True)`.

## Mesh Export

For mesh export from a checkpoint:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --test --save_mesh --text "object prompt"
```

Mesh export reaches `Trainer.save_mesh(...)` and `NeRFRenderer.export_mesh(...)`. That path uses marching cubes and, for textured mesh output, imports `xatlas`, `nvdiffrast.torch`, and scikit-learn nearest neighbors.

## Refinement Dependencies

`nerf/refine_utils.py` imports PyTorch3D structures, point rasterization, and compositing. `nerf/renderer.py` imports Open3D for point cloud output. `nerf/utils.py` imports contextual loss. These may fail before the specific refine function starts because imports happen at module load time.

## Output Review

After a refine/export run, check:

- `results/NAME/checkpoints/` for checkpoint files.
- `results/NAME/mvimg/` for multi-view images generated before refinement.
- test render videos/images under the workspace output folders.
- OBJ/MTL/albedo texture files when mesh export succeeds.
- `log_df.txt` and terminal output for export-specific failures.
