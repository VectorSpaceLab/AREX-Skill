---
name: neural-rendering-3d
description: "Routes Papers-in-100-Lines NeRF, implicit representation, 3D
  Gaussian splatting, camera, ray, and neural rendering tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Neural Rendering and 3D

Use this sub-skill for NeRF-family renderers, Fourier features, SIREN/MFN,
PlenOctrees, Plenoxels, K-Planes, Light Field Networks, 3D Gaussian Splatting,
Speedy-Splat, Spherical Voronoi, Splatter Image, and single-view 3D
reconstruction entries in Papers-in-100-Lines.

## Read these bundled files

- [Rendering guide](references/rendering-guide.md) maps the rendering families,
  key functions, camera/data assumptions, adaptation knobs, and validation
  signals.
- [Troubleshooting](references/troubleshooting.md) covers missing ray datasets,
  trained Gaussian tensors, camera metadata, CUDA hardcodes, projection errors,
  memory pressure, and output frame directories.
- [Implementation index](../../references/implementation-index.md) lists all
  neural-rendering entries and their evidence labels.
- [Dependency and backend guide](../../references/dependency-and-backend-guide.md)
  explains per-entry torch/CUDA version conflicts.
- [estimate_render_memory.py](scripts/estimate_render_memory.py) estimates
  rough NeRF and splatting tensor memory before a run.

## Trigger routes

- **NeRF or volume rendering**: ray origins/directions, positional encoding,
  density/color networks, accumulated transmittance, `render_rays`, novel view
  output, few-shot/regularized variants.
- **Implicit image or coordinate networks**: Fourier feature inverse rendering,
  SIREN, multiplicative filter networks, Deep Image Prior-like reconstruction
  when it is framed as a coordinate/image representation.
- **3D Gaussian or splatting**: spherical harmonics, covariance construction,
  projection, tiling, alpha compositing, trained Gaussian assets, camera
  trajectories.
- **Single-view 3D reconstruction**: Splatter Image and pixel-to-gaussian
  workflows, UNet encoders, camera intrinsics, source/target image pairs.
- **Memory or backend triage**: estimate rays/bins/gaussians before launching a
  full CUDA rendering script.

## Safe workflow

1. Query the catalog if the paper is not explicit:

   ```bash
   python ../../scripts/query_implementation_index.py --group neural-rendering-3d --query "gaussian splatting"
   ```

2. Read [Rendering guide](references/rendering-guide.md) for the selected
   family and identify the minimal inputs: rays and pixels, camera matrices,
   trained fields/gaussians, image pairs, or synthetic coordinates.
3. Estimate size before execution:

   ```bash
   python scripts/estimate_render_memory.py --mode nerf --height 400 --width 400 --nb-bins 192
   python scripts/estimate_render_memory.py --mode 3dgs --height 800 --width 800 --gaussians 100000
   ```

4. For quick debugging, shrink image size, ray count, bins, gaussian count, and
   chunk size. Replace hard-coded CUDA only when the requested result is a CPU
   shape check, not a real rendering benchmark.
5. Treat missing data/weights/camera files as stop conditions requiring user
   input or approved download, not as reasons to fabricate results.

## Boundaries

Route GANs, VAEs, flows, diffusion, DreamBooth, and Stable Diffusion to
[generative-models](../generative-models/SKILL.md). Route optimizers,
activations, meta-learning, hypergradients, Deep Image Prior as optimization,
and Atari RL to [optimization-meta-rl](../optimization-meta-rl/SKILL.md). Use
[paper-catalog-and-execution](../paper-catalog-and-execution/SKILL.md) for
initial lookup and dependency planning.
