# PhysicsNeMo model family map

This table is intentionally compact. It summarizes the verified model families that matter most for common PhysicsNeMo user routes; use it as a shortlist, then confirm exact class availability in the installed package when the family is low-stability or optional-backend dependent.

| Data shape / task | Verified family | Import path | Why it fits |
| --- | --- | --- | --- |
| Regular Cartesian grid / operator learning | FNO | `physicsnemo.models.fno.FNO` | Classic Fourier Neural Operator for grid-to-grid surrogates and PDE operators. |
| Regular grid / image-like regression | AFNO, Pix2Pix, UNet, SRResNet, DiT | `physicsnemo.models.afno.AFNO`, `physicsnemo.models.pix2pix.Pix2Pix`, `physicsnemo.models.unet.UNet`, `physicsnemo.models.srrn.SRResNet`, `physicsnemo.models.dit.DiT` | Good for grid regression, translation, super-resolution, and transformer-style grid models. |
| Weather / climate / lat-lon / HEALPix | DLWP, DLWP-HEALPix, GraphCastNet, Pangu, Fengwu, SwinRNN, AFNO | `physicsnemo.models.dlwp.DLWP`, `physicsnemo.models.dlwp_healpix.HEALPixUNet`, `physicsnemo.models.graphcast.GraphCastNet`, `physicsnemo.models.pangu.Pangu`, `physicsnemo.models.fengwu.Fengwu`, `physicsnemo.models.swinvrnn.SwinRNN`, `physicsnemo.models.afno.AFNO` | Weather families cover autoregressive forecasting, multi-scale grids, and HEALPix/cubed-sphere-style layouts. |
| Unstructured mesh / graph / geometry | MeshGraphNet, BiStrideMeshGraphNet, HybridMeshGraphNet, GeoTransolver, Transolver, FIGConvUNet, DoMINO, VFGN | `physicsnemo.models.meshgraphnet.MeshGraphNet`, `physicsnemo.models.transolver.Transolver`, `physicsnemo.models.geotransolver.GeoTransolver`, `physicsnemo.models.figconvnet.FIGConvUNet`, `physicsnemo.models.domino.DoMINO`, `physicsnemo.models.vfgn.VFGNLearnedSimulator` | These target mesh/graph/geometry workflows and surface/volume surrogates. |
| Point cloud / geometry-conditioned operators | DoMINO, FIGConvUNet, GeoTransolver | `physicsnemo.models.domino.DoMINO`, `physicsnemo.models.figconvnet.FIGConvUNet`, `physicsnemo.models.geotransolver.GeoTransolver` | Useful for geometry-aware CFD and point-cloud-style physics problems. |
| Time series / recurrent forecasting | One2ManyRNN, Seq2SeqRNN, SwinRNN | `physicsnemo.models.rnn.One2ManyRNN`, `physicsnemo.models.rnn.Seq2SeqRNN`, `physicsnemo.models.swinvrnn.SwinRNN` | Fits autoregressive or sequence-to-sequence spatiotemporal workloads. |
| Generative / diffusion / inverse | SongUNet, DhariwalUNet, StormCastUNet, TopoDiff, DPOTNet | `physicsnemo.models.diffusion_unets.SongUNet`, `physicsnemo.models.diffusion_unets.DhariwalUNet`, `physicsnemo.models.diffusion_unets.StormCastUNet`, `physicsnemo.models.topodiff.TopoDiff`, `physicsnemo.models.dpot.DPOTNet` | Common starting points for diffusion and generative recipes. |
| Coordinate / tabular / lightweight baseline | FullyConnected | `physicsnemo.models.mlp.FullyConnected` | Good baseline or trunk network for coordinate MLP/DeepONet-like tasks. |
| Topology / sparse / specialized | FLARE, mesh_reduced | `physicsnemo.models.flare.FLARE`, `physicsnemo.models.mesh_reduced` | Use when an example or domain doc explicitly points here; these are more specialized than the mainstream families above. |

## Routing reminders

- `physicsnemo.models` root exports only `DiT`, `DoMINO`, and `FullyConnected`.
- Many families need optional extras or example-specific dependencies even though they import cleanly.
- If the exact class is low-stability or example-specific, tell the user to confirm it in the installed package before writing code.
