# Neural Rendering Guide

This reference distills the rendering-oriented Papers-in-100-Lines entries into
families, inputs, adaptation knobs, and validation signals. The catalog entry
names are provenance labels; do not treat them as bundled runnable code.

## Family map

| Family | Entries | Core pattern | Inputs/assets | First validation |
|---|---|---|---|---|
| Classic NeRF | NeRF, Fourier features, FastNeRF, FreeNeRF, InfoNeRF, NeRF--, KiloNeRF, PlenOctrees | positional encoding, MLP density/color, `compute_accumulated_transmittance`, `render_rays`, train/test loops | ray origin/direction/pixel arrays, camera bounds, novel-view output directory | tiny ray batch through `render_rays` with small `nb_bins` |
| Explicit/accelerated fields | Plenoxels, K-Planes, Instant NGP | grid/plane/hash encodings, spherical functions, ray marching | scene bounds, images/rays, voxel/grid parameters | check coordinate normalization and output color shape |
| Implicit coordinate/image networks | SIREN, multiplicative filter networks, Fourier feature inverse rendering | coordinate MLPs with sinusoidal or Gabor filters | image coordinates and target pixels | tiny coordinate batch with finite output |
| 3D Gaussian/splatting | 3D Gaussian Splatting, Speedy-Splat, Spherical Voronoi | spherical harmonics or directional appearance, covariance from scale/quaternion, projection, tiling, alpha compositing | trained Gaussian tensors, camera metadata, camera trajectories | small synthetic Gaussian projection before full frame render |
| Single-view 3D reconstruction | Splatter Image, A Pixel Is Worth More Than One 3D Gaussian | UNet/image encoder predicts parent/child gaussians, differentiable splatting | input images, intrinsics, source/target pairs | verify image tensor, intrinsics, and gaussian parameter shapes |
| Light Field Networks | Light Field Networks | Plücker rays, hypernetwork/latent inversion, single-evaluation rendering | camera intrinsics/extrinsics and rays | check plucker ray shape and latent dimension |

## Common objects and functions

- NeRF-like scripts expose a model class such as `NerfModel`, `FastNerf`,
  `KiloNerf`, or `NGP`, plus `render_rays`, `compute_accumulated_transmittance`,
  `train`, and `test` helpers.
- 3DGS-like scripts expose `evaluate_sh` or `evaluate_sv`, `project_points`,
  `build_sigma_from_params`, quaternion-to-rotation helpers, and a `render`
  function.
- Splatter/Image-style entries add camera intrinsics helpers, source/target
  sampling, a UNet-style image encoder, and gaussian decode functions.
- Most full scripts write images or frames and assume output directories exist.

## Safe adaptation knobs

- **Rays/chunks**: reduce ray count or chunk size first; full `H*W*nb_bins`
  tensors grow quickly.
- **Bins/samples**: lower `nb_bins` for debugging; do not compare quality or
  convergence to paper results from reduced bins.
- **Image size**: halve `H`/`W` when debugging memory or output formats.
- **Gaussians**: use a few synthetic gaussians to validate projection and alpha
  compositing before loading trained tensors.
- **Device**: make `device` an explicit argument. CPU can validate shapes and
  math for small inputs, but not full CUDA performance.
- **Data paths**: replace hard-coded data filenames with explicit arguments in
  adaptations. Keep external data/weights out of generated skill directories.

## Memory planning

For NeRF-like rendering, a rough lower-bound tensor scale is
`rays * nb_bins * channels`. A 400x400 image with 192 bins already creates tens
or hundreds of MiB of intermediate tensors before model activations. Use the
bundled estimator before a run:

```bash
python scripts/estimate_render_memory.py --mode nerf --height 400 --width 400 --nb-bins 192
```

For splatting, gaussian projection, tile expansion, sorting, covariance, and
final image buffers all contribute. The estimator gives a lower bound only:

```bash
python scripts/estimate_render_memory.py --mode 3dgs --height 800 --width 800 --gaussians 100000
```

## Validation signals

- Ray origins/directions have matching batch size and final dimension 3.
- Camera matrices are 4x4 or explicitly documented as intrinsics/extrinsics.
- Rendered color tensors are finite and in a plausible range before image save.
- Gaussian covariance matrices are positive and finite after scale/quaternion
  conversion.
- Projection leaves at least one primitive on screen; an all-off-screen result
  is usually a camera/bounds problem, not an empty scene.
- Output directories are created in a scratch workspace before saving frames.
