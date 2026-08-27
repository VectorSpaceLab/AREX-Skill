# Simulation Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: metasim` or `roboverse_pack` | Base package or MetaSim was not installed, or package discovery is not enabled | Install `roboverse-py` with the selected simulator extra in the same environment; run the minimal imports before task code. |
| A simulator backend imports but reset fails | The backend extra, native driver, asset format, or display/runtime is incomplete | Record the exact backend; test a headless minimal scene; install only the documented MetaSim extra and consult its backend prerequisites. Do not call this cross-backend support. |
| `FileNotFoundError` for a model/asset | Asset data is not in the package or was not intentionally downloaded | Verify the asset path and license/data source; use a packaged primitive fixture first. Never silently substitute a different robot or object. |
| Joint/site/body lookup fails | Config name does not match the selected model or task variant | Inspect the robot's declared names and update the config/profile; do not use positional indices without verifying their ordering. |
| Camera/render crashes or hangs | Display, renderer, EGL/GL context, or backend-specific renderer missing | Run headless reset/step first; set a supported renderer and validate one frame; classify display/GPU issues separately from Python test failures. |
| Lidar/query import fails | Optional sensor, Warp, trimesh, or backend query support is missing | Install the documented sensor extra or route to a supported query; fail clearly rather than emitting an empty observation. |
| Teleoperation is unstable or wrong-joint | Wrong robot profile, control slices, transform convention, or device timing | Validate recorded poses and joint count first; inspect profile/slices; then add device input. Keep real-robot/deployment actions out of a default smoke test. |
| Multi-environment behavior differs from one environment | Vectorized state shape or reset semantics were assumed | Assert batch dimensions after reset and step; reduce to one environment, then increase batch size while checking shapes and seeds. |
