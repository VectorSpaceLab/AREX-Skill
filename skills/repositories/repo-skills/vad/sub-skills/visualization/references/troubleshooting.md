# Visualization troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Inspector reports malformed or unreadable artifact | Wrong file, truncated output, or untrusted/incompatible pickle/JSON | Regenerate with evaluation `--out`; inspect only trusted pickle files; verify top-level `results`, `map_results`, and `plan_results`. |
| Renderer says sample token is absent | Result came from a different split/version or data root | Use the exact nuScenes version and root used for evaluation; compare a token from the result with dataset records before rendering all samples. |
| Object boxes render but map/planning overlays are empty | `map_results`/`plan_results` absent, empty, or keyed differently | Inspect the corresponding sample entry and preserve the VAD result formatter's structure; do not feed a generic detection-only result to the VAD renderer. |
| Boxes/trajectories are shifted or rotated | Wrong calibration/ego pose, coordinate-frame assumption, or mismatched dataset version | Verify sample data tokens, sensor calibration, ego pose, and global-to-ego transforms. Re-render a single known sample before a video batch. |
| Released checkpoint output looks visually wrong | New image normalization was used with legacy released weights | Re-evaluate with the documented legacy normalization and matching config; do not repair images after rendering. |
| Import fails before visualization starts with a native extension error | Legacy plugin/MMDetection3D operators are unavailable | Repair the compatible CUDA/native environment; the renderer's external data requirements are separate from the import gate. |
| Output directory is empty or video cannot be encoded | No samples passed, output is unwritable, or codec/display backend is unavailable | Run the artifact/token preflight, use a writable directory, render one sample, and check the host's image/video backend. |
| `--help` fails with module imports | The source visualization script imports plugin and dataset modules before argparse | Treat it as an environment check failure; use this skill's structural inspector for safe checks and install the matching runtime before rendering. |
