# Image Preparation Troubleshooting

## Missing RGBA image

**Symptoms**
- `Could not find image ...` from the single-image datamodule.
- `cv2.imread(..., IMREAD_UNCHANGED)` returns an invalid image or later channel conversion fails.

**Likely causes**
- `data.image_path` points to the original RGB file instead of the generated `_rgba.png` file.
- The command is being run from the wrong checkout root.
- The filename contains shell-sensitive spaces and was not quoted.

**Recovery**
1. Quote the image path in shell commands and OmegaConf overrides.
2. Check that the path is repo-relative from the DreamCraft3D checkout root.
3. Run the bundled validator against the intended `_rgba.png` path.

## Missing depth or normal sidecars

**Symptoms**
- The datamodule asserts while trying to load `<stem>_depth.png` or `<stem>_normal.png`.
- Coarse/geometry stages start parsing config but fail before training.

**Likely causes**
- Only the RGBA image was copied.
- Preprocessing was interrupted after background removal.
- The sidecar stem differs from the RGBA image stem.

**Recovery**
1. Verify all sidecars share the same stem.
2. For coarse stages, require depth; require normal only when the selected config resolves `requires_normal` true.
3. If sidecars are absent, rerun full preprocessing only after CUDA, CarveKit, Omnidata checkpoints, and dependencies are available.

## Omnidata checkpoints missing

**Symptoms**
- `torch.load('load/omnidata/omnidata_dpt_depth_v2.ckpt')` or the normal checkpoint path fails.
- Depth/normal files are not created.

**Likely causes**
- Omnidata weights were not downloaded into `load/omnidata/`.
- A container or job runs from a mount that lacks model artifacts.

**Recovery**
- Place the depth and normal checkpoints at the exact paths used by preprocessing before running the script.
- If downloads are restricted, ask the user for an approved artifact location instead of trying a network command silently.

## Background removal or captioning dependency failure

**Symptoms**
- `ModuleNotFoundError` for `carvekit`, `transformers`, or related model code.
- CUDA OOM while background removal or BLIP2 captioning starts.

**Likely causes**
- Minimal training environment lacks optional preprocessing/captioning dependencies.
- BLIP2 is too large for the available memory.

**Recovery**
- Separate required preprocessing from optional captioning; omit `--do_caption` unless the user explicitly needs it.
- Use a manually supplied prompt when captioning is blocked.
- If background removal is unavailable but the user already has a transparent PNG, keep that alpha channel and validate sidecars.

## Bad alpha mask or recentering artifacts

**Symptoms**
- The object appears cropped, too small, off-center, or with a broken mask.
- Training loss starts but rendered outputs are dominated by background or floaters.

**Likely causes**
- Foreground mask from background removal is poor.
- `--border_ratio` is too small or large for the object.
- Depth/normal maps were generated from a different crop than the RGBA image.

**Recovery**
1. Regenerate RGBA/depth/normal together from the same source image.
2. Try a less aggressive or more generous `--border_ratio`.
3. Inspect the alpha channel before launching expensive stages.
4. Do not mix sidecars from different preprocessing attempts.
