# Backend and dependency compatibility

## Dependency classes

| Capability | Base requirements | Additional requirements | What a base import proves |
|---|---|---|---|
| Controller / linear MPC | Python 3.11–3.12, NumPy, SciPy, OSQP, gRPC/utils/plugins | none beyond the package environment | APIs and CPU QP path may be importable |
| Controller / nonlinear MPC | controller package | `do_mpc`, CasADi, IPOPT runtime behavior | model construction may be possible; not a successful solve |
| Ground physics | Python 3.11–3.12, NumPy/SciPy, gRPC/utils, `warp-lang` | compatible CUDA runtime; optional Polyscope for visualization | Warp symbols can import; not a mesh-kernel execution |
| Traffic service/session helpers | gRPC/runtime/utils, PyTorch, PyG, Hydra/OmegaConf, trajdata | compiled `torch_cluster`, `torch_scatter`, and `torch_sparse` variants as required by the installed PyTorch/CUDA | config, batching, and some fixtures may be usable |
| CATK inference | all traffic requirements | CUDA, matching compiled PyG extensions, USDZ scene data, CATK config/checkpoint/token data | nothing about inference unless the model actually loads and predicts |

Package metadata declares controller, physics, and traffic as Python 3.11–3.12
packages. Traffic's compiled PyG extensions need to match the installed PyTorch
and CUDA build; installing an arbitrary wheel can produce an import error or a
later kernel failure.

## Required distinctions

- `torch.cuda.is_available()` is only a device/runtime probe. It does not prove
  that the selected container, PyG extension, Warp kernel, CATK model, or scene
  assets are compatible.
- A successful `warp` import is not a ground-intersection smoke test. The
  backend allocates CUDA arrays and launches a ray-intersection kernel during
  `update_pose`.
- A controller CPU test does not validate physics or CATK. Keep per-component
  evidence separate.
- CATK's `torch_cluster` import is a hard prerequisite for the CATK servicer in
  this source version. Without it, importing the servicer/entry point is
  blocked, even though lighter traffic config and batching modules may import.
- A missing model checkpoint, token data, or USDZ is a data prerequisite, not an
  optional software warning for a requested inference run.
- Optional visualization packages affect only visualization; they are not a
  substitute for Warp or CATK dependencies.

## Safe diagnostic sequence

Use the bundled `scripts/check_backend.py` first. It reports module import
status, Torch/CUDA information, optional CATK-servicer import status, and any
explicit scene/model paths. It never invokes package installers, network
clients, schedulers, Docker, model loaders, or GPU inference.

Then run the smallest relevant check:

1. **Controller:** import `alpasim_controller`, construct `LinearMPC`, and run a
   tiny trajectory fixture. Add `NonlinearMPC` only when do_mpc/CasADi are
   available.
2. **Physics:** import `PhysicsBackend`, load a tiny PLY fixture, and run one
   `update_pose` only on a verified CUDA/Warp environment.
3. **Traffic helpers:** run service/batching tests with injected fake scene and
   predictor objects; these test lifecycle and contracts without CATK weights.
4. **CATK:** run the marked integration test only when all required CUDA, PyG,
   USDZ, and model assets are explicitly present.

## Failure interpretation

- `ModuleNotFoundError: torch_cluster` while importing the CATK servicer means
  install the matching compiled PyG extension in the runtime/container, then
  repeat the import. Do not catch it and advertise a CPU CATK mode.
- A CUDA library or device mismatch means align the PyTorch, CUDA, Warp, and PyG
  variants or use the supported container. Do not downgrade the claim to
  “verified” from a Python import.
- `No usable map geometry was found within ... m` means the CATK map filter
  produced no usable geometry. Check the scene adapter, map element names,
  filter distance, and scene content.
- Weight/config failures mean the model files are missing, unreadable, or
  inconsistent. Check paths and permissions supplied by the deployment owner;
  never bundle credentials or weights in this skill.

The skill's verified construction evidence includes successful lightweight
controller/physics/config imports and a CUDA-capable Torch/Warp probe, while the
CATK servicer import remains explicitly blocked when `torch_cluster` is absent.
This is a limitation record, not a claim of full GPU coverage.
