---
name: capture
description: "Guides SplaTAM iPhone and NeRFCapture live capture, DDS streaming,
  capture-only dataset creation, online demo, and capture-to-offline
  reconstruction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Capture Sub-Skill

Use this sub-skill when a task involves SplaTAM's iPhone/NeRFCapture path: streaming frames from the NeRFCapture iOS app, saving an RGB-D dataset, running the online demo, or converting a captured dataset into an offline SplaTAM run.

Route pure offline SLAM, export, evaluation, and visualization of existing results to [../reconstruction/SKILL.md](../reconstruction/SKILL.md).

## Required preconditions

- A LiDAR/depth-capable Apple device running the NeRFCapture app.
- Device and workstation on the same network with DDS traffic allowed.
- Python dependency `cyclonedds` for capture; CUDA/rasterizer also required for live online SplaTAM.
- A CUDA-capable SplaTAM runtime for `scripts/iphone_demo.py` and offline reconstruction.
- Explicit user authorization before running bash wrappers that may call `sudo sysctl`.

Run the root environment check:

```bash
python scripts/check_env.py --require-cuda --require-rasterizer
```

For capture-only dataset validation after frames are saved:

```bash
python sub-skills/capture/scripts/validate_nerfcapture_dataset.py \
  --dataset-dir <captured-scene> --require-depth
```

## Workflow routing

| Task | Prefer | Read |
| --- | --- | --- |
| Save RGB-D frames from NeRFCapture without running SLAM | `python scripts/nerfcapture2dataset.py --config <capture-config.py>` | [references/workflows.md](references/workflows.md#capture-only-dataset-creation) |
| Capture dataset, then run offline SplaTAM | Python capture command, validate dataset, then `python scripts/splatam.py <splatam-config.py>` | [references/workflows.md](references/workflows.md#capture-to-offline-reconstruction) |
| Live online SplaTAM while receiving frames | `python scripts/iphone_demo.py --config <online-demo-config.py>` | [references/workflows.md](references/workflows.md#online-live-splatam-demo) |
| Use provided bash wrappers | Only with authorization for `sudo sysctl` buffer changes | [references/workflows.md](references/workflows.md#bash-wrapper-boundaries) |
| Explain or validate captured files | Bundled validator and data-format reference | [references/data-format.md](references/data-format.md) |

## Important safety boundaries

- Do not run `bash_scripts/online_demo.bash`, `bash_scripts/nerfcapture.bash`, or `bash_scripts/nerfcapture2dataset.bash` without permission. They may mutate kernel socket buffer settings with `sudo sysctl -w`.
- Do not silently overwrite captured datasets. Public configs use `overwrite` flags; source capture scripts can prompt or exit when the directory exists.
- Do not treat missing depth as usable for SplaTAM; the live code skips frames without depth and warns that the app should show depth support.
- Do not run network, app, or GUI-dependent steps as automated verification unless hardware and user authorization are available.

## Typical operating path

1. Edit a capture config under `configs/iphone/` or a copy of it.
2. Set `workdir`, `num_frames`, `depth_scale`, and `overwrite` deliberately.
3. Start the Python capture script or an authorized wrapper.
4. In the iOS app, send frames until the requested count is reached.
5. Validate the resulting dataset with the bundled validator.
6. Use the reconstruction sub-skill to run offline `scripts/splatam.py` or visualize/export results.

## Troubleshooting

Use [references/troubleshooting.md](references/troubleshooting.md) for DDS/network, missing-depth, overwrite, sysctl, and live-demo failures. Use the root troubleshooting file for CUDA/rasterizer or Open3D issues.
