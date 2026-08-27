# Capture Troubleshooting

## Purpose

Use this for NeRFCapture/DDS, live iPhone demo, dataset overwrite, depth, and socket-buffer issues.

## Script waits forever at `Waiting for frames...`

Likely causes:

- Device and workstation are not on the same network.
- Firewall blocks CycloneDDS discovery or data traffic.
- NeRFCapture app is not sending frames.
- DDS topic mismatch or CycloneDDS environment issue.
- Kernel receive/send buffers are too small for the stream.

Recovery:

1. Confirm the app is open, capture started, and frames are being sent.
2. Confirm both devices are on the same WiFi/LAN.
3. Check firewall/VPN restrictions.
4. If user permits system mutation, use an authorized wrapper or manually raise `net.core.rmem_max` and `net.core.wmem_max` to `2147483647`.
5. Verify `cyclonedds` imports in the SplaTAM environment.

## Frames arrive but depth is missing

Symptom:

- Script prints that no depth image was received and asks to ensure the app says depth is supported.

Recovery:

- Use a LiDAR/depth-capable device and mode.
- Confirm NeRFCapture UI shows depth support.
- Do not run SplaTAM reconstruction on RGB-only captures unless the code has been explicitly modified; selected workflows require depth.

## Existing output directory blocks capture

Capture configs have `overwrite` flags.

- With `overwrite=False`, the script exits when the target exists.
- With `overwrite=True`, the script prompts before deleting/replacing the folder.

Never auto-confirm deletion of a user dataset without explicit approval. Prefer changing `scene_name` or `workdir` for a new capture.

## Live demo runs out of memory or lags

The online demo performs capture and SplaTAM tracking/mapping in one process.

Mitigations:

- Reduce `num_frames` for testing.
- Increase downscale factors to reduce `desired_image_*` and `densification_image_*` sizes.
- Reduce `tracking_iters`, `mapping_iters`, and `mapping_window_size`.
- Disable W&B.
- First prove capture-only works, then try offline reconstruction, then live online reconstruction.

## Viewer fails after capture/demo

The wrappers launch `viz_scripts/final_recon.py` after capture/reconstruction. If visualization fails:

- Confirm `params.npz` exists with the reconstruction result checker.
- Confirm a GUI/display is available.
- Use `viz.render_mode='centers'` to debug geometry without color/depth rendering.
- Treat headless Open3D failures as visualization blocks, not capture failures.

## Dataset validates but offline SLAM fails

Check:

- Offline config `data.basedir` is the parent directory, not the scene directory itself.
- `data.sequence` is exactly the captured scene directory name.
- `num_frames` does not exceed the manifest length.
- `depth_scale` and `integer_depth_scale` are reasonable.
- CUDA/rasterizer environment passes root `check_env.py`.

## DDS/system changes are not authorized

If the user does not authorize `sudo sysctl` changes:

- Do not run bash wrappers.
- Run Python capture scripts directly.
- Document that small socket buffers may cause dropped or missing frames.
- Ask for authorization only if direct Python capture demonstrably fails due buffer limits.
