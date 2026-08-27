# Cross-cutting troubleshooting

Use this reference after the focused sub-skill's first checks. Preserve the
first causal error and do not retry a credentialed, GPU, or scheduler failure
as if it were a Python import problem.

| Symptom | Likely cause | Next action |
|---|---|---|
| Bare `uv sync` appears empty | Root workspace has intentionally empty dependencies | Select `--extra wizard`, `--extra all`, or the smallest package extra for the task |
| `uv` rejects `exclude-newer = "3 days"` | uv is older than the documented minimum | Upgrade uv; do not remove the supply-chain safeguard |
| `ModuleNotFoundError` for `*_pb2` | Generated gRPC stubs are absent or a mounted checkout shadows image stubs | Run the gRPC compile workflow, check package build artifacts, then re-run an isolated import |
| `GatedRepoError`, HTTP 401/403, or model download timeout | HF access/token/license or network/cache issue | Request dataset/model access, set the user's token outside logs, verify cache/revision, and avoid embedding credentials |
| `CUDA_ERROR_UNSUPPORTED_PTX_VERSION` | Host NVIDIA driver is below the container's CUDA requirement | Check `nvidia-smi`; use a compatible driver/container pair rather than changing application code |
| `UNAVAILABLE`, version probe timeout, or empty endpoint list | Service did not start, port is not ready, or generated network config is wrong | Inspect startup order/logs, generated network config, Docker network/ports, and service readiness |
| No `rollouts` or no `_complete` marker | Runtime/config/service failure or interrupted rollout | Preserve `wizard.log_dir`, inspect the first service error and resolved YAML; do not treat partial ASL as success |
| Zero-decision-delay assertion names a camera/pose | Camera interval, control timestep, and pose cadence are not aligned | Use integer microsecond multiples and enable the validation flag while debugging |
| Video-model frames drift or chunk validation fails | Seed frame/calibration/map mismatch or incorrect chunk timing | Use a documented single-view preset, preserve calibration, and satisfy chunk/force-GT equations |
| `catk_trafficsim_server` fails on `torch_cluster` | Matching PyG compiled extension is absent | Install the documented CUDA/PyG wheel variant or keep CATK unverified; do not fabricate a static fallback |
| `physics_server` imports but backend fails | Warp/CUDA/device/mesh requirements are not all satisfied | Run the backend probe, check mesh glob and device visibility, then distinguish CPU utility tests from ground execution |
| `print-asl` or `asl-to-frames` entry point imports missing `main` | Current package script target does not match the module implementation | Use `python -m alpasim_utils.print_asl` / `python -m alpasim_utils.asl_to_frames` or the bundled evaluation helpers |
| Driver import works but inference fails | Missing `av`, `flash-attn`, weights, HF access, or incompatible CUDA/torch variant | Read the driver troubleshooting route; identify the exact model preset and optional dependency before installing anything broad |
| Plugin model is listed but Hydra config is missing | Only `alpasim.models` or only `alpasim.configs` was registered, or package is not installed | Inspect entry-point groups with the driver helper, register both contracts when needed, and reinstall the plugin |
| Slurm/enroot command works locally but job fails | No active allocation, site image/cache/permissions, or inherited environment mismatch | Use the approved site wrapper and allocation; keep scheduler submission manual |
| Results metrics look implausible | Missing USDZ/map, wrong suite/revision, malformed ASL, or evaluator fallback | Validate scene/cache and log metadata; inspect per-rollout data before aggregation |

Stop and ask for an informed decision when a required backend, host runtime,
credential, or user-owned environment mutation is unresolved. A CPU import is
not a substitute for required renderer/model/CATK/Warp execution.
