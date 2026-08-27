# Package and backend overview

Read this when choosing an AlpaSim workspace extra, interpreting an import
failure, or deciding whether a capability needs CPU, CUDA, containers, assets,
or credentials.

## Workspace packages

| Distribution | Import root / role | Public entry points or notes |
|---|---|---|
| `alpasim_wizard` | `alpasim_wizard` | `alpasim_wizard`, `alpasim_check_config`; Hydra orchestration |
| `alpasim-runtime` | `alpasim_runtime` | simulation event loop, workers, daemon, replay |
| `alpasim_grpc` | `alpasim_grpc` | v0 protobuf messages/stubs, `compile-protos`, `clean-protos` |
| `alpasim_utils` | `alpasim_utils` | logs, Pose/Trajectory/geometry, `print-asl`, `asl-to-frames` |
| `alpasim_eval` | `eval` | `alpasim-eval`, aggregation, re-evaluation |
| `alpasim_controller` | `alpasim_controller` | linear/nonlinear MPC entry points and vehicle model |
| `alpasim-physics` | `alpasim_physics` | `physics_server`, Warp-backed ground constraints |
| `alpasim-trafficsim` | `alpasim_trafficsim` | `catk_trafficsim_server`, CATK/PyG traffic |
| `alpasim_driver` | `alpasim_driver` | Python 3.12+, built-in policy adapters and `alpasim_driver_main` |
| `alpasim_plugins` | `alpasim_plugins` | `alpasim-info`, entry-point registries |

Install package groups through root extras rather than assuming bare `uv sync`
installs the simulator. The workspace uses a shared resolution; the repository
also documents a `setuptools<82` constraint for older `grpcio-tools` behavior.

## Backend decision table

- **CPU:** package import, config/schema checks, controller MPC, ASL loading,
  evaluation, many runtime replay/validation tests, and plugin metadata.
- **CUDA:** model inference, the documented NuRec/FlashDreams paths, Warp
  physics execution, CATK/PyG inference, and GPU service topology. Match the
  framework wheel and compiled extensions to the host driver and container.
- **Containers:** default renderer and managed services run in Docker/Compose
  or site-specific Slurm/enroot images. Host Python imports do not validate
  image mounts, inter-service networking, or service readiness.
- **Data/credentials:** public scene suites still use gated Hugging Face assets;
  model weights, USDZ artifacts, maps, and CATK token/checkpoint files are not
  bundled in this skill.
- **Python:** core packages declare `>=3.11,<3.13`; `alpasim_driver` declares
  `>=3.12,<3.13`. Keep separate compatible environments rather than forcing a
  cross-version install.

## Live inspection facts

The private inspection run imported the core package set, generated protobuf
modules, Rust geometry extension, Torch CUDA, and Warp. It detected eight
A100-SXM4-40GB devices. CATK service import/help was blocked by missing
compiled `torch_cluster`; this is an optional backend limitation, not a reason
to claim a CPU fallback. The supplemental Python 3.12 driver environment
imports `alpasim_driver` and lists built-in model entry points, but optional
`av`, `flash-attn`, and `hyperqueue` are not installed and the workspace's
`torchmetrics` override differs from upstream VaVAM's pin.

The installed console scripts `print-asl` and `asl-to-frames` currently target
`main` symbols that are not defined by their `__main__` modules. Use
`python -m alpasim_utils.print_asl`, `python -m alpasim_utils.asl_to_frames`,
or the bounded helpers bundled in the evaluation sub-skill until packaging is
corrected.
