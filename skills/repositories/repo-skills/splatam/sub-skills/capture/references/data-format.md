# NeRFCapture Data Format

## Purpose

Use this to validate or explain datasets produced by SplaTAM's `nerfcapture2dataset.py` and `iphone_demo.py` scripts.

## Directory layout

A completed capture dataset should look like:

```text
<scene>/
  rgb/
    0.png
    1.png
    ...
  depth/
    0.png
    1.png
    ...
  transforms.json
```

Depth may be absent for frames when the app does not send depth, but SplaTAM's RGB-D workflows require usable depth. Treat missing depth as a capture failure for reconstruction unless the user explicitly wants RGB-only archival.

## `transforms.json` global fields

The capture scripts initialize:

| Field | Meaning |
| --- | --- |
| `fl_x`, `fl_y` | Focal lengths from the device stream. |
| `cx`, `cy` | Principal point. |
| `w`, `h` | RGB frame width and height. |
| `integer_depth_scale` | `depth_scale / 65535.0`, used to interpret saved 16-bit depth PNGs. |
| `frames` | Ordered frame metadata list. |

## Per-frame fields

Each frame entry contains:

| Field | Meaning |
| --- | --- |
| `transform_matrix` | 4x4 ARKit camera transform as a nested list. |
| `file_path` | Relative RGB image path such as `rgb/0.png`. |
| `depth_path` | Relative depth image path such as `depth/0.png` when depth is available. |
| `fl_x`, `fl_y`, `cx`, `cy`, `w`, `h` | Per-frame camera intrinsics and dimensions. |

## Validation

Run:

```bash
python sub-skills/capture/scripts/validate_nerfcapture_dataset.py \
  --dataset-dir <scene> --require-depth
```

The helper checks manifest presence, frame list, RGB/depth files, transform shape, and basic camera fields. It does not verify visual quality, scale accuracy, or pose correctness.

## Using captured data in SplaTAM

For offline SplaTAM configs, use:

- `data.dataset_name="nerfcapture"`.
- `data.basedir` as the parent directory containing the scene folder.
- `data.sequence` as the scene folder name.
- `data.start`, `data.end`, `data.stride`, and `data.num_frames` matching the captured frames.
- `data.desired_image_height`/`width` and densification sizes based on the original capture resolution and downscale factors.

The iPhone public configs default to `./experiments/iPhone_Captures/<scene>` with `full_res_width=1920` and `full_res_height=1440`, then derive tracking and densification sizes from `downscale_factor` and `densify_downscale_factor`.

## Common data-format pitfalls

- Existing output directory plus `overwrite=False`: capture exits instead of replacing data.
- Existing output directory plus `overwrite=True`: script prompts before deleting; do not automate destructive confirmation without user approval.
- Missing `depth_path`: SplaTAM will not have RGB-D input for that frame.
- Non-sequential frame names: the manifest is authoritative, but public configs and debugging assumptions often expect numeric order.
- Wrong `depth_scale`: saved 16-bit depths will be metrically wrong, causing tracking and scale failures.
