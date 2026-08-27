# PhysicsNeMo diffusion API reference

| Object | Key fact |
| --- | --- |
| `physicsnemo.diffusion.DiffusionModel` | Base diffusion model surface used by the package docs. |
| `physicsnemo.diffusion.Predictor` | Predictor-side abstraction for inference/sampling pipelines. |
| `physicsnemo.diffusion.Denoiser` | Denoiser-side abstraction used by samplers and solvers. |
| `physicsnemo.diffusion.samplers.EulerSolver` | Basic solver around a denoiser. |
| `physicsnemo.diffusion.samplers.HeunSolver` | Heun solver variant around a denoiser. |
| `physicsnemo.diffusion.preconditioners.EDMPrecond` | EDM preconditioner constructor used by the API smoke. |
| `physicsnemo.diffusion.noise_schedulers.*` | Noise scheduler family; choose per workflow. |
| `physicsnemo.diffusion.guidance.*` | Guidance helpers, including DPS-style workflows. |
| `physicsnemo.diffusion.multi_diffusion.*` | Patch-based / multi-diffusion helpers and losses. |
| `physicsnemo.models.diffusion_unets.*` | SongUNet, DhariwalUNet, StormCastUNet and related diffusion U-Nets. |
| `physicsnemo.models.dit.DiT` | Diffusion transformer family. |
| `physicsnemo.models.topodiff.TopoDiff` | Conditional topology/design diffusion model. |

## Practical notes

- Keep the API smoke tiny and deterministic.
- Do not imply pretrained weights or domain datasets are bundled.
- Distinguish sampler/preconditioner selection from full training or generation examples.
