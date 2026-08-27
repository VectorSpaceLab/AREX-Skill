# Built-in method overview

Nerfstudio exposes built-in methods through the `method_configs` catalog. Run `ns-train --help` in the target environment for the authoritative list, including external install hooks.

## Common choices

| Method | Use when | Notes |
| --- | --- | --- |
| `nerfacto` | Default real-world captures and general NeRF training. | Recommended first choice; CUDA expected for practical speed. |
| `nerfacto-big`, `nerfacto-huge` | Higher quality with larger memory/time budget. | Increase rays/model size carefully. |
| `splatfacto`, `splatfacto-big`, `splatfacto-mcmc` | 3D Gaussian Splatting workflows. | Requires `gsplat` and CUDA for real use. |
| `instant-ngp`, `instant-ngp-bounded` | Fast Instant-NGP-style fields. | Uses `nerfacc` and GPU paths; CPU is not a full substitute. |
| `vanilla-nerf` | Original NeRF baseline or tiny CPU smoke. | Slow but useful for minimal/reduced checks. |
| `mipnerf`, `tensorf`, `dnerf`, `phototourism` | Research/baseline methods with data-specific expectations. | Read method help and dataparser requirements. |
| `depth-nerfacto` | RGB-D/depth-supervised data. | Dataset frames need depth paths and appropriate scaling. |
| `neus`, `neus-facto` | Surface/SDF-style reconstruction. | Prefer when the desired output is a surface reconstruction workflow. |
| `semantic-nerfw` | Semantic/transient-object workflows. | Data and labels must match method expectations. |
| `generfacto` | Text-to-NeRF/generative route. | Optional heavy dependencies; not part of a minimal install. |

## Backend reality

- CUDA is the practical backend for most real methods.
- CPU can verify config assembly, dataparser IO, and tiny reduced loops when the model implementation is set to torch and iterations/rays are tiny.
- tiny-cuda-nn accelerates hash encodings/MLPs; when absent, some configs can use a slower torch implementation.
- `gsplat` and `nerfacc` must match the installed torch/CUDA stack for Splatfacto/Instant-NGP paths.

## Method help

Use nested help before changing advanced config fields:

```bash
ns-train --help
ns-train nerfacto --help
ns-train splatfacto --help
```
