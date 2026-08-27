# Refinement and Export Troubleshooting

## `--refine` appears to do nothing

The README says `--refine` starts refine-stage training. The inspected source only executes the refine block inside `if opt.final:`. Use `--final --refine` or deliberately patch the source control flow if the user wants a refine-only path.

## `contextual_loss` missing

The README notes contextual loss is used in refinement. Install `contextual_loss_pytorch` for refine runs and re-check imports.

## PyTorch3D import errors

Refinement imports PyTorch3D at module load time. Install a PyTorch3D build matching Python, torch, CUDA, and platform. If wheels are unavailable, use an environment/container known to support PyTorch3D.

## `xatlas` or `nvdiffrast` missing during `--save_mesh`

These are used inside the mesh export function. Install them only if the user needs mesh export; they are not required for command generation or input validation.

## OBJ exists but texture is blank or broken

Likely causes include failed UV unwrap, rasterization mismatch, empty density/alpha field, or bad checkpoint. Check mesh export logs, ensure the checkpoint renders plausible RGB images first, and verify `albedo.png`, `mesh.obj`, and `mesh.mtl` are all present.

## Test render OOM

Lower `--H`, `--W`, or `--max_ray_batch`; use a smaller checkpoint/render first; avoid simultaneous export and high-resolution test renders on a crowded GPU.
